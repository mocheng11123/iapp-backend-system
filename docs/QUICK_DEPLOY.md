# 一键部署指南

## 🚀 快速开始

只需一条命令，完成所有部署工作：

```bash
git clone https://github.com/mocheng11123/iapp-backend-system.git
cd iapp-backend-system
chmod +x auto-deploy.sh
./auto-deploy.sh
```

部署完成后访问：**http://localhost:8080/docs**

---

## 📋 自动化部署流程

部署脚本会自动执行以下 8 个步骤：

### 步骤 1/8: 系统环境检测
- 检测操作系统（Ubuntu/Debian/CentOS/Fedora 等）
- 检测包管理器（apt/yum/dnf/pacman）

### 步骤 2/8: 安装系统依赖
自动安装：curl, git, wget, gnupg, ca-certificates, lsb-release

### 步骤 3/8: Docker 环境安装
- 如果 Docker 未安装，自动下载安装
- 如果 Docker Compose 未安装，自动安装 v2.24.0
- 将当前用户添加到 docker 组（避免 sudo）

### 步骤 4/8: 端口占用检测
自动检测 8080, 8000, 5432, 6379 端口，如被占用自动调整

### 步骤 5/8: 创建配置文件
- 自动生成 backend/.env（含随机 JWT 密钥和数据库密码）
- 自动创建 docker/nginx.conf（反向代理配置）

### 步骤 6/8: 构建 Docker 镜像
- 清理旧的悬死镜像
- 使用 --no-cache 重新构建

### 步骤 7/8: 启动所有服务
依次启动：PostgreSQL → Redis → Backend → Nginx

### 步骤 8/8: 健康检查
- 等待 30 秒初始化
- 检查所有容器状态
- 测试 API 文档可访问性

---

## 🎯 部署后的服务

| 服务 | 容器名 | 端口 | 说明 |
|------|--------|------|------|
| PostgreSQL | app_backend_db | 5432 | 数据库（仅内网） |
| Redis | app_backend_redis | 6379 | 缓存（仅内网） |
| FastAPI | app_backend_api | 8000 | 后端服务 |
| Nginx | app_backend_nginx | 8080 | 反向代理（对外） |

**访问地址**:
- API 文档：http://localhost:8080/docs
- Redoc 文档：http://localhost:8080/redoc
- 后端 API: http://localhost:8080

---

## 🔧 常用命令

```bash
# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 重启服务
docker-compose restart backend

# 停止服务
docker-compose down

# 完全重置（删除所有数据）
docker-compose down -v && docker-compose up -d

# 进入容器
docker-compose exec backend bash
docker-compose exec postgres psql -U postgres
```

---

## ❓ 常见问题

**Q: 端口 8080 被占用？**
A: 脚本会自动调整为 8081

**Q: Docker 安装失败？**
A: 使用国内镜像：curl -fsSL https://get.docker.com -o get-docker.sh

**Q: 服务启动后退出？**
A: docker-compose logs backend 查看错误

---

**文档版本**: 2.0  
**更新日期**: 2026-06-03  
**GitHub**: https://github.com/mocheng11123/iapp-backend-system
