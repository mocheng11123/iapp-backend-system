#!/bin/bash

# iApp 后台管理系统 - 一键部署脚本

set -e

echo "🚀 iApp 后台管理系统 - 一键部署"
echo "================================"

# 1. 检查 .env 文件
if [ ! -f backend/.env ]; then
    echo "📝 创建 .env 配置文件..."
    cp backend/.env.example backend/.env
    
    # 生成随机 JWT_SECRET_KEY
    JWT_KEY=$(openssl rand -hex 32 2>/dev/null || cat /dev/urandom | tr -dc 'a-f0-9' | fold -w 64 | head -n 1)
    sed -i "s/JWT_SECRET_KEY=.*/JWT_SECRET_KEY=$JWT_KEY/" backend/.env
    
    echo "✅ .env 文件已创建（JWT_SECRET_KEY 已自动生成）"
else
    echo "✅ .env 文件已存在"
fi

# 2. 检查 Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装，请先安装 Docker"
    exit 1
fi

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose 未安装"
    exit 1
fi

# 3. 启动服务
echo "🐳 启动 Docker 服务..."
if command -v docker-compose &> /dev/null; then
    docker-compose up -d
else
    docker compose up -d
fi

# 4. 等待服务启动
echo "⏳ 等待服务启动..."
sleep 10

# 5. 检查服务状态
echo "📊 服务状态检查..."
if command -v docker-compose &> /dev/null; then
    docker-compose ps
else
    docker compose ps
fi

# 6. 显示访问信息
echo ""
echo "✅ 部署完成！"
echo "=============="
echo "🌐 API 文档：http://localhost/docs"
echo "🔧 后端 API：http://localhost:8000"
echo "💻 管理后台：需要部署前端（见 frontend/README.md）"
echo ""
echo "📝 快速开始："
echo "1. 访问 http://localhost/docs 注册开发者账号"
echo "2. 使用 /dev/register 接口创建第一个账号"
echo "3. 登录管理后台（前端部署后）"
echo ""
echo "🔧 常用命令："
echo "  查看日志：docker-compose logs -f"
echo "  停止服务：docker-compose down"
echo "  重启服务：docker-compose restart"
