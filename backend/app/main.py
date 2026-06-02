from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.api import developers, apps, api_users, auth, webhooks, dashboard, cards, remote, community
import time

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="App 后台管理系统 API - 为 iApp 开发者提供开箱即用的后台 API 系统",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """记录请求日志"""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    response.headers["X-Process-Time"] = str(process_time)
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理"""
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "type": type(exc).__name__},
    )


# 注册路由
app.include_router(developers.router, prefix="/dev", tags=["开发者管理"])
app.include_router(apps.router, prefix="/dev/apps", tags=["应用管理"])
app.include_router(cards.router, prefix="/dev", tags=["卡密系统"])
app.include_router(api_users.router, prefix="/api/v1", tags=["终端用户管理"])
app.include_router(cards.router, prefix="/api/v1", tags=["卡密系统"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["终端用户认证"])
app.include_router(remote.router, prefix="/dev", tags=["远程管理"])
app.include_router(remote.router, prefix="/api/v1", tags=["远程管理 - 客户端"])
app.include_router(community.router, prefix="/dev", tags=["社区管理"])
app.include_router(community.router, prefix="/api/v1", tags=["社区管理 - 客户端"])
app.include_router(webhooks.router, prefix="/dev/webhooks", tags=["Webhook 管理"])
app.include_router(dashboard.router, prefix="/dev/dashboard", tags=["统计监控"])


@app.get("/")
async def root():
    """根路径"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "timestamp": time.time()}
