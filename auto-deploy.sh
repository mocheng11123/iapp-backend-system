#!/bin/bash

# iApp 后台管理系统 - 全自动一键部署脚本
# 功能：检测环境、安装依赖、配置 Docker、自动部署、健康检查、Nginx 反向代理

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印函数
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

echo "=========================================="
echo "  iApp 后台管理系统 - 全自动部署脚本"
echo "=========================================="
echo ""

# ==================== 步骤 1: 系统环境检测 ====================
print_info "步骤 1/8: 检测系统环境..."

# 检测操作系统
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
    echo "  操作系统：$OS $VERSION_ID"
else
    OS="unknown"
    echo "  操作系统：未知"
fi

# 检测包管理器
if command -v apt-get &> /dev/null; then
    PM="apt"
elif command -v yum &> /dev/null; then
    PM="yum"
elif command -v dnf &> /dev/null; then
    PM="dnf"
elif command -v pacman &> /dev/null; then
    PM="pacman"
else
    PM="unknown"
fi
echo "  包管理器：$PM"

# ==================== 步骤 2: 安装系统依赖 ====================
print_info "步骤 2/8: 安装系统依赖..."

case $PM in
    apt)
        sudo apt-get update -qq
        sudo apt-get install -y -qq curl git wget gnupg ca-certificates lsb-release
        ;;
    yum|dnf)
        sudo $PM install -y -q curl git wget
        ;;
    pacman)
        sudo pacman -S --noconfirm --quiet curl git wget
        ;;
    *)
        print_warning "未知包管理器，跳过系统依赖安装"
        ;;
esac

print_success "系统依赖安装完成"

# ==================== 步骤 3: 安装/检测 Docker ====================
print_info "步骤 3/8: 检测 Docker 环境..."

if ! command -v docker &> /dev/null; then
    print_warning "Docker 未安装，正在安装..."
    
    case $OS in
        ubuntu|debian)
            curl -fsSL https://get.docker.com -o get-docker.sh
            sudo sh get-docker.sh
            sudo systemctl start docker
            sudo systemctl enable docker
            rm get-docker.sh
            ;;
        centos|fedora|rhel)
            curl -fsSL https://get.docker.com -o get-docker.sh
            sudo sh get-docker.sh
            sudo systemctl start docker
            sudo systemctl enable docker
            rm get-docker.sh
            ;;
        *)
            print_error "不支持的操作系统，请手动安装 Docker"
            exit 1
            ;;
    esac
    
    print_success "Docker 安装完成"
else
    DOCKER_VERSION=$(docker --version)
    echo "  Docker 已安装：$DOCKER_VERSION"
fi

# 检测 Docker Compose
if command -v docker-compose &> /dev/null; then
    COMPOSE_VERSION=$(docker-compose --version)
    echo "  Docker Compose 已安装：$COMPOSE_VERSION"
    COMPOSE_CMD="docker-compose"
elif docker compose version &> /dev/null; then
    COMPOSE_VERSION=$(docker compose version)
    echo "  Docker Compose Plugin 已安装：$COMPOSE_VERSION"
    COMPOSE_CMD="docker compose"
else
    print_warning "Docker Compose 未安装，正在安装..."
    
    sudo mkdir -p /usr/local/lib/docker/cli-plugins
    curl -SL "https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-$(uname -s)-$(uname -m)" \
        -o /tmp/docker-compose
    sudo chmod +x /tmp/docker-compose
    sudo mv /tmp/docker-compose /usr/local/lib/docker/cli-plugins/docker-compose
    sudo ln -s /usr/local/lib/docker/cli-plugins/docker-compose /usr/local/bin/docker-compose
    
    COMPOSE_CMD="docker-compose"
    print_success "Docker Compose 安装完成"
fi

# 将当前用户添加到 docker 组（避免每次都用 sudo）
if ! groups $USER | grep -q docker; then
    sudo usermod -aG docker $USER
    print_warning "已将用户添加到 docker 组，需要重新登录或执行：newgrp docker"
fi

# ==================== 步骤 4: 检测端口占用 ====================
print_info "步骤 4/8: 检测端口占用..."

# 检测端口占用
check_port() {
    if command -v netstat &> /dev/null; then
        netstat -tuln | grep -q ":$1 "
    elif command -v ss &> /dev/null; then
        ss -tuln | grep -q ":$1 "
    else
        # 尝试直接绑定测试
        ! (echo > /dev/tcp/localhost/$1) 2>/dev/null
    fi
}

# 默认端口配置
NGINX_PORT=${NGINX_PORT:-8080}
BACKEND_PORT=${BACKEND_PORT:-8000}
POSTGRES_PORT=${POSTGRES_PORT:-5432}
REDIS_PORT=${REDIS_PORT:-6379}

# 检查端口
PORTS_TO_CHECK="$NGINX_PORT $BACKEND_PORT $POSTGRES_PORT $REDIS_PORT"
for PORT in $PORTS_TO_CHECK; do
    if check_port $PORT; then
        print_warning "端口 $PORT 被占用"
        if [ $PORT -eq $NGINX_PORT ]; then
            NGINX_PORT=8081
            print_info "Nginx 端口调整为：$NGINX_PORT"
        fi
    else
        print_success "端口 $PORT 可用"
    fi
done

# ==================== 步骤 5: 创建配置文件 ====================
print_info "步骤 5/8: 创建配置文件..."

# 创建 .env 文件
if [ ! -f backend/.env ]; then
    print_info "创建 .env 配置文件..."
    
    # 生成随机 JWT_SECRET_KEY
    if command -v openssl &> /dev/null; then
        JWT_KEY=$(openssl rand -hex 32)
    else
        JWT_KEY=$(cat /dev/urandom | tr -dc 'a-f0-9' | fold -w 64 | head -n 1)
    fi
    
    # 生成随机数据库密码
    DB_PASSWORD=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 16 | head -n 1)
    
    cat > backend/.env << EOF
# iApp 后台管理系统环境配置
# 自动生成于 $(date '+%Y-%m-%d %H:%M:%S')

# JWT 配置
JWT_SECRET_KEY=$JWT_KEY
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440

# 数据库配置
DATABASE_URL=postgresql+asyncpg://postgres:$DB_PASSWORD@postgres:5432/app_backend
POSTGRES_USER=postgres
POSTGRES_PASSWORD=$DB_PASSWORD
POSTGRES_DB=app_backend

# Redis 配置
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis://redis:6379/2

# 应用配置
DEBUG=False
API_PREFIX=/api/v1
EOF
    
    # 替换 docker-compose.yml 中的默认密码
    sed -i "s/POSTGRES_PASSWORD: postgres/POSTGRES_PASSWORD: $DB_PASSWORD/g" docker-compose.yml
    sed -i "s/postgres:postgres/postgres:$DB_PASSWORD/g" docker-compose.yml
    
    print_success ".env 文件已创建（JWT_SECRET_KEY 和数据库密码已自动生成）"
else
    print_success ".env 文件已存在"
fi

# 创建 Nginx 配置文件
mkdir -p docker
if [ ! -f docker/nginx.conf ]; then
    print_info "创建 Nginx 配置文件..."
    
    cat > docker/nginx.conf << EOF
events {
    worker_connections 1024;
}

http {
    # upstream 配置
    upstream backend {
        server backend:8000;
        keepalive 32;
    }

    # 主服务器配置
    server {
        listen 80;
        server_name localhost;
        
        # 日志配置
        access_log /var/log/nginx/access.log;
        error_log /var/log/nginx/error.log;
        
        # 客户端配置
        client_max_body_size 100M;
        
        # API 代理
        location /api/ {
            proxy_pass http://backend;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
            proxy_http_version 1.1;
            proxy_set_header Upgrade \$http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
        }
        
        # API 文档
        location /docs {
            proxy_pass http://backend/docs;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        }
        
        location /openapi.json {
            proxy_pass http://backend/openapi.json;
            proxy_set_header Host \$host;
        }
        
        # Redoc 文档
        location /redoc {
            proxy_pass http://backend/redoc;
            proxy_set_header Host \$host;
        }
        
        # 健康检查
        location /health {
            proxy_pass http://backend/health;
            access_log off;
        }
        
        # 根路径
        location / {
            proxy_pass http://backend;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        }
    }
}
EOF
    
    print_success "Nginx 配置文件已创建"
else
    print_success "Nginx 配置文件已存在"
fi

# ==================== 步骤 6: 构建 Docker 镜像 ====================
print_info "步骤 6/8: 构建 Docker 镜像..."

cd "$(dirname "$0")"

# 清理旧镜像（可选）
print_info "清理旧的悬空镜像..."
$COMPOSE_CMD images -q | xargs -r docker images --filter "dangling=true" -q --no-trunc | xargs -r docker rmi || true

# 构建镜像
print_info "开始构建镜像（可能需要 3-10 分钟）..."
$COMPOSE_CMD build --no-cache

print_success "镜像构建完成"

# ==================== 步骤 7: 启动服务 ====================
print_info "步骤 7/8: 启动所有服务..."

# 启动服务
$COMPOSE_CMD up -d

print_success "服务启动成功"

# ==================== 步骤 8: 健康检查 ====================
print_info "步骤 8/8: 服务健康检查..."

# 等待服务启动
print_info "等待服务初始化（30 秒）..."
sleep 30

# 检查各个服务状态
SERVICES=("postgres" "redis" "backend" "nginx")
ALL_HEALTHY=true

for SERVICE in "${SERVICES[@]}"; do
    CONTAINER_NAME="app_backend_$SERVICE"
    
    if $COMPOSE_CMD ps | grep -q "$CONTAINER_NAME"; then
        if $COMPOSE_CMD ps | grep "$CONTAINER_NAME" | grep -q "healthy\|Up"; then
            print_success "$SERVICE 服务运行正常"
        else
            print_warning "$SERVICE 服务状态异常"
            ALL_HEALTHY=false
        fi
    else
        print_error "$SERVICE 服务未运行"
        ALL_HEALTHY=false
    fi
done

# 检查 API 可访问性
print_info "检查 API 可访问性..."
if curl -f -s http://localhost:$NGINX_PORT/docs > /dev/null; then
    print_success "API 文档可访问：http://localhost:$NGINX_PORT/docs"
else
    print_warning "API 文档访问失败，正在重试..."
    sleep 10
    if curl -f -s http://localhost:$NGINX_PORT/docs > /dev/null; then
        print_success "API 文档可访问：http://localhost:$NGINX_PORT/docs"
    else
        print_error "API 文档访问失败"
    fi
fi

# ==================== 部署完成 ====================
echo ""
echo "=========================================="
if [ "$ALL_HEALTHY" = true ]; then
    print_success "部署完成！"
else
    print_warning "部署完成，但部分服务状态异常"
fi
echo "=========================================="

echo ""
echo "📊 服务访问信息："
echo "  🌐 API 文档：http://localhost:$NGINX_PORT/docs"
echo "  🔧 后端 API：http://localhost:$NGINX_PORT"
echo "  📝 Redoc文档：http://localhost:$NGINX_PORT/redoc"
echo "  💾 数据库：localhost:$POSTGRES_PORT"
echo "  📦 Redis：localhost:$REDIS_PORT"
echo ""
echo "📝 快速开始："
echo "  1. 访问 http://localhost:$NGINX_PORT/docs"
echo "  2. 点击 /dev/register 注册开发者账号"
echo "  3. 点击 /dev/login 登录获取 Token"
echo "  4. 点击 Authorize 输入 Token"
echo "  5. 开始使用所有管理接口"
echo ""
echo "🔧 常用命令："
echo "  查看服务状态：$COMPOSE_CMD ps"
echo "  查看日志：$COMPOSE_CMD logs -f"
echo "  查看特定服务日志：$COMPOSE_CMD logs -f backend"
echo "  重启服务：$COMPOSE_CMD restart"
echo "  停止服务：$COMPOSE_CMD down"
echo "  完全重置：$COMPOSE_CMD down -v && $COMPOSE_CMD up -d"
echo ""
echo "🔒 安全提示："
echo "  - JWT_SECRET_KEY 和数据库密码已自动生成并保存在 backend/.env"
echo "  - 生产环境请修改默认密码并配置 HTTPS"
echo "  - 数据库端口 5432 仅在 Docker 内部暴露，外部无法访问"
echo ""
echo "📁 配置文件位置："
echo "  - 环境配置：backend/.env"
echo "  - Nginx 配置：docker/nginx.conf"
echo "  - Docker Compose: docker-compose.yml"
echo ""
echo "=========================================="
echo ""

# 自动打开浏览器（如果支持）
if command -v xdg-open &> /dev/null; then
    print_info "正在打开 API 文档..."
    xdg-open "http://localhost:$NGINX_PORT/docs" &> /dev/null || true
elif command -v open &> /dev/null; then
    print_info "正在打开 API 文档..."
    open "http://localhost:$NGINX_PORT/docs" &> /dev/null || true
fi

exit 0
