"""依赖注入和认证"""
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.security import decode_token
from app.models import Developer, App, EndUser
from app.core.config import settings
import hashlib
import secrets

http_bearer = HTTPBearer(auto_error=False)


# ============ 开发者认证依赖 ============

async def get_current_developer(
    credentials: HTTPAuthorizationCredentials = Depends(http_bearer),
    db: AsyncSession = Depends(get_db),
) -> Developer:
    """获取当前登录的开发者"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    payload = decode_token(credentials.credentials)
    if not payload or payload.get("type") != "developer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    developer_id = payload.get("sub")
    result = await db.execute(
        select(Developer).where(Developer.id == developer_id, Developer.status == 0)
    )
    developer = result.scalar_one_or_none()
    
    if not developer:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Developer not found or disabled",
        )
    
    return developer


# ============ API Key 认证依赖 ============

class APIKeyAuth:
    """API Key 认证"""
    async def __call__(
        self,
        request: Request,
        db: AsyncSession = Depends(get_db),
    ) -> App:
        app_id = request.headers.get("X-App-Id")
        api_key = request.headers.get("X-API-Key")
        
        if not app_id or not api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing X-App-Id or X-API-Key header",
            )
        
        # 查询应用
        result = await db.execute(
            select(App).where(App.id == app_id, App.is_deleted == False)
        )
        app = result.scalar_one_or_none()
        
        if not app:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid App ID",
            )
        
        # 验证 API Key
        api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        if api_key_hash != app.api_key_hash:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API Key",
            )
        
        return app


api_key_auth = APIKeyAuth()


# ============ 终端用户 JWT 认证依赖 ============

async def get_current_enduser(
    credentials: HTTPAuthorizationCredentials = Depends(http_bearer),
    db: AsyncSession = Depends(get_db),
) -> EndUser:
    """获取当前登录的终端用户"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    payload = decode_token(credentials.credentials)
    if not payload or payload.get("role") != "enduser":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("sub")
    result = await db.execute(
        select(EndUser).where(EndUser.id == user_id, EndUser.status == 0)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or disabled",
        )
    
    return user
