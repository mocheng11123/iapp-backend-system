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
