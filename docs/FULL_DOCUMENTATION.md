# iApp 后台管理系统 - 完整功能文档

## 系统概述

本系统为 iApp 开发者提供**开箱即用的商业级后台 API 系统**，在通用 App 后台架构基础上，深度融合 iApp 生态特色功能。

---

## 完整功能清单

### 一、基础架构功能

#### 1. 开发者自服务
- 注册/登录（JWT 认证）
- 个人信息管理
- 余额查询和充值
- 交易流水查询
- 多应用管理

#### 2. 终端用户管理
- 用户 CRUD（开发者 API 调用）
- 用户自主登录（JWT 双令牌）
- 双层余额系统
- 交易流水记录

#### 3. 计费与 Webhook
- API 按量计费
- 套餐管理
- Webhook 事件推送
- 开发者余额预警

---

### 二、iApp 特色功能

#### 1. 卡密系统（混合商业模式核心）

**功能说明**：
- 支持两种卡密类型：
  - **额度卡密**：兑换后增加终端用户余额（如：10 元、50 元面值）
  - **会员卡密**：兑换后激活或延长会员有效期（如：30 天、90 天 VIP）
- 开发者自定义卡密参数（面值/有效期/数量）
- 批量生成卡密，支持 CSV 导出
- 开发者 7 折购买卡密，转售赚取差价

**商业模式**：
1. 平台以 7 折价格向开发者批发卡密
2. 开发者以面值价格向终端用户零售
3. 开发者赚取 30% 差价
4. 平台通过批发卡密和 API 调用获利

**接口列表**：
| 接口 | 方法 | 认证 | 说明 |
|------|------|------|------|
| /dev/card/batches | POST | Developer JWT | 创建卡密批次 |
| /dev/card/batches | GET | Developer JWT | 批次列表 |
| /dev/card/batches/{id}/cards | GET | Developer JWT | 导出卡密 CSV |
| /dev/card/batches/{id}/revoke | POST | Developer JWT | 吊销批次 |
| /api/v1/card/redeem | POST | EndUser JWT | 终端用户兑换 |
| /api/v1/users/me/membership | GET | EndUser JWT | 查询会员信息 |

---

#### 2. 远程管理系统

**公告系统**：
- 富文本公告内容
- 生效时间范围控制
- 置顶公告
- 终端 App 实时获取

**强制更新**：
- 版本号管理（version_code + version_name）
- 强制/非强制更新标识
- 更新日志和下载链接
- 文件 MD5 校验

**启动图配置**：
- 按平台区分（Android/iOS）
- 生效时间段
- 优先级控制
- 动态切换

**广告管理**：
- 多广告位支持
- 图片/视频广告
- 权重随机展示
- 跳转链接配置

**接口列表**：
| 接口 | 方法 | 认证 | 说明 |
|------|------|------|------|
| /dev/announcements | POST/GET | Developer JWT | 公告管理 |
| /api/v1/announcements | GET | App API Key | 获取生效公告 |
| /dev/versions | POST/GET | Developer JWT | 版本管理 |
| /api/v1/version/latest | GET | App API Key | 检查更新 |
| /dev/splash | POST/GET | Developer JWT | 启动图配置 |
| /api/v1/splash/current | GET | App API Key | 当前启动图 |
| /dev/ads | POST/GET | Developer JWT | 广告配置 |
| /api/v1/ads/{slot} | GET | App API Key | 广告位内容 |

---

#### 3. 社区运营系统

**论坛模块**：
- 多版块管理
- 帖子发布/浏览
- 评论回复（支持楼中楼）
- 置顶/加精管理
- 用户封禁

**反馈系统**：
- 用户提交反馈（支持图片）
- 状态跟踪（待处理/已读/已解决/已忽略）
- 开发者回复
- 邮件通知（Celery 异步）

**接口列表**：
| 接口 | 方法 | 认证 | 说明 |
|------|------|------|------|
| /dev/forum/boards | POST/GET | Developer JWT | 版块管理 |
| /api/v1/forum/posts | POST/GET | EndUser JWT | 发布/查看帖子 |
| /api/v1/forum/{id}/replies | POST/GET | EndUser JWT | 回复帖子 |
| /dev/forum/posts/{id} | DELETE | Developer JWT | 删除帖子 |
| /api/v1/feedback | POST | EndUser JWT | 提交反馈 |
| /dev/feedback | GET | Developer JWT | 反馈列表 |
| /dev/feedback/{id}/status | PUT | Developer JWT | 更新状态 |
| /dev/feedback/{id}/reply | POST | Developer JWT | 回复反馈 |

---

### 三、数据库表结构

#### 新增数据表（iApp 特色）

1. **card_batches** - 卡密批次表
2. **cards** - 卡密表
3. **user_memberships** - 终端会员表
4. **announcements** - 公告表
5. **app_versions** - 版本表
6. **splash_configs** - 启动图表
7. **ads** - 广告表
8. **forum_boards** - 论坛版块表
9. **forum_posts** - 论坛帖子表
10. **forum_replies** - 论坛回复表
11. **feedbacks** - 反馈表
12. **email_logs** - 邮件发送记录表

---

### 四、混合商业模式

#### B2D 收入（平台向开发者收费）
- 开发者套餐月费
- API 调用超量费用
- 卡密批发差价（30%）
- 增值服务（存储、CDN 等）

#### B2C 收入（开发者向终端用户收费）
- 卡密零售（开发者自主定价）
- 会员订阅（开发者自主定价）
- 平台不参与分成，通过批发获利

#### 计费流程示例
```
1. 开发者充值 1000 元 → 开发者余额 +1000
2. 创建 100 张 10 元面值额度卡密 → 扣除 700 元（7 折）
3. 开发者以 10 元/张零售 → 开发者收入 1000 元（毛利 300 元）
4. 终端用户兑换卡密 → 用户余额 +10 元
5. 开发者 API 调用 → 按量扣费
```

---

### 五、完整 API 接口总览

#### 开发者管理（/dev）
- POST /dev/register - 注册
- POST /dev/login - 登录
- GET/PUT /dev/profile - 个人信息
- GET /dev/balance - 余额
- POST /dev/recharge - 充值
- GET /dev/transactions - 流水

#### 应用管理（/dev/apps）
- POST /dev/apps - 创建
- GET /dev/apps - 列表
- GET/PUT/DELETE /dev/apps/{id} - 详情/修改/删除
- POST /dev/apps/{id}/rotate-key - 轮换密钥

#### 卡密系统（/dev/card + /api/v1/card）
- POST /dev/card/batches - 创建批次
- GET /dev/card/batches - 批次列表
- GET /dev/card/batches/{id}/cards - 导出
- POST /dev/card/batches/{id}/revoke - 吊销
- POST /api/v1/card/redeem - 兑换
- GET /api/v1/users/me/membership - 会员信息

#### 远程管理（/dev + /api/v1）
- /dev/announcements - 公告管理（后台）
- /api/v1/announcements - 获取公告（客户端）
- /dev/versions - 版本管理（后台）
- /api/v1/version/latest - 版本检查（客户端）
- /dev/splash - 启动图配置（后台）
- /api/v1/splash/current - 获取启动图（客户端）
- /dev/ads - 广告配置（后台）
- /api/v1/ads/{slot} - 获取广告（客户端）

#### 社区运营（/dev + /api/v1）
- /dev/forum/boards - 版块管理
- /api/v1/forum/posts - 帖子管理
- /api/v1/forum/{id}/replies - 回复管理
- /api/v1/feedback - 提交反馈
- /dev/feedback - 反馈管理（后台）

#### 终端用户管理（/api/v1）
- /api/v1/users - 用户 CRUD
- /api/v1/users/{id}/balance - 余额管理
- /api/v1/auth/login - 登录
- /api/v1/auth/register - 注册

#### 统计监控（/dev/dashboard）
- /dev/dashboard/overview - 总览
- /dev/apps/{id}/stats - 应用统计
- /dev/api-usage - API 使用明细
- /dev/billing/prediction - 费用预估

---

### 六、技术栈

| 层次 | 技术选型 | 说明 |
|------|----------|------|
| 后端框架 | FastAPI (Python) | 异步，自动生成 OpenAPI 文档 |
| 数据库 | PostgreSQL + Redis | 主数据 + 缓存/限流/队列 |
| 任务队列 | Celery + Redis | 异步扣费、Webhook 重试、邮件发送 |
| 认证 | JWT + API Key | 双认证体系 |
| 邮件服务 | SMTP（可配置） | 反馈通知、余额预警 |
| 部署 | Docker Compose + Nginx | 一键部署 |

---

### 七、快速开始

#### 1. Docker 部署（完整服务）

```bash
# 克隆项目
git clone https://github.com/your-org/app-backend-system.git
cd app-backend-system

# 修改环境变量
cp backend/.env.example backend/.env
# 编辑 .env 设置 JWT_SECRET_KEY 等

# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f
```

服务端口：
- API + Nginx: http://localhost:80
- Web 控制台：http://localhost:3000（开发模式）或 80（生产模式）
- PostgreSQL: 5432
- Redis: 6379

#### 2. 本地开发

**后端**：
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# 编辑 .env 配置本地数据库

# 运行数据库迁移
alembic upgrade head

# 启动开发服务器
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**前端**：
```bash
cd frontend
npm install
npm run dev
```

访问 http://localhost:3000 登录管理后台。

#### 3. API 文档

启动后端后访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

### 八、Web 管理控制台

#### 功能模块

| 模块 | 路径 | 功能 | 状态 |
|------|------|------|------|
| 仪表盘 | /dashboard | 数据总览、趋势图表、余额管理 | ✅ 完成 |
| 应用管理 | /apps | 创建/配置/删除应用 | ✅ 完成 |
| 卡密管理 | /cards | 批次创建、导出、吊销 | ✅ 完成 |
| 终端用户 | /users | 列表、搜索、禁用、导出 | ✅ 完成 |
| 公告管理 | /announcements | 富文本编辑、发布/下架 | ✅ 完成 |
| 版本管理 | /versions | 版本发布、MD5、强制更新 | ✅ 完成 |
| 启动图 | /splash | 图片预览、优先级 | ✅ 完成 |
| 广告位 | /ads | 广告配置、权重管理 | ✅ 完成 |
| 论坛管理 | /forum | 版块管理 | ✅ 完成 |
| 反馈管理 | /feedback | 查看/回复/状态跟踪 | ✅ 完成 |
| 账单管理 | /billing | 流水查询、充值、导出 | ✅ 完成 |
| 系统设置 | /settings | Webhook、通知、安全 | ✅ 完成 |

#### 界面预览

**登录页**：
- 邮箱密码登录
- API 文档链接
- 注册入口

**仪表盘**：
- 4 个统计卡片（应用总数、终端用户、今日 API 调用、今日消费）
- 余额信息和充值入口
- 费用预估（今日/本月/可用天数）
- 7 天 API 调用趋势图

**应用管理**：
- 应用列表表格
- 新建应用弹窗
- API Key 显示（创建时一次性）
- 配置和删除操作

**卡密管理**：
- 批次列表（名称、类型、数量、价格）
- 新建批次表单（额度/会员、数量、面值/天数）
- 导出 CSV
- 吊销操作

#### 技术架构

```
Vue 3 + Vite
├── Element Plus (UI)
├── Pinia (状态管理)
├── Vue Router (路由)
├── Axios (HTTP)
└── 原生 CSS（图表）
```

---

### 九、安全特性

- 密码 bcrypt 哈希（cost=12）
- API Key SHA256 存储
- JWT RS256 签名
- 登录失败锁定（5 次/15 分钟）
- SQL 注入防护（参数化查询）
- 数据隔离（强制 app_id 过滤）
- 卡密加密生成（secrets.token_urlsafe）

---

### 十、待办事项

- [ ] 前端管理控制台（Vue3 + Element Plus）
- [ ] 邮件服务集成（SMTP 配置）
- [ ] Celery 异步任务（Webhook/邮件）
- [ ] 支付集成（支付宝/微信）
- [ ] Prometheus 监控
- [ ] 自动化测试
- [ ] CI/CD 流水线

---

**文档版本**：2.0  
**最后更新**：2026-06-03  
**演示服务器**：https://8000-3d3fb86f924418a0.monkeycode-ai.online/docs
