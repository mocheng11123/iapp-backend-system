"""计费服务"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from decimal import Decimal
import redis.asyncio as redis
from app.models import ApiCallLog, Developer, Plan, App
from app.core.config import settings
import json


class BillingService:
    """计费服务"""
    
    def __init__(self, db: AsyncSession, r: redis.Redis = None):
        self.db = db
        self.r = r or redis.from_url(settings.REDIS_URL)
    
    async def check_and_deduct_fee(
        self,
        developer: Developer,
        app: App,
        endpoint: str,
        cost: Decimal,
    ) -> bool:
        """
        检查并扣除费用
        返回是否扣费成功
        """
        # 1. 检查请求去重（幂等）
        cache_key = f"api_request:{app.id}:{endpoint}:{datetime.utcnow().strftime('%Y%m%d%H')}"
        # 使用 request_id 去重
        request_id = await self.r.get(f"request_id:{cost}")
        if request_id:
            return True  # 已处理过
        
        # 2. 检查开发者余额
        if developer.balance < cost:
            return False
        
        # 3. 冻结金额
        developer.balance -= cost
        developer.frozen_balance += cost
        
        # 4. 记录 API 调用日志
        log = ApiCallLog(
            app_id=app.id,
            developer_id=developer.id,
            endpoint=endpoint,
            cost=cost,
        )
        self.db.add(log)
        
        return True
    
    async def confirm_fee(self, app_id: str, cost: Decimal):
        """确认费用（冻结转消费）"""
        # 实际项目中需要在开发者表记录消费
        # 这里是简化版本
        pass
    
    async def get_plan_price(self, plan_id: int) -> Plan:
        """获取套餐价格信息"""
        result = await self.db.execute(select(Plan).where(Plan.id == plan_id))
        return result.scalar_one_or_none()
    
    def get_endpoint_price(self, endpoint: str, method: str, plan: Plan) -> Decimal:
        """根据 endpoint 获取单价"""
        # 简化版本：根据 endpoint 类型返回不同价格
        if "/users" in endpoint and method == "POST":
            return plan.create_user_price if plan else Decimal("0.01")
        elif "/auth/login" in endpoint:
            return plan.login_price if plan else Decimal("0.005")
        else:
            return plan.other_operation_price if plan else Decimal("0.005")


async def get_billing_service(
    db: AsyncSession,
) -> BillingService:
    """获取计费服务依赖"""
    r = redis.from_url(settings.REDIS_URL)
    return BillingService(db, r)
