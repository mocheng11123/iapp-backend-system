"""仪表盘统计 API 路由"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.sql import text
from app.core.database import get_db
from app.models import App, EndUser, ApiCallLog, Developer
from app.schemas import (
    DashboardOverviewResponse,
    AppStatsResponse,
    ApiUsageResponse,
    BillingPredictionResponse,
)
from app.services.auth import get_current_developer
from datetime import datetime, timedelta
from decimal import Decimal

router = APIRouter()


@router.get("/overview", response_model=DashboardOverviewResponse)
async def get_overview(
    developer: Developer = Depends(get_current_developer),
    db: AsyncSession = Depends(get_db),
):
    """获取仪表盘总览"""
    # 统计数据
    app_count = await db.execute(
        select(func.count()).select_from(App).where(
            App.developer_id == developer.id,
            App.is_deleted == False
        )
    )
    total_apps = app_count.scalar()
    
    # 终端用户总数
    user_count = await db.execute(
        select(func.count()).select_from(EndUser)
        .join(App)
        .where(App.developer_id == developer.id)
    )
    total_users = user_count.scalar()
    
    # 今日 API 调用量和费用
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_stats = await db.execute(
        select(func.count(), func.sum(ApiCallLog.cost))
        .where(
            ApiCallLog.developer_id == developer.id,
            ApiCallLog.request_time >= today_start
        )
    )
    row = await today_stats.first()
    total_api_calls_today = row[0] or 0
    total_cost_today = float(row[1] or 0)
    
    # API 调用趋势（最近 7 天）
    trend_query = text("""
        SELECT DATE(request_time) as date, COUNT(*) as count
        FROM api_call_logs
        WHERE developer_id = :dev_id
        AND request_time >= :start_date
        GROUP BY DATE(request_time)
        ORDER BY date DESC
        LIMIT 7
    """)
    
    result = await db.execute(
        trend_query,
        {"dev_id": developer.id, "start_date": datetime.utcnow() - timedelta(days=7)}
    )
    trend_rows = result.fetchall()
    
    api_calls_trend = [
        {"date": str(row[0]), "count": row[1]}
        for row in reversed(trend_rows)
    ]
    
    return DashboardOverviewResponse(
        total_apps=total_apps,
        total_users=total_users,
        total_api_calls_today=total_api_calls_today,
        total_cost_today=total_cost_today,
        api_calls_trend=api_calls_trend,
    )


@router.get("/apps/{app_id}/stats", response_model=AppStatsResponse)
async def get_app_stats(
    app_id: str,
    developer: Developer = Depends(get_current_developer),
    db: AsyncSession = Depends(get_db),
):
    """获取单个应用的统计信息"""
    # 获取应用
    result = await db.execute(
        select(App).where(App.id == app_id, App.developer_id == developer.id, App.is_deleted == False)
    )
    app = result.scalar_one_or_none()
    
    if not app:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="App not found",
        )
    
    # 总调用量和费用
    stats = await db.execute(
        select(func.count(), func.sum(ApiCallLog.cost))
        .where(ApiCallLog.app_id == app_id)
    )
    row = await stats.first()
    total_api_calls = row[0] or 0
    total_cost = float(row[1] or 0)
    
    # 活跃用户数（最近 7 天有登录记录）
    active_users = await db.execute(
        select(func.count(EndUser.id))
        .where(
            EndUser.app_id == app_id,
            EndUser.last_login_at >= datetime.utcnow() - timedelta(days=7)
        )
    )
    active_users_count = active_users.scalar()
    
    # 调用趋势
    trend_query = text("""
        SELECT DATE(request_time) as date, COUNT(*) as count
        FROM api_call_logs
        WHERE app_id = :app_id
        AND request_time >= :start_date
        GROUP BY DATE(request_time)
        ORDER BY date DESC
        LIMIT 7
    """)
    
    result = await db.execute(
        trend_query,
        {"app_id": app_id, "start_date": datetime.utcnow() - timedelta(days=7)}
    )
    trend_rows = result.fetchall()
    
    api_calls_trend = [
        {"date": str(row[0]), "count": row[1]}
        for row in reversed(trend_rows)
    ]
    
    return AppStatsResponse(
        app_id=app.id,
        app_name=app.name,
        total_api_calls=total_api_calls,
        total_cost=total_cost,
        active_users=active_users_count,
        api_calls_trend=api_calls_trend,
    )


@router.get("/api-usage", response_model=list[ApiUsageResponse])
async def get_api_usage(
    developer: Developer = Depends(get_current_developer),
    db: AsyncSession = Depends(get_db),
    days: int = 7,
):
    """获取 API 使用明细"""
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # 按 endpoint 统计
    query = text("""
        SELECT 
            endpoint,
            http_method,
            COUNT(*) as count,
            SUM(CASE WHEN response_status >= 200 AND response_status < 300 THEN 1 ELSE 0 END) as success_count,
            SUM(CASE WHEN response_status >= 300 THEN 1 ELSE 0 END) as error_count,
            SUM(cost) as total_cost
        FROM api_call_logs
        WHERE developer_id = :dev_id
        AND request_time >= :start_date
        GROUP BY endpoint, http_method
        ORDER BY count DESC
        LIMIT 100
    """)
    
    result = await db.execute(
        query,
        {"dev_id": developer.id, "start_date": start_date}
    )
    rows = result.fetchall()
    
    return [
        ApiUsageResponse(
            endpoint=row[0],
            method=row[1],
            count=row[2],
            success_count=row[3],
            error_count=row[4],
            total_cost=float(row[5] or 0),
        )
        for row in rows
    ]


@router.get("/billing/prediction", response_model=BillingPredictionResponse)
async def get_billing_prediction(
    developer: Developer = Depends(get_current_developer),
    db: AsyncSession = Depends(get_db),
):
    """获取费用预估"""
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # 今日费用
    today_stats = await db.execute(
        select(func.sum(ApiCallLog.cost))
        .where(
            ApiCallLog.developer_id == developer.id,
            ApiCallLog.request_time >= today_start
        )
    )
    today_cost = float(today_stats.scalar() or 0)
    
    # 本月费用
    month_stats = await db.execute(
        select(func.sum(ApiCallLog.cost))
        .where(
            ApiCallLog.developer_id == developer.id,
            ApiCallLog.request_time >= month_start
        )
    )
    month_cost = float(month_stats.scalar() or 0)
    
    # 估算当月剩余费用
    today_day = datetime.utcnow().day
    days_in_month = (datetime.utcnow().replace(month=datetime.utcnow().month + 1, day=1) - 
                     datetime.utcnow().replace(day=1)).days if datetime.utcnow().month < 12 else 31
    
    if today_day > 0:
        daily_avg = month_cost / today_day
        estimated_month = daily_avg * days_in_month
    else:
        estimated_month = month_cost
    
    # 余额可用天数
    if today_cost > 0:
        days_remaining = int(developer.balance / Decimal(str(today_cost)))
    else:
        days_remaining = None
    
    return BillingPredictionResponse(
        today_estimated=today_cost,
        month_estimated=estimated_month,
        current_balance=float(developer.balance),
        days_remaining=days_remaining,
    )
