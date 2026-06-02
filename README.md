# App 后台管理系统 (iApp 增强版)

为 iApp 开发者提供开箱即用的后台 API 系统，融合通用 App 后台架构与 iApp 生态特色功能。

## 功能特性

### 核心功能
- **开发者管理**：注册/登录/余额/套餐
- **多应用管理**：每个开发者可创建多个 App
- **终端用户管理**：App 的最终用户，可自主登录
- **双层余额系统**：开发者余额 + 终端用户余额
- **API 按量计费**：支持按次、阶梯计费
- **Webhook 事件推送**：实时同步数据

### iApp 特色功能
- **卡密系统**：支持额度卡密、会员卡密，开发者自定义
- **远程管理**：公告、强制更新、启动图/广告远程配置
- **社区运营**：论坛、反馈系统，反馈邮件通知
- **混合商业模式**：开发者付费套餐 + 终端用户卡密分成

## 技术栈

- **后端框架**：FastAPI (Python)
- **数据库**：PostgreSQL + Redis
- **任务队列**：Celery + Redis
- **认证**：JWT + API Key
- **部署**：Docker Compose + Nginx

## 快速开始

### 1. 环境要求

- Docker & Docker Compose
- 或本地环境：Python 3.11+, PostgreSQL 15+, Redis 7+

### 2. Docker 部署（推荐）

```bash
# 克隆项目
git clone https://github.com/your-org/app-backend-system.git
cd app-backend-system

# 修改环境变量
cp .env.example .env
# 编辑 .env 文件，设置 JWT_SECRET_KEY

# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f backend
```

服务启动后：
- API 服务：http://localhost:8000
- API 文档：http://localhost:8000/docs
- Nginx 代理：http://localhost:80

### 3. 本地开发

```bash
# 进入后端目录
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 复制环境变量
cp .env.example .env
# 编辑 .env 配置数据库连接

# 运行数据库迁移
alembic upgrade head

# 启动开发服务器
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 项目结构

```
app-backend-system/
├── backend/                 # FastAPI 后端
│   ├── app/
│   │   ├── api/            # API 路由
│   │   ├── core/           # 核心配置
│   │   ├── models/         # 数据库模型
│   │   ├── schemas/        # Pydantic Schema
│   │   └── services/       # 业务服务
│   ├── tests/              # 测试代码
│   ├── requirements.txt    # Python 依赖
│   └── Dockerfile
├── frontend/               # Vue3 管理控制台
│   ├── src/
│   │   ├── api/           # API 接口
│   │   ├── views/         # 页面组件
│   │   ├── router/        # 路由配置
│   │   └── stores/        # 状态管理
│   └── package.json
├── docker/                 # Docker 配置
├── docs/                   # 项目文档
├── docker-compose.yml      # Docker 编排
└── README.md
```

## 核心接口

### 开发者管理

| 接口 | 方法 | 说明 |
|------|------|------|
| /dev/register | POST | 开发者注册 |
| /dev/login | POST | 开发者登录 |
| /dev/profile | GET | 获取个人信息 |
| /dev/balance | GET | 查询余额 |
| /dev/recharge | POST | 充值 |

### 应用管理

| 接口 | 方法 | 说明 |
|------|------|------|
| /dev/apps | POST | 创建应用 |
| /dev/apps | GET | 应用列表 |
| /dev/apps/{app_id} | GET | 应用详情 |
| /dev/apps/{app_id}/rotate-key | POST | 轮换 API Key |

### 卡密系统（iApp 特色）

| 接口 | 方法 | 说明 |
|------|------|------|
| /dev/card/batches | POST | 创建卡密批次 |
| /dev/card/batches | GET | 批次列表 |
| /dev/card/batches/{id}/cards | GET | 导出卡密 CSV |
| /api/v1/card/redeem | POST | 终端用户兑换 |
| /api/v1/users/me/membership | GET | 查询会员信息 |

### 远程管理（iApp 特色）

| 接口 | 方法 | 说明 |
|------|------|------|
| /dev/announcements | POST/GET | 公告管理 |
| /api/v1/announcements | GET | 获取生效公告 |
| /dev/versions | POST/GET | 版本管理 |
| /api/v1/version/latest | GET | 检查版本更新 |
| /dev/splash | POST/GET | 启动图配置 |
| /api/v1/splash/current | GET | 获取当前启动图 |
| /dev/ads | POST/GET | 广告配置 |
| /api/v1/ads/{slot} | GET | 获取广告内容 |

### 社区运营（iApp 特色）

| 接口 | 方法 | 说明 |
|------|------|------|
| /dev/forum/boards | POST/GET | 版块管理 |
| /api/v1/forum/posts | POST/GET | 发布/查看帖子 |
| /api/v1/forum/{id}/replies | POST/GET | 回复帖子 |
| /api/v1/feedback | POST | 提交反馈 |
| /dev/feedback | GET | 反馈列表 |
| /dev/feedback/{id}/status | PUT | 更新反馈状态 |

| 接口 | 方法 | 说明 |
|------|------|------|
| /api/v1/users | POST | 创建终端用户 |
| /api/v1/users/{user_id} | GET | 查询用户 |
| /api/v1/users/{user_id}/balance | GET | 查询余额 |
| /api/v1/auth/login | POST | 终端用户登录 |

完整文档见：http://localhost:8000/docs

## 数据库迁移

使用 Alembic 管理数据库迁移：

```bash
# 进入后端目录
cd backend

# 生成新迁移
alembic revision --autogenerate -m "Description"

# 执行迁移
alembic upgrade head

# 回滚
alembic downgrade -1
```

## 配置说明

主要配置项在 `.env` 文件：

```env
# 数据库
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/app_backend

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT
JWT_SECRET_KEY=your-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=120

# 安全
BCRYPT_ROUNDS=12
LOGIN_MAX_ATTEMPTS=5

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:8080
```

## 开发指南

### 创建新的 API

1. 在 `app/models/` 中添加数据库模型
2. 在 `app/schemas/` 中定义请求/响应 Schema
3. 在 `app/api/` 中编写路由
4. 生成迁移脚本并执行

### 计费逻辑

计费逻辑在 `app/services/billing.py` 中实现：
- 根据 endpoint 和套餐确定单价
- 支持幂等去重（基于 request_id）
- 先冻结后确认的扣费机制

### Webhook 事件

支持的事件类型：
- `user.created` - 用户创建
- `user.updated` - 用户更新
- `user.balance.changed` - 余额变动
- `user.login` - 用户登录
- `developer.balance.low` - 余额预警

## 安全性

- 密码使用 bcrypt 哈希（cost=12）
- API Key 使用 SHA256 存储
- JWT 签名验证
- 登录失败锁定机制
- SQL 注入防护（参数化查询）
- 数据隔离（强制 app_id 过滤）

## 监控与运维

### 健康检查

```bash
curl http://localhost/health
```

### 日志查看

```bash
docker-compose logs -f backend
docker-compose logs -f celery_worker
```

### 数据库备份

```bash
docker exec postgres pg_dump -U postgres app_backend > backup.sql
```

## 性能指标

单机性能预估（4 核 8G）：
- QPS: 500-1000
- 响应时间：P99 < 200ms
- 数据库连接池：10-20

## 待办事项

- [ ] 前端管理控制台开发
- [ ] 支付集成（支付宝/微信）
- [ ] Prometheus 监控集成
- [ ] 自动化测试覆盖
- [ ] CI/CD 流水线

## 许可证

MIT License

## 联系方式

- 项目地址：https://github.com/your-org/app-backend-system
- 问题反馈：https://github.com/your-org/app-backend-system/issues
