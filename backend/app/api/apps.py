"""应用管理 API 路由"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models import App, Developer
from app.schemas import (
    AppCreate,
    AppResponse,
    AppDetailResponse,
    AppUpdate,
    ApiKeyRotateResponse,
    MessageResponse,
)
from app.services.auth import get_current_developer
from datetime import datetime
import hashlib
import secrets

router = APIRouter()


@router.post("", response_model=AppDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_app(
    data: AppCreate,
    developer: Developer = Depends(get_current_developer),
    db: AsyncSession = Depends(get_db),
):
    """创建应用"""
    # 生成 API Key
    api_key = f"sk_live_{secrets.token_urlsafe(32)}"
    api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    api_key_prefix = api_key[:10]
    
    # 创建应用
    app = App(
        developer_id=developer.id,
        name=data.name,
        description=data.description,
        api_key_hash=api_key_hash,
        api_key_prefix=api_key_prefix,
        plan_id=data.plan_id,
        allow_enduser_login=data.allow_enduser_login,
        custom_fields_schema=data.custom_fields_schema,
    )
    db.add(app)
    await db.commit()
    await db.refresh(app)
    
    # 返回完整 API Key（仅一次）
    response = AppDetailResponse.model_validate(app)
    response.api_key = api_key
    return response


@router.get("", response_model=list[AppResponse])
async def list_apps(
    developer: Developer = Depends(get_current_developer),
    db: AsyncSession = Depends(get_db),
):
    """获取应用列表"""
    result = await db.execute(
        select(App)
        .where(App.developer_id == developer.id, App.is_deleted == False)
        .order_by(App.created_at.desc())
    )
    apps = result.scalars().all()
    
    return [AppResponse.model_validate(app) for app in apps]


@router.get("/{app_id}", response_model=AppResponse)
async def get_app(
    app_id: str,
    developer: Developer = Depends(get_current_developer),
    db: AsyncSession = Depends(get_db),
):
    """获取应用详情"""
    result = await db.execute(
        select(App).where(App.id == app_id, App.developer_id == developer.id, App.is_deleted == False)
    )
    app = result.scalar_one_or_none()
    
    if not app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="App not found",
        )
    
    return AppResponse.model_validate(app)


@router.put("/{app_id}", response_model=AppResponse)
async def update_app(
    app_id: str,
    data: AppUpdate,
    developer: Developer = Depends(get_current_developer),
    db: AsyncSession = Depends(get_db),
):
    """更新应用配置"""
    result = await db.execute(
        select(App).where(App.id == app_id, App.developer_id == developer.id, App.is_deleted == False)
    )
    app = result.scalar_one_or_none()
    
    if not app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="App not found",
        )
    
    # 更新字段
    if data.name is not None:
        app.name = data.name
    if data.description is not None:
        app.description = data.description
    if data.plan_id is not None:
        app.plan_id = data.plan_id
    if data.allow_enduser_login is not None:
        app.allow_enduser_login = data.allow_enduser_login
    if data.custom_fields_schema is not None:
        app.custom_fields_schema = data.custom_fields_schema
    
    app.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(app)
    
    return AppResponse.model_validate(app)


@router.delete("/{app_id}", response_model=MessageResponse)
async def delete_app(
    app_id: str,
    developer: Developer = Depends(get_current_developer),
    db: AsyncSession = Depends(get_db),
):
    """删除应用（软删除）"""
    result = await db.execute(
        select(App).where(App.id == app_id, App.developer_id == developer.id, App.is_deleted == False)
    )
    app = result.scalar_one_or_none()
    
    if not app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="App not found",
        )
    
    app.is_deleted = True
    app.updated_at = datetime.utcnow()
    await db.commit()
    
    return MessageResponse(message="App deleted successfully")


@router.post("/{app_id}/rotate-key", response_model=ApiKeyRotateResponse)
async def rotate_api_key(
    app_id: str,
    developer: Developer = Depends(get_current_developer),
    db: AsyncSession = Depends(get_db),
):
    """轮换 API Key"""
    result = await db.execute(
        select(App).where(App.id == app_id, App.developer_id == developer.id, App.is_deleted == False)
    )
    app = result.scalar_one_or_none()
    
    if not app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="App not found",
        )
    
    # 生成新的 API Key
    api_key = f"sk_live_{secrets.token_urlsafe(32)}"
    api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    api_key_prefix = api_key[:10]
    
    app.api_key_hash = api_key_hash
    app.api_key_prefix = api_key_prefix
    app.updated_at = datetime.utcnow()
    await db.commit()
    
    return ApiKeyRotateResponse(
        api_key=api_key,
        api_key_prefix=api_key_prefix,
    )
