"""开发者相关 API 路由"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.security import get_password_hash, verify_password, create_access_token, create_refresh_token
from app.models import Developer, DeveloperTransaction, App
from app.schemas import (
    DeveloperRegister,
    DeveloperLogin,
    DeveloperResponse,
    DeveloperProfileUpdate,
    DeveloperBalanceResponse,
    DeveloperTransactionResponse,
    Token,
    TokenRefresh,
    MessageResponse,
)
from app.services.auth import get_current_developer
from datetime import datetime, timedelta
from decimal import Decimal

router = APIRouter()


@router.post("/register", response_model=DeveloperResponse, status_code=status.HTTP_201_CREATED)
async def register_developer(
    data: DeveloperRegister,
    db: AsyncSession = Depends(get_db),
):
    """开发者注册"""
    # 检查邮箱是否已存在
    result = await db.execute(select(Developer).where(Developer.email == data.email))
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    
    # 创建开发者
    developer = Developer(
        email=data.email,
        password_hash=get_password_hash(data.password),
        phone=data.phone,
    )
    db.add(developer)
    await db.commit()
    await db.refresh(developer)
    
    return DeveloperResponse.model_validate(developer)


@router.post("/login", response_model=Token)
async def login_developer(
    data: DeveloperLogin,
    db: AsyncSession = Depends(get_db),
):
    """开发者登录"""
    # 查找开发者
    result = await db.execute(select(Developer).where(Developer.email == data.email))
    developer = result.scalar_one_or_none()
    
    if not developer or not verify_password(data.password, developer.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    
    if developer.status != 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled",
        )
    
    # 生成 Token
    access_token = create_access_token(
        data={"sub": str(developer.id), "type": "developer", "email": developer.email}
    )
    refresh_token = create_refresh_token(
        data={"sub": str(developer.id), "type": "developer"}
    )
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.get("/profile", response_model=DeveloperResponse)
async def get_profile(
    developer: Developer = Depends(get_current_developer),
):
    """获取开发者个人信息"""
    return DeveloperResponse.model_validate(developer)


@router.put("/profile", response_model=DeveloperResponse)
async def update_profile(
    data: DeveloperProfileUpdate,
    developer: Developer = Depends(get_current_developer),
    db: AsyncSession = Depends(get_db),
):
    """更新开发者资料"""
    if data.phone is not None:
        developer.phone = data.phone
    
    # 修改密码
    if data.old_password and data.new_password:
        if not verify_password(data.old_password, developer.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid old password",
            )
        developer.password_hash = get_password_hash(data.new_password)
    
    developer.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(developer)
    
    return DeveloperResponse.model_validate(developer)


@router.get("/balance", response_model=DeveloperBalanceResponse)
async def get_balance(
    developer: Developer = Depends(get_current_developer),
):
    """查询开发者余额"""
    return DeveloperBalanceResponse(
        balance=float(developer.balance),
        frozen_balance=float(developer.frozen_balance),
        low_balance_threshold=float(developer.low_balance_threshold),
    )


@router.post("/recharge", response_model=DeveloperBalanceResponse)
async def recharge(
    amount: float,
    developer: Developer = Depends(get_current_developer),
    db: AsyncSession = Depends(get_db),
):
    """开发者充值"""
    if amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Amount must be positive",
        )
    
    # 更新余额
    developer.balance += Decimal(str(amount))
    
    # 记录交易流水
    transaction = DeveloperTransaction(
        developer_id=developer.id,
        amount=Decimal(str(amount)),
        type="recharge",
        reason="Manual recharge",
    )
    db.add(transaction)
    
    await db.commit()
    await db.refresh(developer)
    
    return DeveloperBalanceResponse(
        balance=float(developer.balance),
        frozen_balance=float(developer.frozen_balance),
        low_balance_threshold=float(developer.low_balance_threshold),
    )


@router.get("/transactions", response_model=list[DeveloperTransactionResponse])
async def get_transactions(
    limit: int = 20,
    offset: int = 0,
    developer: Developer = Depends(get_current_developer),
    db: AsyncSession = Depends(get_db),
):
    """查询开发者交易流水"""
    result = await db.execute(
        select(DeveloperTransaction)
        .where(DeveloperTransaction.developer_id == developer.id)
        .order_by(DeveloperTransaction.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    transactions = result.scalars().all()
    
    return [DeveloperTransactionResponse.model_validate(tx) for tx in transactions]


@router.post("/token/refresh", response_model=Token)
async def refresh_token(
    data: TokenRefresh,
    db: AsyncSession = Depends(get_db),
):
    """刷新访问令牌"""
    payload = decode_token(data.refresh_token)
    if not payload or payload.get("type") != "developer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )
    
    developer_id = payload.get("sub")
    result = await db.execute(select(Developer).where(Developer.id == developer_id))
    developer = result.scalar_one_or_none()
    
    if not developer or developer.status != 0:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Developer not found or disabled",
        )
    
    # 生成新的 access token
    access_token = create_access_token(
        data={"sub": str(developer.id), "type": "developer", "email": developer.email}
    )
    refresh_token = create_refresh_token(
        data={"sub": str(developer.id), "type": "developer"}
    )
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }
