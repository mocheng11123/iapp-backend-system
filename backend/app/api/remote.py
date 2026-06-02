"""远程管理 API 路由（公告、版本、启动图、广告）"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models import Announcement, AppVersion, SplashConfig, Ad, App, Developer
from app.schemas import (
    AnnouncementCreate,
    AnnouncementResponse,
    AppVersionCreate,
    AppVersionResponse,
    VersionCheckResponse,
    SplashConfigCreate,
    SplashConfigResponse,
    AdCreate,
    AdResponse,
    MessageResponse,
)
from app.services.auth import get_current_developer, api_key_auth
from datetime import datetime
import random

router = APIRouter()


# ============ 公告管理 ============

@router.post("/announcements", response_model=AnnouncementResponse, status_code=status.HTTP_201_CREATED)
async def create_announcement(
    data: AnnouncementCreate,
    developer: Developer = Depends(get_current_developer),
    db: AsyncSession = Depends(get_db),
):
    """发布公告"""
    result = await db.execute(select(App).where(App.id == data.app_id, App.developer_id == developer.id))
    app = result.scalar_one_or_none()
    
    if not app:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="App not found")
    
    announcement = Announcement(
        app_id=app.id,
        title=data.title,
        content=data.content,
        is_sticky=data.is_sticky,
        start_at=data.start_at,
        end_at=data.end_at,
    )
    db.add(announcement)
    await db.commit()
    await db.refresh(announcement)
    
    return AnnouncementResponse.model_validate(announcement)


@router.get("/announcements", response_model=list[AnnouncementResponse])
async def list_announcements(
    app_id: str = None,
    developer: Developer = Depends(get_current_developer),
    db: AsyncSession = Depends(get_db),
):
    """获取公告列表"""
    query = select(Announcement).join(App).where(
        App.developer_id == developer.id,
        App.is_deleted == False
    )
    
    if app_id:
        query = query.where(Announcement.app_id == app_id)
    
    result = await db.execute(query.order_by(Announcement.is_sticky.desc(), Announcement.created_at.desc()))
    announcements = result.scalars().all()
    
    return [AnnouncementResponse.model_validate(a) for a in announcements]


@router.delete("/announcements/{id}", response_model=MessageResponse)
async def delete_announcement(
    id: str,
    developer: Developer = Depends(get_current_developer),
    db: AsyncSession = Depends(get_db),
):
    """删除公告"""
    result = await db.execute(
        select(Announcement)
        .join(App)
        .where(Announcement.id == id, App.developer_id == developer.id)
    )
    announcement = result.scalar_one_or_none()
    
    if not announcement:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Announcement not found")
    
    await db.delete(announcement)
    await db.commit()
    
    return MessageResponse(message="Announcement deleted successfully")


@router.get("/api/v1/announcements", response_model=list[AnnouncementResponse])
async def get_active_announcements(
    app_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """获取当前生效的公告列表（终端 App 调用）"""
    result = await db.execute(
        select(Announcement)
        .where(
            Announcement.app_id == app_id,
            (Announcement.start_at == None) | (Announcement.start_at <= datetime.utcnow()),
            (Announcement.end_at == None) | (Announcement.end_at >= datetime.utcnow())
        )
        .order_by(Announcement.is_sticky.desc(), Announcement.created_at.desc())
    )
    announcements = result.scalars().all()
    
    return [AnnouncementResponse.model_validate(a) for a in announcements]


# ============ 版本管理 ============

@router.post("/versions", response_model=AppVersionResponse, status_code=status.HTTP_201_CREATED)
async def create_version(
    data: AppVersionCreate,
    developer: Developer = Depends(get_current_developer),
    db: AsyncSession = Depends(get_db),
):
    """创建版本记录"""
    result = await db.execute(select(App).where(App.id == data.app_id, App.developer_id == developer.id))
    app = result.scalar_one_or_none()
    
    if not app:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="App not found")
    
    version = AppVersion(
        app_id=app.id,
        version_code=data.version_code,
        version_name=data.version_name,
        update_log=data.update_log,
        download_url=data.download_url,
        file_md5=data.file_md5,
        force_update=data.force_update,
    )
    db.add(version)
    await db.commit()
    await db.refresh(version)
    
    return AppVersionResponse.model_validate(version)


@router.get("/versions", response_model=list[AppVersionResponse])
async def list_versions(
    developer: Developer = Depends(get_current_developer),
    db: AsyncSession = Depends(get_db),
):
    """版本列表"""
    result = await db.execute(
        select(AppVersion)
        .join(App)
        .where(App.developer_id == developer.id, App.is_deleted == False)
        .order_by(AppVersion.version_code.desc())
    )
    versions = result.scalars().all()
    
    return [AppVersionResponse.model_validate(v) for v in versions]


@router.get("/api/v1/version/latest", response_model=VersionCheckResponse)
async def check_latest_version(
    app_id: str = Query(...),
    current_version_code: int = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """获取最新版本信息（终端 App 调用）"""
    result = await db.execute(
        select(AppVersion)
        .where(AppVersion.app_id == app_id)
        .order_by(AppVersion.version_code.desc())
    )
    latest = result.scalar_one_or_none()
    
    if not latest:
        return VersionCheckResponse(need_update=False)
    
    if current_version_code and latest.version_code > current_version_code:
        return VersionCheckResponse(
            need_update=True,
            force_update=latest.force_update,
            version_code=latest.version_code,
            version_name=latest.version_name,
            download_url=latest.download_url,
            update_log=latest.update_log,
        )
    
    return VersionCheckResponse(need_update=False)


# ============ 启动图配置 ============

@router.post("/splash", response_model=SplashConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_splash_config(
    data: SplashConfigCreate,
    developer: Developer = Depends(get_current_developer),
    db: AsyncSession = Depends(get_db),
):
    """配置启动图"""
    result = await db.execute(select(App).where(App.id == data.app_id, App.developer_id == developer.id))
    app = result.scalar_one_or_none()
    
    if not app:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="App not found")
    
    config = SplashConfig(
        app_id=app.id,
        image_url=data.image_url,
        platform=data.platform,
        start_at=data.start_at,
        end_at=data.end_at,
        priority=data.priority,
    )
    db.add(config)
    await db.commit()
    await db.refresh(config)
    
    return SplashConfigResponse.model_validate(config)


@router.get("/splash", response_model=list[SplashConfigResponse])
async def list_splash_configs(
    developer: Developer = Depends(get_current_developer),
    db: AsyncSession = Depends(get_db),
):
    """启动图列表"""
    result = await db.execute(
        select(SplashConfig)
        .join(App)
        .where(App.developer_id == developer.id, App.is_deleted == False)
        .order_by(SplashConfig.priority.desc())
    )
    configs = result.scalars().all()
    
    return [SplashConfigResponse.model_validate(c) for c in configs]


@router.get("/api/v1/splash/current", response_model=SplashConfigResponse)
async def get_current_splash(
    app_id: str = Query(...),
    platform: str = Query("all", pattern="^(android|ios|all)$"),
    db: AsyncSession = Depends(get_db),
):
    """获取当前启动图（终端 App 调用）"""
    now = datetime.utcnow()
    
    result = await db.execute(
        select(SplashConfig)
        .where(
            SplashConfig.app_id == app_id,
            (SplashConfig.platform == "all") | (SplashConfig.platform == platform),
            (SplashConfig.start_at == None) | (SplashConfig.start_at <= now),
            (SplashConfig.end_at == None) | (SplashConfig.end_at >= now)
        )
        .order_by(SplashConfig.priority.desc(), SplashConfig.created_at.desc())
    )
    config = result.scalar_one_or_none()
    
    if not config:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No splash config found")
    
    return SplashConfigResponse.model_validate(config)


# ============ 广告配置 ============

@router.post("/ads", response_model=AdResponse, status_code=status.HTTP_201_CREATED)
async def create_ad(
    data: AdCreate,
    developer: Developer = Depends(get_current_developer),
    db: AsyncSession = Depends(get_db),
):
    """配置广告"""
    result = await db.execute(select(App).where(App.id == data.app_id, App.developer_id == developer.id))
    app = result.scalar_one_or_none()
    
    if not app:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="App not found")
    
    ad = Ad(
        app_id=app.id,
        slot=data.slot,
        type=data.type,
        media_url=data.media_url,
        target_url=data.target_url,
        weight=data.weight,
    )
    db.add(ad)
    await db.commit()
    await db.refresh(ad)
    
    return AdResponse.model_validate(ad)


@router.get("/ads", response_model=list[AdResponse])
async def list_ads(
    developer: Developer = Depends(get_current_developer),
    db: AsyncSession = Depends(get_db),
):
    """广告列表"""
    result = await db.execute(
        select(Ad)
        .join(App)
        .where(App.developer_id == developer.id, App.is_deleted == False)
        .order_by(Ad.weight.desc())
    )
    ads = result.scalars().all()
    
    return [AdResponse.model_validate(a) for a in ads]


@router.get("/api/v1/ads/{slot}", response_model=list[AdResponse])
async def get_ads_by_slot(
    slot: str,
    app_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """获取指定广告位内容（终端 App 调用）"""
    result = await db.execute(
        select(Ad)
        .where(
            Ad.app_id == app_id,
            Ad.slot == slot,
            Ad.status == 1
        )
        .order_by(Ad.weight.desc())
    )
    ads = result.scalars().all()
    
    # 权重随机选择（简化：返回前 10 个）
    return [AdResponse.model_validate(a) for a in ads[:10]]
