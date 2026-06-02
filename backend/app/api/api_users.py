"""终端用户管理 API 路由（供 App 服务端调用）"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.security import get_password_hash
from app.models import App, EndUser, UserBalance, UserTransaction, ApiCallLog
from app.schemas import (
    EndUserCreate,
    EndUserResponse,
    EndUserUpdate,
    EndUserBatchCreate,
    UserBalanceResponse,
    UserBalanceAdd,
    UserBalanceSub,
    UserTransactionResponse,
    MessageResponse,
)
from app.services.auth import api_key_auth
from app.services.billing import BillingService, get_billing_service
from datetime import datetime
from decimal import Decimal
from typing import List
import csv
import io
from fastapi.responses import Response

router = APIRouter()


@router.post("/users", response_model=EndUserResponse, status_code=status.HTTP_201_CREATED)
async def create_enduser(
    data: EndUserCreate,
    app: App = Depends(api_key_auth),
    db: AsyncSession = Depends(get_db),
    billing: BillingService = Depends(get_billing_service),
):
    """创建终端用户"""
    # 检查用户名是否已存在
    result = await db.execute(
        select(EndUser).where(EndUser.app_id == app.id, EndUser.username == data.username)
    )
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists in this app",
        )
    
    # 创建用户
    user = EndUser(
        app_id=app.id,
        username=data.username,
        password_hash=get_password_hash(data.password) if data.password else None,
        custom_data=data.custom_data,
    )
    db.add(user)
    
    # 创建余额记录
    user.balance = UserBalance(user=user, balance=Decimal("0"))
    
    await db.commit()
    await db.refresh(user)
    
    return EndUserResponse(
        id=user.id,
        username=user.username,
        custom_data=user.custom_data,
        status=user.status,
        last_login_at=user.last_login_at,
        created_at=user.created_at,
        has_password=user.password_hash is not None,
    )


@router.get("/users/{user_id}", response_model=EndUserResponse)
async def get_enduser(
    user_id: str,
    app: App = Depends(api_key_auth),
    db: AsyncSession = Depends(get_db),
):
    """查询终端用户信息"""
    result = await db.execute(
        select(EndUser).where(EndUser.id == user_id, EndUser.app_id == app.id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    return EndUserResponse(
        id=user.id,
        username=user.username,
        custom_data=user.custom_data,
        status=user.status,
        last_login_at=user.last_login_at,
        created_at=user.created_at,
        has_password=user.password_hash is not None,
    )


@router.put("/users/{user_id}", response_model=EndUserResponse)
async def update_enduser(
    user_id: str,
    data: EndUserUpdate,
    app: App = Depends(api_key_auth),
    db: AsyncSession = Depends(get_db),
):
    """修改终端用户"""
    result = await db.execute(
        select(EndUser).where(EndUser.id == user_id, EndUser.app_id == app.id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    if data.custom_data is not None:
        user.custom_data = data.custom_data
    
    user.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(user)
    
    return EndUserResponse(
        id=user.id,
        username=user.username,
        custom_data=user.custom_data,
        status=user.status,
        last_login_at=user.last_login_at,
        created_at=user.created_at,
        has_password=user.password_hash is not None,
    )


@router.delete("/users/{user_id}", response_model=MessageResponse)
async def delete_enduser(
    user_id: str,
    app: App = Depends(api_key_auth),
    db: AsyncSession = Depends(get_db),
):
    """删除终端用户"""
    result = await db.execute(
        select(EndUser).where(EndUser.id == user_id, EndUser.app_id == app.id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    await db.delete(user)
    await db.commit()
    
    return MessageResponse(message="User deleted successfully")


@router.post("/users/batch", response_model=List[EndUserResponse], status_code=status.HTTP_201_CREATED)
async def batch_create_users(
    data: EndUserBatchCreate,
    app: App = Depends(api_key_auth),
    db: AsyncSession = Depends(get_db),
):
    """批量创建终端用户"""
    users = []
    for user_data in data.users:
        # 检查用户名是否已存在
        result = await db.execute(
            select(EndUser).where(EndUser.app_id == app.id, EndUser.username == user_data.username)
        )
        if result.scalar_one_or_none():
            continue  # 跳过已存在的用户
        
        user = EndUser(
            app_id=app.id,
            username=user_data.username,
            password_hash=get_password_hash(user_data.password) if user_data.password else None,
            custom_data=user_data.custom_data,
        )
        db.add(user)
        user.balance = UserBalance(user=user, balance=Decimal("0"))
        users.append(user)
    
    await db.commit()
    
    return [
        EndUserResponse(
            id=u.id,
            username=u.username,
            custom_data=u.custom_data,
            status=u.status,
            last_login_at=u.last_login_at,
            created_at=u.created_at,
            has_password=u.password_hash is not None,
        )
        for u in users
    ]


@router.get("/users/export")
async def export_users(
    app: App = Depends(api_key_auth),
    db: AsyncSession = Depends(get_db),
    format: str = Query("json", pattern="^(json|csv)$"),
):
    """导出用户列表"""
    result = await db.execute(
        select(EndUser).where(EndUser.app_id == app.id).order_by(EndUser.created_at.desc())
    )
    users = result.scalars().all()
    
    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "username", "status", "created_at", "custom_data"])
        for user in users:
            writer.writerow([
                user.id,
                user.username,
                user.status,
                user.created_at.isoformat(),
                str(user.custom_data),
            ])
        
        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=users.csv"},
        )
    else:
        # JSON 格式（默认）
        return [
            {
                "id": user.id,
                "username": user.username,
                "status": user.status,
                "created_at": user.created_at.isoformat(),
                "custom_data": user.custom_data,
            }
            for user in users
        ]


@router.post("/users/{user_id}/disable", response_model=MessageResponse)
async def disable_user(
    user_id: str,
    enable: bool = True,
    app: App = Depends(api_key_auth),
    db: AsyncSession = Depends(get_db),
):
    """禁用/启用终端用户"""
    result = await db.execute(
        select(EndUser).where(EndUser.id == user_id, EndUser.app_id == app.id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    user.status = 0 if enable else 1
    user.updated_at = datetime.utcnow()
    await db.commit()
    
    status_text = "enabled" if enable else "disabled"
    return MessageResponse(message=f"User {status_text} successfully")


# ============ 余额相关接口 ============

@router.get("/users/{user_id}/balance", response_model=UserBalanceResponse)
async def get_user_balance(
    user_id: str,
    app: App = Depends(api_key_auth),
    db: AsyncSession = Depends(get_db),
):
    """查询终端用户余额"""
    result = await db.execute(
        select(UserBalance).where(UserBalance.user_id == user_id)
    )
    balance = result.scalar_one_or_none()
    
    if not balance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User balance not found",
        )
    
    return UserBalanceResponse(balance=float(balance.balance))


@router.post("/users/{user_id}/balance/add", response_model=UserBalanceResponse)
async def add_user_balance(
    user_id: str,
    data: UserBalanceAdd,
    app: App = Depends(api_key_auth),
    db: AsyncSession = Depends(get_db),
):
    """增加终端用户余额（充值）"""
    result = await db.execute(
        select(UserBalance).where(UserBalance.user_id == user_id)
    )
    balance = result.scalar_one_or_none()
    
    if not balance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User balance not found",
        )
    
    # 增加余额
    balance.balance += Decimal(str(data.amount))
    
    # 记录用户交易流水
    transaction = UserTransaction(
        user_id=user_id,
        amount=Decimal(str(data.amount)),
        type="recharge",
        reason=data.reason,
    )
    db.add(transaction)
    
    await db.commit()
    
    return UserBalanceResponse(balance=float(balance.balance))


@router.post("/users/{user_id}/balance/sub", response_model=UserBalanceResponse)
async def sub_user_balance(
    user_id: str,
    data: UserBalanceSub,
    app: App = Depends(api_key_auth),
    db: AsyncSession = Depends(get_db),
):
    """扣减终端用户余额"""
    result = await db.execute(
        select(UserBalance).where(UserBalance.user_id == user_id)
    )
    balance = result.scalar_one_or_none()
    
    if not balance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User balance not found",
        )
    
    if balance.balance < Decimal(str(data.amount)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient balance",
        )
    
    # 扣减余额
    balance.balance -= Decimal(str(data.amount))
    
    # 记录交易流水
    transaction = UserTransaction(
        user_id=user_id,
        amount=Decimal(str(data.amount)) * -1,
        type="consume",
        reason=data.reason,
    )
    db.add(transaction)
    
    await db.commit()
    
    return UserBalanceResponse(balance=float(balance.balance))


@router.get("/users/{user_id}/transactions", response_model=list[UserTransactionResponse])
async def get_user_transactions(
    user_id: str,
    limit: int = 20,
    offset: int = 0,
    app: App = Depends(api_key_auth),
    db: AsyncSession = Depends(get_db),
):
    """查询终端用户交易流水"""
    result = await db.execute(
        select(UserTransaction)
        .where(UserTransaction.user_id == user_id)
        .order_by(UserTransaction.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    transactions = result.scalars().all()
    
    return [UserTransactionResponse.model_validate(tx) for tx in transactions]
