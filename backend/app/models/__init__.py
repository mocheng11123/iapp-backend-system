"""数据库模型定义"""
from sqlalchemy import Column, String, Text, Boolean, SmallInteger, DECIMAL, ForeignKey, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP, INET, JSON, BIGSERIAL
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base
import uuid


class Developer(Base):
    """开发者表"""
    __tablename__ = "developers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=True)
    balance = Column(DECIMAL(20, 8), default=0, nullable=False)
    frozen_balance = Column(DECIMAL(20, 8), default=0, nullable=False)
    low_balance_threshold = Column(DECIMAL(10, 2), default=10.0)
    status = Column(SmallInteger, default=0, comment="0=正常，1=冻结，2=删除")
    created_at = Column(TIMESTAMP, default=datetime.utcnow, nullable=False)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    apps = relationship("App", back_populates="developer", cascade="all, delete-orphan")
    transactions = relationship("DeveloperTransaction", back_populates="developer")
    api_keys = relationship("ApiKey", back_populates="developer")
    
    __table_args__ = (
        Index("idx_developers_status", "status"),
    )


class App(Base):
    """应用表"""
    __tablename__ = "apps"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    developer_id = Column(UUID(as_uuid=True), ForeignKey("developers.id"), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    api_key_hash = Column(String(255), nullable=False)
    api_key_prefix = Column(String(10), nullable=False)
    plan_id = Column(BIGSERIAL, nullable=True)
    allow_enduser_login = Column(Boolean, default=False)
    custom_fields_schema = Column(JSON, default=dict)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP, default=datetime.utcnow, nullable=False)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    developer = relationship("Developer", back_populates="apps")
    end_users = relationship("EndUser", back_populates="app", cascade="all, delete-orphan")
    api_call_logs = relationship("ApiCallLog", back_populates="app")
    webhooks = relationship("Webhook", back_populates="app", cascade="all, delete-orphan")
    webhooks_deliveries = relationship("WebhookDelivery", back_populates="app")
    
    __table_args__ = (
        Index("idx_apps_developer_id", "developer_id"),
        Index("idx_apps_is_deleted", "is_deleted"),
    )


class EndUser(Base):
    """终端用户表"""
    __tablename__ = "end_users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    app_id = Column(UUID(as_uuid=True), ForeignKey("apps.id"), nullable=False)
    username = Column(String(128), nullable=False)
    password_hash = Column(String(255), nullable=True)
    custom_data = Column(JSON, default=dict)
    status = Column(SmallInteger, default=0, comment="0=正常，1=禁用")
    last_login_at = Column(TIMESTAMP, nullable=True)
    created_at = Column(TIMESTAMP, default=datetime.utcnow, nullable=False)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    app = relationship("App", back_populates="end_users")
    balance = relationship("UserBalance", back_populates="user", uselist=False, cascade="all, delete-orphan")
    transactions = relationship("UserTransaction", back_populates="user", cascade="all, delete-orphan")
    login_logs = relationship("LoginLog", back_populates="user", cascade="all, delete-orphan")
    
    __table_args__ = (
        UniqueConstraint("app_id", "username", name="uq_app_username"),
        Index("idx_end_users_app_id", "app_id"),
        Index("idx_end_users_status", "status"),
    )


class UserBalance(Base):
    """终端用户余额表"""
    __tablename__ = "user_balances"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("end_users.id"), unique=True, nullable=False)
    balance = Column(DECIMAL(16, 2), default=0, nullable=False)
    version = Column(BIGSERIAL, default=0, comment="乐观锁版本号")
    
    user = relationship("EndUser", back_populates="balance")


class ApiCallLog(Base):
    """API 调用日志表（用于计费）"""
    __tablename__ = "api_call_logs"
    
    id = Column(BIGSERIAL, primary_key=True)
    app_id = Column(UUID(as_uuid=True), ForeignKey("apps.id"), nullable=False)
    developer_id = Column(UUID(as_uuid=True), ForeignKey("developers.id"), nullable=False)
    endpoint = Column(String(255), nullable=False)
    http_method = Column(String(10), nullable=False)
    response_status = Column(SmallInteger, nullable=False)
    cost = Column(DECIMAL(10, 6), default=0)
    request_id = Column(String(64), nullable=True, index=True)
    request_time = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)
    response_time = Column(TIMESTAMP, nullable=True)
    
    app = relationship("App", back_populates="api_call_logs")
    developer = relationship("Developer")
    
    __table_args__ = (
        Index("idx_api_call_logs_app_time", "app_id", "request_time"),
        Index("idx_api_call_logs_developer_time", "developer_id", "request_time"),
        Index("idx_api_call_logs_endpoint", "endpoint"),
    )


class DeveloperTransaction(Base):
    """开发者交易流水表"""
    __tablename__ = "developer_transactions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    developer_id = Column(UUID(as_uuid=True), ForeignKey("developers.id"), nullable=False)
    amount = Column(DECIMAL(20, 8), nullable=False, comment="正数为充值，负数为消费")
    type = Column(String(20), nullable=False, comment="recharge/consume/freeze/unfreeze")
    reason = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, default=datetime.utcnow, nullable=False)
    
    developer = relationship("Developer", back_populates="transactions")
    
    __table_args__ = (
        Index("idx_dev_tx_developer_time", "developer_id", "created_at"),
        Index("idx_dev_tx_type", "type"),
    )


class UserTransaction(Base):
    """终端用户交易流水表"""
    __tablename__ = "user_transactions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("end_users.id"), nullable=False)
    amount = Column(DECIMAL(16, 2), nullable=False, comment="正增负减")
    type = Column(String(20), nullable=False, comment="recharge/consume")
    reason = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, default=datetime.utcnow, nullable=False)
    
    user = relationship("EndUser", back_populates="transactions")
    
    __table_args__ = (
        Index("idx_user_tx_user_time", "user_id", "created_at"),
        Index("idx_user_tx_type", "type"),
    )


class Webhook(Base):
    """Webhook 配置表"""
    __tablename__ = "webhooks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    app_id = Column(UUID(as_uuid=True), ForeignKey("apps.id"), nullable=False)
    url = Column(String(500), nullable=False)
    events = Column(JSON, default=list, comment="订阅的事件列表")
    retry_count = Column(SmallInteger, default=3)
    retry_interval = Column(BIGSERIAL, default=60)
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, default=datetime.utcnow, nullable=False)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    app = relationship("App", back_populates="webhooks")
    deliveries = relationship("WebhookDelivery", back_populates="webhook")


class WebhookDelivery(Base):
    """Webhook 投递记录表"""
    __tablename__ = "webhook_deliveries"
    
    id = Column(BIGSERIAL, primary_key=True)
    webhook_id = Column(UUID(as_uuid=True), ForeignKey("webhooks.id"), nullable=False)
    app_id = Column(UUID(as_uuid=True), ForeignKey("apps.id"), nullable=False)
    event_type = Column(String(50), nullable=False)
    payload = Column(JSON, nullable=False)
    status = Column(SmallInteger, default=0, comment="0=待发送，1=成功，2=失败，3=重试中")
    http_status = Column(SmallInteger, nullable=True)
    retry_count = Column(SmallInteger, default=0)
    next_retry_at = Column(TIMESTAMP, nullable=True)
    created_at = Column(TIMESTAMP, default=datetime.utcnow, nullable=False)
    
    webhook = relationship("Webhook", back_populates="deliveries")
    app = relationship("App", back_populates="webhooks_deliveries")
    
    __table_args__ = (
        Index("idx_webhook_delivery_status", "status"),
        Index("idx_webhook_delivery_retry", "status", "next_retry_at"),
    )


class LoginLog(Base):
    """终端用户登录日志表"""
    __tablename__ = "login_logs"
    
    id = Column(BIGSERIAL, primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("end_users.id"), nullable=False)
    ip = Column(INET, nullable=True)
    user_agent = Column(Text, nullable=True)
    login_at = Column(TIMESTAMP, default=datetime.utcnow, nullable=False)
    
    user = relationship("EndUser", back_populates="login_logs")
    
    __table_args__ = (
        Index("idx_login_logs_user_time", "user_id", "login_at"),
    )


class Plan(Base):
    """计费套餐表"""
    __tablename__ = "plans"
    
    id = Column(BIGSERIAL, primary_key=True)
    name = Column(String(50), nullable=False, comment="套餐名称")
    monthly_fee = Column(DECIMAL(10, 2), default=0)
    free_monthly_calls = Column(BIGSERIAL, default=0)
    create_user_price = Column(DECIMAL(10, 6), default=0.01)
    other_operation_price = Column(DECIMAL(10, 6), default=0.005)
    login_price = Column(DECIMAL(10, 6), default=0.005)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP, default=datetime.utcnow, nullable=False)


# ============ iApp 特色功能模型 ============

class CardBatch(Base):
    """卡密批次表"""
    __tablename__ = "card_batches"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    app_id = Column(UUID(as_uuid=True), ForeignKey("apps.id"), nullable=False)
    name = Column(String(100), nullable=False)
    type = Column(SmallInteger, nullable=False, comment="1=额度卡密，2=会员卡密")
    amount = Column(DECIMAL(16, 2), nullable=True, comment="额度卡密面值")
    duration_days = Column(BIGSERIAL, nullable=True, comment="会员有效天数")
    total_quantity = Column(BIGSERIAL, nullable=False)
    remaining_quantity = Column(BIGSERIAL, nullable=False)
    price_per_card = Column(DECIMAL(10, 4), nullable=False, comment="开发者购买单价")
    total_price = Column(DECIMAL(16, 2), nullable=False, comment="总价格")
    status = Column(SmallInteger, default=0, comment="0=正常，1=已吊销")
    created_at = Column(TIMESTAMP, default=datetime.utcnow, nullable=False)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    app = relationship("App", back_populates="card_batches")
    cards = relationship("Card", back_populates="batch", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_card_batches_app_id", "app_id"),
        Index("idx_card_batches_status", "status"),
    )


class Card(Base):
    """卡密表"""
    __tablename__ = "cards"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    batch_id = Column(UUID(as_uuid=True), ForeignKey("card_batches.id"), nullable=False)
    code = Column(String(64), unique=True, nullable=False, comment="卡密码")
    status = Column(SmallInteger, default=0, comment="0=未使用，1=已使用，2=已吊销")
    used_by_user_id = Column(UUID(as_uuid=True), ForeignKey("end_users.id"), nullable=True)
    used_at = Column(TIMESTAMP, nullable=True)
    created_at = Column(TIMESTAMP, default=datetime.utcnow, nullable=False)
    
    batch = relationship("CardBatch", back_populates="cards")
    used_by_user = relationship("EndUser")
    
    __table_args__ = (
        Index("idx_cards_batch_id", "batch_id"),
        Index("idx_cards_code", "code"),
        Index("idx_cards_status", "status"),
    )


class UserMembership(Base):
    """终端会员表"""
    __tablename__ = "user_memberships"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("end_users.id"), unique=True, nullable=False)
    level = Column(String(50), default="vip", comment="会员等级")
    expire_at = Column(TIMESTAMP, nullable=True, comment="到期时间，NULL 表示永久")
    created_at = Column(TIMESTAMP, default=datetime.utcnow, nullable=False)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("EndUser", back_populates="membership")


class Announcement(Base):
    """公告表"""
    __tablename__ = "announcements"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    app_id = Column(UUID(as_uuid=True), ForeignKey("apps.id"), nullable=False)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    is_sticky = Column(Boolean, default=False, comment="置顶")
    start_at = Column(TIMESTAMP, nullable=True)
    end_at = Column(TIMESTAMP, nullable=True)
    created_at = Column(TIMESTAMP, default=datetime.utcnow, nullable=False)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    app = relationship("App", back_populates="announcements")
    
    __table_args__ = (
        Index("idx_announcements_app_time", "app_id", "start_at", "end_at"),
    )


class AppVersion(Base):
    """版本表"""
    __tablename__ = "app_versions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    app_id = Column(UUID(as_uuid=True), ForeignKey("apps.id"), nullable=False)
    version_code = Column(BIGSERIAL, nullable=False, comment="内部版本号")
    version_name = Column(String(50), nullable=False, comment="展示版本号")
    update_log = Column(Text, nullable=True)
    download_url = Column(String(500), nullable=False)
    file_md5 = Column(String(32), nullable=True)
    force_update = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP, default=datetime.utcnow, nullable=False)
    
    app = relationship("App", back_populates="versions")
    
    __table_args__ = (
        Index("idx_app_versions_app_code", "app_id", "version_code"),
    )


class SplashConfig(Base):
    """启动图表"""
    __tablename__ = "splash_configs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    app_id = Column(UUID(as_uuid=True), ForeignKey("apps.id"), nullable=False)
    image_url = Column(String(500), nullable=False)
    platform = Column(String(10), default="all", comment="android/ios/all")
    start_at = Column(TIMESTAMP, nullable=True)
    end_at = Column(TIMESTAMP, nullable=True)
    priority = Column(BIGSERIAL, default=0, comment="越大越优先")
    created_at = Column(TIMESTAMP, default=datetime.utcnow, nullable=False)
    
    app = relationship("App", back_populates="splash_configs")
    
    __table_args__ = (
        Index("idx_splash_app_time", "app_id", "start_at", "end_at"),
    )


class Ad(Base):
    """广告表"""
    __tablename__ = "ads"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    app_id = Column(UUID(as_uuid=True), ForeignKey("apps.id"), nullable=False)
    slot = Column(String(50), nullable=False, comment="广告位标识")
    type = Column(String(20), default="image", comment="image/video")
    media_url = Column(String(500), nullable=False)
    target_url = Column(String(500), nullable=True)
    weight = Column(BIGSERIAL, default=0, comment="权重")
    status = Column(SmallInteger, default=1, comment="0=禁用，1=启用")
    created_at = Column(TIMESTAMP, default=datetime.utcnow, nullable=False)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    app = relationship("App", back_populates="ads")
    
    __table_args__ = (
        Index("idx_ads_app_slot", "app_id", "slot"),
    )


class ForumBoard(Base):
    """论坛版块表"""
    __tablename__ = "forum_boards"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    app_id = Column(UUID(as_uuid=True), ForeignKey("apps.id"), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    sort_order = Column(BIGSERIAL, default=0)
    status = Column(SmallInteger, default=1, comment="0=关闭，1=开放")
    created_at = Column(TIMESTAMP, default=datetime.utcnow, nullable=False)
    
    app = relationship("App", back_populates="forum_boards")
    posts = relationship("ForumPost", back_populates="board", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_forum_boards_app_id", "app_id"),
    )


class ForumPost(Base):
    """论坛帖子表"""
    __tablename__ = "forum_posts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    board_id = Column(UUID(as_uuid=True), ForeignKey("forum_boards.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("end_users.id"), nullable=False)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    view_count = Column(BIGSERIAL, default=0)
    reply_count = Column(BIGSERIAL, default=0)
    is_sticky = Column(Boolean, default=False)
    is_essence = Column(Boolean, default=False)
    status = Column(SmallInteger, default=0, comment="0=正常，1=已删除")
    created_at = Column(TIMESTAMP, default=datetime.utcnow, nullable=False)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    board = relationship("ForumBoard", back_populates="posts")
    user = relationship("EndUser", back_populates="forum_posts")
    replies = relationship("ForumReply", back_populates="post", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_forum_posts_board", "board_id"),
        Index("idx_forum_posts_user", "user_id"),
        Index("idx_forum_posts_status", "status"),
    )


class ForumReply(Base):
    """论坛回复表"""
    __tablename__ = "forum_replies"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    post_id = Column(UUID(as_uuid=True), ForeignKey("forum_posts.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("end_users.id"), nullable=False)
    content = Column(Text, nullable=False)
    reply_to_id = Column(UUID(as_uuid=True), nullable=True, comment="引用回复的 ID")
    status = Column(SmallInteger, default=0)
    created_at = Column(TIMESTAMP, default=datetime.utcnow, nullable=False)
    
    post = relationship("ForumPost", back_populates="replies")
    user = relationship("EndUser", back_populates="forum_replies")
    
    __table_args__ = (
        Index("idx_forum_replies_post", "post_id"),
    )


class Feedback(Base):
    """反馈表"""
    __tablename__ = "feedbacks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    app_id = Column(UUID(as_uuid=True), ForeignKey("apps.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("end_users.id"), nullable=False)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    images = Column(JSON, default=list, comment="图片 URL 列表")
    status = Column(SmallInteger, default=0, comment="0=待处理，1=已读，2=已解决，3=已忽略")
    reply_content = Column(Text, nullable=True)
    replied_at = Column(TIMESTAMP, nullable=True)
    email_sent = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP, default=datetime.utcnow, nullable=False)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    app = relationship("App", back_populates="feedbacks")
    user = relationship("EndUser", back_populates="feedbacks")
    
    __table_args__ = (
        Index("idx_feedbacks_app_status", "app_id", "status"),
        Index("idx_feedbacks_user", "user_id"),
    )


class EmailLog(Base):
    """邮件发送记录表"""
    __tablename__ = "email_logs"
    
    id = Column(BIGSERIAL, primary_key=True)
    to_email = Column(String(255), nullable=False)
    subject = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    status = Column(SmallInteger, default=0, comment="0=待发送，1=成功，2=失败")
    retry_count = Column(BIGSERIAL, default=0)
    error_message = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, default=datetime.utcnow, nullable=False)
    sent_at = Column(TIMESTAMP, nullable=True)


# 添加新的关联关系到已有模型
EndUser.membership = relationship("UserMembership", back_populates="user", uselist=False, cascade="all, delete-orphan")
EndUser.forum_posts = relationship("ForumPost", back_populates="user", cascade="all, delete-orphan")
EndUser.forum_replies = relationship("ForumReply", back_populates="user", cascade="all, delete-orphan")
EndUser.feedbacks = relationship("Feedback", back_populates="user", cascade="all, delete-orphan")
EndUser.card_usages = relationship("Card", back_populates="used_by_user")

App.card_batches = relationship("CardBatch", back_populates="app", cascade="all, delete-orphan")
App.announcements = relationship("Announcement", back_populates="app", cascade="all, delete-orphan")
App.versions = relationship("AppVersion", back_populates="app", cascade="all, delete-orphan")
App.splash_configs = relationship("SplashConfig", back_populates="app", cascade="all, delete-orphan")
App.ads = relationship("Ad", back_populates="app", cascade="all, delete-orphan")
App.forum_boards = relationship("ForumBoard", back_populates="app", cascade="all, delete-orphan")
App.feedbacks = relationship("Feedback", back_populates="app", cascade="all, delete-orphan")
