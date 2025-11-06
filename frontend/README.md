# SentiScore 管理后台

基于Vue3 + TypeScript + Element Plus开发的Web管理后台

## 技术栈

- **框架**: Vue 3 (Composition API)
- **语言**: TypeScript
- **构建工具**: Vite
- **UI组件库**: Element Plus
- **图表库**: Apache ECharts
- **状态管理**: Pinia
- **路由**: Vue Router 4
- **样式**: Tailwind CSS
- **HTTP客户端**: Axios
- **开发工具**: ESLint + Prettier

## 项目结构

```text
frontend/
├── public/                 # 静态资源
├── src/
│   ├── components/         # 通用组件
│   ├── views/             # 页面组件
│   ├── router/            # 路由配置
│   ├── stores/            # Pinia状态管理
│   ├── api/               # API接口
│   ├── types/             # TypeScript类型定义
│   ├── utils/             # 工具函数
│   ├── styles/            # 样式文件
│   ├── App.vue            # 根组件
│   └── main.ts            # 入口文件
├── package.json           # 项目依赖
├── tsconfig.json          # TypeScript配置
├── vite.config.ts         # Vite配置
└── README.md              # 项目说明
```

## 开发指南

### 安装依赖

```bash
npm install
```

### 开发环境启动

```bash
npm run dev
```

### 构建生产版本

```bash
npm run build
```

### 代码检查

```bash
npm run lint
```

## 功能模块

- **仪表盘**: 系统概览、统计数据、图表展示
- **用户管理**: 用户列表、用户详情、状态管理
- **订单管理**: 订单列表、订单详情、财务统计
- **系统设置**: 平台配置、套餐管理、系统日志
- **个人中心**: 用户信息、密码修改、API Key管理
