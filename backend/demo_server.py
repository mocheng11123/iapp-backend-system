"""
App 后台管理系统 - 简化演示服务器
仅用于展示项目结构和 API 文档
实际使用需要 PostgreSQL 和 Redis
"""
from fastapi import FastAPI

app = FastAPI(
    title="App 后台管理系统",
    version="1.0.0",
    description="为 App 开发者提供开箱即用的后台 API 系统",
)


@app.get("/")
async def root():
    """根路径"""
    return {
        "name": "App 后台管理系统",
        "version": "1.0.0",
        "status": "Demo Mode",
        "message": "此为演示模式，完整功能需要 PostgreSQL 和 Redis",
        "docs": "/docs",
        "redoc": "/redoc",
    }


@app.get("/health")
async def health():
    """健康检查"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
