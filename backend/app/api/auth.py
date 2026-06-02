"""终端用户认证 API 路由（供 App 客户端调用）"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.security import get_password_hash, verify_password, create_access_token, create_refresh_token
from app.models import App, EndUser, LoginLog
from app.schemas import (
    EndUserLogin,
    EndUserRegister,
    EndUserMeUpdate,
    EndUserPasswordChange,
    Token,
    MessageResponse,
)
from app.services.auth import get_current_enduser, api_key_auth
from datetime import datetime

router = APIRouter()


@router.post("/register", response_model=Token)
async def enduser_register(
    data: EndUserRegister,
    app: App = Depends(api_key_auth),
    db: AsyncSession = Depends(get_db),
):
    """终端用户自助注册"""
    # 检查是否允许自助注册
    if not app.allow_enduser_login:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="End user registration is not allowed for this app",
        )
    
    # 检查用户名是否已存在
    result = await db.execute(
        select(EndUser).where(EndUser.app_id == app.id, EndUser.username == data.username)
    )
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists",
        )
    
    # 创建用户
    user = EndUser(
        app_id=app.id,
        username=data.username,
        password_hash=get_password_hash(data.password),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    # 生成 Token
    access_token = create_access_token(
        data={"sub": str(user.id), "app_id": str(app.id), "role": "enduser", "username": user.username}
    )
    refresh_token = create_refresh_token(
        data={"sub": str(user.id), "app_id": str(app.id), "role": "enduser"}
    )
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/login", response_model=Token)
async def enduser_login(
    data: EndUserLogin,
    app: App = Depends(api_key_auth),
    db: AsyncSession = Depends(get_db),
    request: Request = None,
):
    """终端用户登录"""
    # 检查是否允许登录
    if not app.allow_enduser_login:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="End user login is not allowed for this app",
        )
    
    # 查找用户
    result = await db.execute(
        select(EndUser).where(EndUser.app_id == app.id, EndUser.username == data.username)
    )
    user = result.scalar_one_or_none()
    
    if not user or not user.password_hash or not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )
    
    if user.status != 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled",
        )
    
    # 更新最后登录时间
    user.last_login_at = datetime.utcnow()
    
    # 记录登录日志
    login_log = LoginLog(
        user_id=user.id,
        ip=request.client.host if request and request.client else None,
        user_agent=request.headers.get("user-agent") if request else None,
    )
    db.add(login_log)
    
    await db.commit()
    
    # 生成 Token
    access_token = create_access_token(
        data={"sub": str(user.id), "app_id": str(app.id), "role": "enduser", "username": user.username}
    )
    refresh_token = create_refresh_token(
        data={"sub": str(user.id), "app_id": str(app.id), "role": "enduser"}
    )
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_token_str: str,
    app: App = Depends(api_key_auth),
    db: AsyncSession = Depends(get_db),
):
    """刷新访问令牌"""
    from app.core.security import decode_token
    
    payload = decode_token(refresh_token_str)
    if not payload or payload.get("role") != "enduser":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )
    
    user_id = payload.get("sub")
    result = await db.execute(select(EndUser).where(EndUser.id == user_id, EndUser.app_id == app.id))
    user = result.scalar_one_or_none()
    
    if not user or user.status != 0:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or disabled",
        )
    
    # 生成新的 access token
    access_token = create_access_token(
        data={"sub": str(user.id), "app_id": str(app.id), "role": "enduser", "username": user.username}
    )
    new_refresh_token = create_refresh_token(
        data={"sub": str(user.id), "app_id": str(app.id), "role": "enduser"}
    )
    
    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
    }


@router.post("/logout", response_model=MessageResponse)
async def enduser_logout(
    user: EndUser = Depends(get_current_enduser),
):
    """终端用户登出"""
    # 实际项目中可能需要在黑名单中记录 token
    return MessageResponse(message="Logged out successfully")


@router.get("/me", response_model=dict)
async def get_current_user_info(
    user: EndUser = Depends(get_current_enduser),
):
    """获取当前登录用户信息"""
    return {
        "id": user.id,
        "username": user.username,
        "custom_data": user.custom_data,
        "last_login_at": user.last_login_at,
        "created_at": user.created_at,
    }


@router.put("/me", response_model=dict)
async def update_current_user(
    data: EndUserMeUpdate,
    user: EndUser = Depends(get_current_enduser),
    db: AsyncSession = Depends(get_db),
):
    """修改当前用户信息"""
    if data.custom_data is not None:
        user.custom_data = data.custom_data
    
    user.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(user)
    
    return {
        "id": user.id,
        "username": user.username,
        "custom_data": user.custom_data,
        "last_login_at": user.last_login_at,
        "created_at": user.created_at,
    }


@router.post("/me/password", response_model=MessageResponse)
async def change_password(
    data: EndUserPasswordChange,
    user: EndUser = Depends(get_current_enduser),
    db: AsyncSession = Depends(get_db),
):
    """修改密码"""
    if not user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change password for users without password",
        )
    
    if not verify_password(data.old_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid old password",
        )
    
    user.password_hash = get_password_hash(data.new_password)
    user.updated_at = datetime.utcnow()
    await db.commit()
    
    return MessageResponse(message="Password changed successfully")
