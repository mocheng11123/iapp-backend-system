# iApp 管理控制台 - 前端

基于 Vue3 + Vite + Element Plus 的 Web 管理后台。

## 技术栈

- **框架**: Vue 3.4
- **构建工具**: Vite 5
- **UI 组件库**: Element Plus 2.5
- **状态管理**: Pinia 2
- **路由**: Vue Router 4
- **HTTP 客户端**: Axios
- **图表**: 原生 CSS + SVG

## 功能模块

### 已实现
- 登录认证（JWT）
- 仪表盘（数据总览、趋势图表）
- 应用管理（列表、创建、删除）
- 卡密管理（批次创建、导出、吊销）

### 待完善
- 终端用户管理
- 公告管理（富文本编辑器）
- 版本管理
- 启动图配置（图片上传）
- 广告配置
- 论坛管理
- 反馈管理
- 账单管理
- 系统设置

## 快速开始

### 安装依赖

```bash
cd frontend
npm install
```

### 开发模式

```bash
npm run dev
```

访问 http://localhost:3000

### 生产构建

```bash
npm run build
```

构建产物输出到 `dist/` 目录。

## 项目结构

```
frontend/
├── src/
│   ├── api/           # API 接口定义
│   │   ├── developer.ts
│   │   ├── app.ts
│   │   ├── card.ts
│   │   └── remote.ts
│   ├── components/    # 公共组件
│   │   └── Breadcrumb.vue
│   ├── router/        # 路由配置
│   ├── stores/        # Pinia stores
│   │   └── auth.ts
│   ├── utils/         # 工具函数
│   │   └── request.ts  # Axios 封装
│   ├── views/         # 页面组件
│   │   ├── Login.vue
│   │   ├── Layout.vue
│   │   ├── Dashboard.vue
│   │   ├── apps/
│   │   ├── cards/
│   │   ├── users/
│   │   ├── remote/
│   │   ├── forum/
│   │   ├── feedback/
│   │   ├── billing/
│   │   └── settings/
│   ├── App.vue
│   └── main.ts
├── index.html
├── package.json
├── tsconfig.json
└── vite.config.ts
```

## API 代理

开发模式下通过 Vite 代理转发请求到后端：

```typescript
proxy: {
  '/dev': {
    target: 'http://localhost:8000',
    changeOrigin: true,
  },
  '/api': {
    target: 'http://localhost:8000',
    changeOrigin: true,
  },
}
```

## 认证流程

1. 用户在登录页输入邮箱密码
2. 调用 `/dev/login` 获取 JWT token
3. Token 存储到 localStorage
4. 所有 API 请求自动携带 `Authorization: Bearer <token>`
5. 401 响应自动跳转到登录页

## 部署

### Nginx配置示例

```nginx
server {
    listen 80;
    server_name admin.yourdomain.com;

    location / {
        root /var/www/admin;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    location /dev {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /api {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
    }
}
```

## 下一步

1. 完善各管理页面的 CRUD 功能
2. 集成富文本编辑器（WangEditor）
3. 图片上传功能（OSS 预签名 URL）
4. 数据可视化图表（ECharts）
5. 导出 Excel/CSV 功能
6. 权限控制（路由级 + 按钮级）
