from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """应用配置"""
    
    # 应用基础配置
    APP_NAME: str = "App 后台管理系统"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # 数据库配置
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/app_backend"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    
    # Redis 配置
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Celery 配置
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"
    
    # JWT 配置
    JWT_SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 120
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # API Key 配置
    API_KEY_PREFIX: str = "sk_live_"
    API_KEY_LENGTH: int = 32
    
    # 安全配置
    BCRYPT_ROUNDS: int = 12
    LOGIN_MAX_ATTEMPTS: int = 5
    LOGIN_LOCKOUT_MINUTES: int = 15
    
    # 计费配置
    DEFAULT_LOW_BALANCE_THRESHOLD: float = 10.0
    
    # Webhook 配置
    WEBHOOK_MAX_RETRIES: int = 3
    WEBHOOK_RETRY_INTERVAL: int = 60
    
    # CORS 配置
    CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:8080"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
