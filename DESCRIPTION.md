# SentiScore 项目描述

## 项目概述

SentiScore 是一个基于 cemotion 情感分析库封装的轻量级 Flask RESTful API 服务，
专注于提供高精度的中文文本情感分析能力。该项目旨在简化对复杂 BERT 模型的调用流程，
提供高性能、易部署的情感分析接口。同时，项目还提供了完整的Web管理后台，方便用户管理API密钥和查看调用统计。

## 核心功能

- **高精度情感分析**：基于预训练 BERT 模型，专门针对中文文本优化
- **中文文本分词**：基于预训练模型的中文文本分词功能
- **多部署方式支持**：支持 Docker、Docker Compose 和传统部署方式
- **高性能设计**：支持批量处理、结果缓存和 GPU 加速
- **多环境适配**：支持国内外多种模型镜像源，适应不同网络环境
- **实时监控**：内置健康检查和性能指标接口
- **Web管理后台**：提供完整的前端管理界面，支持用户认证、API密钥管理、调用统计等功能
- **套餐计费系统**：支持多种套餐选择和配额管理

## 技术架构

### 设计模式

- 模块化分层架构：按功能划分为 api、core、models、utils 四个模块
- 工厂模式：通过 config.py 实现配置管理
- 缓存模式：使用 LRU 缓存避免重复计算
- MVC模式：前端采用Vue3 + Element Plus实现组件化开发

### 主要组件交互

- app.py 初始化 Flask 应用并注册 src.api.routes 中的路由
- routes.py 接收 HTTP 请求并调用 core.cemotion 或 core.segmentor 进行分析
- emotion_classifier 封装 cemotion 模型加载与预测逻辑
- segmentor 封装 cemotion 分词器加载与分词逻辑
- utils.helpers 提供通用工具函数（如输入验证、日志等）
- 前端通过Vue Router实现页面路由，通过Pinia进行状态管理

## 技术选型

### 后端技术栈

- **后端框架**：Flask >=3.0.0
- **AI框架**：cemotion >=2.0.0 (基于 PyTorch 的中文情感分析和分词库)
- **系统监控**：psutil >=5.9.0
- **数据库**：SQLite（开发环境）/ PostgreSQL（生产环境）
- **认证机制**：JWT Token
- **Python版本**：3.11

### 前端技术栈

- **前端框架**：Vue 3 + TypeScript
- **UI框架**：Element Plus
- **状态管理**：Pinia
- **路由管理**：Vue Router
- **构建工具**：Vite
- **图表库**：ECharts

## 部署方式

### Docker 部署

```bash
# 构建镜像
docker build -t sentiscore .

# 运行容器
docker run -d -p 5000:5000 sentiscore
```

### Docker Compose 部署

```bash
# 仅部署后端服务
docker-compose up -d

# 部署完整的前后端服务
docker-compose -f docker-compose.full.yml up -d
```

### 本地开发部署

```bash
# 安装后端依赖
pip install -r requirements.txt

# 安装前端依赖
cd frontend
npm install

# 运行后端服务
cd ..
python app.py

# 运行前端开发服务器（新终端窗口）
cd frontend
npm run dev
```

## API 接口

SentiScore 提供以下 RESTful API 接口：

1. **情感分析接口**
   - `POST /analyze` - 单文本情感分析
   - `POST /batch` - 批量文本情感分析

2. **文本分词接口**
   - `POST /segment` - 单文本分词
   - `POST /segment/batch` - 批量文本分词

3. **系统接口**
   - `GET /health` - 健康检查

4. **认证接口**
   - `POST /auth/register` - 用户注册
   - `POST /auth/login` - 用户登录
   - `POST /auth/logout` - 用户登出
   - `GET /auth/profile` - 获取用户信息
   - `PUT /auth/profile` - 更新用户信息

5. **API密钥管理接口**
   - `GET /auth/api-keys` - 获取用户所有API密钥
   - `POST /auth/api-keys` - 创建新的API密钥
   - `PUT /auth/api-keys/{id}` - 更新API密钥
   - `DELETE /auth/api-keys/{id}` - 删除API密钥
   - `POST /auth/reset-api-key` - 重置主API密钥

6. **统计接口**
   - `GET /auth/statistics` - 获取用户调用统计

详细接口文档请参见 [API_DOCUMENTATION.md](API_DOCUMENTATION.md)。

## 管理后台功能

SentiScore 提供了完整的Web管理后台，用户可以通过浏览器界面管理API密钥、查看调用统计等。

主要功能模块包括：

1. **仪表板**
   - 实时查看API调用统计
   - 图表展示调用趋势
   - 关键指标展示（总密钥数、总调用次数、今日调用次数等）

2. **API密钥管理**
   - 创建、编辑、删除API密钥
   - 设置密钥权限（读取/写入）
   - 配额管理（设置调用上限）
   - 查看密钥使用情况和配额消耗

3. **调用历史**
   - 查看API调用历史记录
   - 按时间、接口类型筛选记录
   - 查看调用详情

4. **个人资料**
   - 查看和编辑个人信息
   - 修改密码
   - 查看账户状态和套餐信息

5. **文档中心**
   - API接口文档
   - 使用指南
   - 常见问题解答

## 配置说明

通过环境变量配置服务：

- `FLASK_ENV` - 运行环境 (development/production)
- `MODEL_DOWNLOAD_STRATEGY` - 模型下载策略 (auto/cn_priority/global_priority)
- `BATCH_SIZE` - 批处理大小限制
- `LRU_CACHE_SIZE` - 缓存大小

详细配置请参考 [config.py](config.py) 文件。

## 许可证

本项目采用 MIT 许可证。

MIT License

Copyright (c) 2025 0xByteBard404
