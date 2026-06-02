"""WebHook 管理 API 路由"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models import Webhook, App
from app.schemas import (
    WebhookCreate,
    WebhookResponse,
    WebhookUpdate,
    MessageResponse,
)
from app.services.auth import get_current_developer
from datetime import datetime

router = APIRouter()


@router.post("", response_model=WebhookResponse, status_code=status.HTTP_201_CREATED)
async def create_webhook(
    data: WebhookCreate,
    developer: Developer = Depends(get_current_developer),
    db: AsyncSession = Depends(get_db),
):
    """创建 Webhook"""
    # 查找应用
    result = await db.execute(
        select(App).where(App.id == data.app_id, App.developer_id == developer.id)
    )
    app = result.scalar_one_or_none()
    
    if not app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="App not found",
        )
    
    # 创建 Webhook
    webhook = Webhook(
        app_id=app.id,
        url=data.url,
        events=data.events,
        retry_count=data.retry_count,
        retry_interval=data.retry_interval,
    )
    db.add(webhook)
    await db.commit()
    await db.refresh(webhook)
    
    return WebhookResponse.model_validate(webhook)


@router.get("", response_model=list[WebhookResponse])
async def list_webhooks(
    app_id: str = None,
    developer: Developer = Depends(get_current_developer),
    db: AsyncSession = Depends(get_db),
):
    """获取 Webhook 列表"""
    query = select(Webhook).join(App).where(
        App.developer_id == developer.id,
        App.is_deleted == False
    )
    
    if app_id:
        query = query.where(Webhook.app_id == app_id)
    
    result = await db.execute(query.order_by(Webhook.created_at.desc()))
    webhooks = result.scalars().all()
    
    return [WebhookResponse.model_validate(wh) for wh in webhooks]


@router.put("/{webhook_id}", response_model=WebhookResponse)
async def update_webhook(
    webhook_id: str,
    data: WebhookUpdate,
    developer: Developer = Depends(get_current_developer),
    db: AsyncSession = Depends(get_db),
):
    """更新 Webhook"""
    result = await db.execute(
        select(Webhook)
        .join(App)
        .where(Webhook.id == webhook_id, App.developer_id == developer.id, App.is_deleted == False)
    )
    webhook = result.scalar_one_or_none()
    
    if not webhook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook not found",
        )
    
    if data.url is not None:
        webhook.url = data.url
    if data.events is not None:
        webhook.events = data.events
    if data.retry_count is not None:
        webhook.retry_count = data.retry_count
    if data.retry_interval is not None:
        webhook.retry_interval = data.retry_interval
    if data.is_active is not None:
        webhook.is_active = data.is_active
    
    webhook.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(webhook)
    
    return WebhookResponse.model_validate(webhook)


@router.delete("/{webhook_id}", response_model=MessageResponse)
async def delete_webhook(
    webhook_id: str,
    developer: Developer = Depends(get_current_developer),
    db: AsyncSession = Depends(get_db),
):
    """删除 Webhook"""
    result = await db.execute(
        select(Webhook)
        .join(App)
        .where(Webhook.id == webhook_id, App.developer_id == developer.id, App.is_deleted == False)
    )
    webhook = result.scalar_one_or_none()
    
    if not webhook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook not found",
        )
    
    await db.delete(webhook)
    await db.commit()
    
    return MessageResponse(message="Webhook deleted successfully")
