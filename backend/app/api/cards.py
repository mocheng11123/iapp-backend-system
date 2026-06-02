"""卡密系统 API 路由"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models import CardBatch, Card, App, Developer, EndUser, UserBalance, UserMembership, UserTransaction
from app.schemas import (
    CardBatchCreate,
    CardBatchResponse,
    CardExportResponse,
    CardRedeemRequest,
    CardRedeemResponse,
    UserMembershipResponse,
    MessageResponse,
)
from app.services.auth import get_current_developer, api_key_auth, get_current_enduser
from datetime import datetime, timedelta
from decimal import Decimal
import secrets
import csv
import io
from fastapi.responses import Response

router = APIRouter()


def generate_card_code() -> str:
    """生成随机卡密码"""
    return secrets.token_urlsafe(24)[:32]


@router.post("/card/batches", response_model=CardBatchResponse, status_code=status.HTTP_201_CREATED)
async def create_card_batch(
    data: CardBatchCreate,
    developer: Developer = Depends(get_current_developer),
    db: AsyncSession = Depends(get_db),
):
    """创建卡密批次"""
    # 查找应用
    result = await db.execute(select(App).where(App.id == data.app_id, App.developer_id == developer.id))
    app = result.scalar_one_or_none()
    
    if not app:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="App not found")
    
    # 验证参数
    if data.type == 1 and not data.amount:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="额度卡密必须指定面值")
    if data.type == 2 and not data.duration_days:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="会员卡密必须指定有效期")
    
    # 计算价格（简化：固定 7 折）
    if data.type == 1:
        price_per_card = Decimal(str(data.amount)) * Decimal("0.7")
        total_price = price_per_card * data.quantity
    else:
        # 会员卡密按天数计价，每天 0.1 元
        price_per_card = Decimal(str(data.duration_days)) * Decimal("0.1")
        total_price = price_per_card * data.quantity
    
    # 检查开发者余额
    if developer.balance < total_price:
        raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail="Insufficient developer balance")
    
    # 扣费
    developer.balance -= total_price
    developer.updated_at = datetime.utcnow()
    
    # 创建批次
    batch = CardBatch(
        app_id=app.id,
        name=data.name,
        type=data.type,
        amount=Decimal(str(data.amount)) if data.amount else None,
        duration_days=data.duration_days,
        total_quantity=data.quantity,
        remaining_quantity=data.quantity,
        price_per_card=price_per_card,
        total_price=total_price,
    )
    db.add(batch)
    await db.flush()
    
    # 批量生成卡密
    cards = []
    for _ in range(data.quantity):
        card = Card(
            batch_id=batch.id,
            code=generate_card_code(),
        )
        cards.append(card)
    
    db.add_all(cards)
    await db.commit()
    
    return CardBatchResponse.model_validate(batch)


@router.get("/card/batches", response_model=list[CardBatchResponse])
async def list_card_batches(
    app_id: str = None,
    developer: Developer = Depends(get_current_developer),
    db: AsyncSession = Depends(get_db),
):
    """获取卡密批次列表"""
    query = select(CardBatch).join(App).where(
        App.developer_id == developer.id,
        App.is_deleted == False
    )
    
    if app_id:
        query = query.where(CardBatch.app_id == app_id)
    
    result = await db.execute(query.order_by(CardBatch.created_at.desc()))
    batches = result.scalars().all()
    
    return [CardBatchResponse.model_validate(batch) for batch in batches]


@router.get("/card/batches/{batch_id}/cards")
async def export_cards(
    batch_id: str,
    developer: Developer = Depends(get_current_developer),
    db: AsyncSession = Depends(get_db),
):
    """导出卡密批次"""
    result = await db.execute(
        select(CardBatch)
        .join(App)
        .where(CardBatch.id == batch_id, App.developer_id == developer.id)
    )
    batch = result.scalar_one_or_none()
    
    if not batch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch not found")
    
    result = await db.execute(select(Card).where(Card.batch_id == batch_id).order_by(Card.created_at))
    cards = result.scalars().all()
    
    # 返回 CSV
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["卡密代码"])
    for card in cards:
        writer.writerow([card.code])
    
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={batch.name}.csv"},
    )


@router.post("/card/batches/{batch_id}/revoke", response_model=MessageResponse)
async def revoke_batch(
    batch_id: str,
    developer: Developer = Depends(get_current_developer),
    db: AsyncSession = Depends(get_db),
):
    """吊销卡密批次"""
    result = await db.execute(
        select(CardBatch)
        .join(App)
        .where(CardBatch.id == batch_id, App.developer_id == developer.id)
    )
    batch = result.scalar_one_or_none()
    
    if not batch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch not found")
    
    batch.status = 1  # 已吊销
    await db.commit()
    
    return MessageResponse(message="Batch revoked successfully")


@router.post("/card/redeem", response_model=CardRedeemResponse)
async def redeem_card(
    data: CardRedeemRequest,
    user: EndUser = Depends(get_current_enduser),
    db: AsyncSession = Depends(get_db),
):
    """兑换卡密"""
    # 查找卡密
    result = await db.execute(select(Card).where(Card.code == data.code))
    card = result.scalar_one_or_none()
    
    if not card:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid card code")
    
    if card.status != 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Card already used or revoked")
    
    # 验证归属应用
    batch = card.batch
    if batch.app_id != user.app_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Card does not belong to this app")
    
    # 根据类型处理
    if batch.type == 1:  # 额度卡密
        user_balance = user.balance
        if not user_balance:
            user_balance = UserBalance(user_id=user.id, balance=Decimal("0"))
            db.add(user_balance)
        
        user_balance.balance += batch.amount
        
        # 记录流水
        tx = UserTransaction(
            user_id=user.id,
            amount=batch.amount,
            type="recharge",
            reason=f"Card redemption: {card.code[:10]}...",
        )
        db.add(tx)
        
    else:  # 会员卡密
        membership = user.membership
        if not membership:
            membership = UserMembership(user_id=user.id, level="vip")
            db.add(membership)
        
        if membership.expire_at and membership.expire_at > datetime.utcnow():
            membership.expire_at += timedelta(days=batch.duration_days)
        else:
            membership.expire_at = datetime.utcnow() + timedelta(days=batch.duration_days)
    
    # 更新卡密状态
    card.status = 1
    card.used_by_user_id = user.id
    card.used_at = datetime.utcnow()
    
    # 批次剩余数量
    batch.remaining_quantity -= 1
    
    await db.commit()
    
    return CardRedeemResponse(
        card_type=batch.type,
        amount=float(batch.amount) if batch.amount else None,
        duration_days=batch.duration_days,
        message="Card redeemed successfully",
    )


@router.get("/users/me/membership", response_model=UserMembershipResponse)
async def get_my_membership(
    user: EndUser = Depends(get_current_enduser),
    db: AsyncSession = Depends(get_db),
):
    """查询当前用户会员信息"""
    membership = user.membership
    
    if not membership:
        return UserMembershipResponse(
            level="free",
            expire_at=None,
            is_valid=False,
        )
    
    is_valid = not membership.expire_at or membership.expire_at > datetime.utcnow()
    
    return UserMembershipResponse(
        level=membership.level,
        expire_at=membership.expire_at,
        is_valid=is_valid,
    )
