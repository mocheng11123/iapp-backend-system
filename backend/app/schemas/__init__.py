"""Pydantic Schema 定义"""
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID


# ============ 开发者相关 Schema ============

class DeveloperRegister(BaseModel):
    """开发者注册请求"""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    phone: Optional[str] = None


class DeveloperLogin(BaseModel):
    """开发者登录请求"""
    email: EmailStr
    password: str


class DeveloperResponse(BaseModel):
    """开发者响应"""
    id: UUID
    email: str
    phone: Optional[str]
    balance: float
    status: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class DeveloperProfileUpdate(BaseModel):
    """开发者资料更新"""
    phone: Optional[str] = None
    old_password: Optional[str] = None
    new_password: Optional[str] = None


class DeveloperBalanceResponse(BaseModel):
    """开发者余额响应"""
    balance: float
    frozen_balance: float
    low_balance_threshold: float


class DeveloperTransactionResponse(BaseModel):
    """开发者交易流水响应"""
    id: UUID
    amount: float
    type: str
    reason: Optional[str]
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ============ Token 相关 Schema ============

class Token(BaseModel):
    """访问令牌响应"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenRefresh(BaseModel):
    """刷新令牌请求"""
    refresh_token: str


# ============ 应用管理相关 Schema ============

class AppCreate(BaseModel):
    """创建应用请求"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    plan_id: Optional[int] = None
    allow_enduser_login: bool = False
    custom_fields_schema: Dict[str, Any] = Field(default_factory=dict)


class AppResponse(BaseModel):
    """应用响应"""
    id: UUID
    name: str
    description: Optional[str]
    api_key_prefix: str
    plan_id: Optional[int]
    allow_enduser_login: bool
    custom_fields_schema: Dict[str, Any]
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class AppDetailResponse(AppResponse):
    """应用详情响应"""
    api_key: str  # 仅在创建时返回完整 API Key


class AppUpdate(BaseModel):
    """应用更新请求"""
    name: Optional[str] = None
    description: Optional[str] = None
    plan_id: Optional[int] = None
    allow_enduser_login: Optional[bool] = None
    custom_fields_schema: Optional[Dict[str, Any]] = None


class ApiKeyRotateResponse(BaseModel):
    """API Key 轮换响应"""
    api_key: str
    api_key_prefix: str


# ============ 终端用户管理相关 Schema ============

class EndUserCreate(BaseModel):
    """创建终端用户请求"""
    username: str = Field(..., min_length=1, max_length=128)
    password: Optional[str] = Field(None, min_length=6, max_length=128)
    custom_data: Dict[str, Any] = Field(default_factory=dict)


class EndUserResponse(BaseModel):
    """终端用户响应"""
    id: UUID
    username: str
    custom_data: Dict[str, Any]
    status: int
    last_login_at: Optional[datetime]
    created_at: datetime
    has_password: bool  # 是否设置了密码
    
    model_config = ConfigDict(from_attributes=True)


class EndUserUpdate(BaseModel):
    """终端用户更新请求"""
    custom_data: Optional[Dict[str, Any]] = None


class EndUserBatchCreate(BaseModel):
    """批量创建终端用户请求"""
    users: List[EndUserCreate] = Field(..., max_length=1000)


class EndUserExportFormat(BaseModel):
    """导出格式选项"""
    format: str = Field("json", pattern="^(json|csv)$")


# ============ 终端用户余额相关 Schema ============

class UserBalanceResponse(BaseModel):
    """用户余额响应"""
    balance: float


class UserBalanceAdd(BaseModel):
    """增加余额请求"""
    amount: float = Field(..., gt=0)
    reason: Optional[str] = None


class UserBalanceSub(BaseModel):
    """扣减余额请求"""
    amount: float = Field(..., gt=0)
    reason: Optional[str] = None


class UserTransactionResponse(BaseModel):
    """用户交易流水响应"""
    id: UUID
    amount: float
    type: str
    reason: Optional[str]
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ============ 终端用户认证相关 Schema ============

class EndUserLogin(BaseModel):
    """终端用户登录请求"""
    username: str
    password: str


class EndUserRegister(BaseModel):
    """终端用户注册请求"""
    username: str = Field(..., min_length=1, max_length=128)
    password: str = Field(..., min_length=6, max_length=128)


class EndUserMeUpdate(BaseModel):
    """当前用户信息更新"""
    custom_data: Optional[Dict[str, Any]] = None


class EndUserPasswordChange(BaseModel):
    """密码修改请求"""
    old_password: str
    new_password: str = Field(..., min_length=6, max_length=128)


# ============ Webhook 相关 Schema ============

class WebhookCreate(BaseModel):
    """创建 Webhook 请求"""
    url: str = Field(..., max_length=500)
    events: List[str] = Field(default_factory=list)
    retry_count: int = Field(3, ge=1, le=10)
    retry_interval: int = Field(60, ge=10, le=3600)


class WebhookResponse(BaseModel):
    """Webhook 响应"""
    id: UUID
    url: str
    events: List[str]
    retry_count: int
    retry_interval: int
    is_active: bool
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class WebhookUpdate(BaseModel):
    """Webhook 更新请求"""
    url: Optional[str] = None
    events: Optional[List[str]] = None
    retry_count: Optional[int] = None
    retry_interval: Optional[int] = None
    is_active: Optional[bool] = None


# ============ 仪表盘统计相关 Schema ============

class DashboardOverviewResponse(BaseModel):
    """仪表盘总览响应"""
    total_apps: int
    total_users: int
    total_api_calls_today: int
    total_cost_today: float
    api_calls_trend: List[Dict[str, Any]]  # 最近 7 天趋势


class AppStatsResponse(BaseModel):
    """应用统计响应"""
    app_id: UUID
    app_name: str
    total_api_calls: int
    total_cost: float
    active_users: int
    api_calls_trend: List[Dict[str, Any]]


class ApiUsageResponse(BaseModel):
    """API 使用明细响应"""
    endpoint: str
    method: str
    count: int
    success_count: int
    error_count: int
    total_cost: float


class BillingPredictionResponse(BaseModel):
    """费用预估响应"""
    today_estimated: float
    month_estimated: float
    current_balance: float
    days_remaining: Optional[int]  # 按当前消耗估算余额可用天数


# ============ 通用响应 ============

class MessageResponse(BaseModel):
    """通用消息响应"""
    message: str


class ErrorResponse(BaseModel):
    """错误响应"""
    detail: str
    error_code: Optional[str] = None


# ============ iApp 特色功能 Schema ============

# --- 卡密系统 ---

class CardBatchCreate(BaseModel):
    """创建卡密批次请求"""
    name: str = Field(..., min_length=1, max_length=100)
    type: int = Field(..., description="1=额度卡密，2=会员卡密")
    amount: Optional[float] = Field(None, gt=0, description="额度卡密面值")
    duration_days: Optional[int] = Field(None, gt=0, description="会员有效天数")
    quantity: int = Field(..., ge=1, le=10000, description="数量")


class CardBatchResponse(BaseModel):
    """卡密批次响应"""
    id: UUID
    app_id: UUID
    name: str
    type: int
    amount: Optional[float]
    duration_days: Optional[int]
    total_quantity: int
    remaining_quantity: int
    price_per_card: float
    total_price: float
    status: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class CardExportResponse(BaseModel):
    """卡密导出响应"""
    batch_id: UUID
    batch_name: str
    cards: List[str]  # 卡密列表
    format: str = "csv"


class CardRedeemRequest(BaseModel):
    """兑换卡密请求"""
    code: str = Field(..., min_length=1, max_length=64)


class CardRedeemResponse(BaseModel):
    """兑换卡密响应"""
    card_type: int
    amount: Optional[float]
    duration_days: Optional[int]
    message: str


class UserMembershipResponse(BaseModel):
    """会员信息响应"""
    level: str
    expire_at: Optional[datetime]
    is_valid: bool
    
    model_config = ConfigDict(from_attributes=True)


# --- 远程管理 ---

class AnnouncementCreate(BaseModel):
    """创建公告请求"""
    title: str = Field(..., min_length=1, max_length=200)
    content: str
    is_sticky: bool = False
    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None


class AnnouncementResponse(BaseModel):
    """公告响应"""
    id: UUID
    app_id: UUID
    title: str
    content: str
    is_sticky: bool
    start_at: Optional[datetime]
    end_at: Optional[datetime]
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class AppVersionCreate(BaseModel):
    """创建版本请求"""
    version_code: int = Field(..., gt=0)
    version_name: str = Field(..., min_length=1, max_length=50)
    update_log: Optional[str] = None
    download_url: str = Field(..., max_length=500)
    file_md5: Optional[str] = None
    force_update: bool = False


class AppVersionResponse(BaseModel):
    """版本响应"""
    id: UUID
    version_code: int
    version_name: str
    update_log: Optional[str]
    download_url: str
    file_md5: Optional[str]
    force_update: bool
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class VersionCheckResponse(BaseModel):
    """版本检查响应"""
    need_update: bool
    force_update: Optional[bool] = False
    version_code: Optional[int] = None
    version_name: Optional[str] = None
    download_url: Optional[str] = None
    update_log: Optional[str] = None


class SplashConfigCreate(BaseModel):
    """启动图配置请求"""
    image_url: str = Field(..., max_length=500)
    platform: str = Field("all", pattern="^(android|ios|all)$")
    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None
    priority: int = Field(0, ge=0)


class SplashConfigResponse(BaseModel):
    """启动图响应"""
    id: UUID
    image_url: str
    platform: str
    start_at: Optional[datetime]
    end_at: Optional[datetime]
    priority: int
    
    model_config = ConfigDict(from_attributes=True)


class AdCreate(BaseModel):
    """广告配置请求"""
    slot: str = Field(..., min_length=1, max_length=50)
    type: str = Field("image", pattern="^(image|video)$")
    media_url: str = Field(..., max_length=500)
    target_url: Optional[str] = Field(None, max_length=500)
    weight: int = Field(0, ge=0)


class AdResponse(BaseModel):
    """广告响应"""
    id: UUID
    slot: str
    type: str
    media_url: str
    target_url: Optional[str]
    weight: int
    status: int
    
    model_config = ConfigDict(from_attributes=True)


# --- 论坛模块 ---

class ForumBoardCreate(BaseModel):
    """创建版块请求"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    sort_order: int = Field(0)


class ForumBoardResponse(BaseModel):
    """版块响应"""
    id: UUID
    name: str
    description: Optional[str]
    sort_order: int
    status: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ForumPostCreate(BaseModel):
    """发布帖子请求"""
    board_id: UUID
    title: str = Field(..., min_length=1, max_length=200)
    content: str


class ForumPostResponse(BaseModel):
    """帖子响应"""
    id: UUID
    board_id: UUID
    board_name: Optional[str] = None
    user_id: UUID
    username: Optional[str] = None
    title: str
    content: str
    view_count: int
    reply_count: int
    is_sticky: bool
    is_essence: bool
    status: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ForumReplyCreate(BaseModel):
    """回复帖子请求"""
    content: str
    reply_to_id: Optional[UUID] = None


class ForumReplyResponse(BaseModel):
    """回复响应"""
    id: UUID
    post_id: UUID
    user_id: UUID
    username: Optional[str] = None
    content: str
    reply_to_id: Optional[UUID]
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# --- 反馈系统 ---

class FeedbackCreate(BaseModel):
    """提交反馈请求"""
    title: str = Field(..., min_length=1, max_length=200)
    content: str
    images: List[str] = Field(default_factory=list)


class FeedbackResponse(BaseModel):
    """反馈响应"""
    id: UUID
    app_id: UUID
    user_id: UUID
    username: Optional[str] = None
    title: str
    content: str
    images: List[str]
    status: int
    reply_content: Optional[str]
    replied_at: Optional[datetime]
    email_sent: bool
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class FeedbackStatusUpdate(BaseModel):
    """更新反馈状态请求"""
    status: int = Field(..., ge=0, le=3)


class FeedbackReply(BaseModel):
    """回复反馈请求"""
    reply_content: str
