# 情感分析API服务

基于cemotion情感分析库封装的Flask Restful API服务，提供中文文本情感分析和分词功能。

## 核心特性

- 🎯 高精度情感分析：基于预训练 BERT 模型，专门针对中文文本优化
- ✂️  文本分词功能：支持中文文本分词处理
- ⚡ 高性能设计：支持批量处理、结果缓存和 GPU 加速
- 🌐 多环境部署：支持 Docker、Docker Compose 和传统部署方式
- 🔄 模块化架构：清晰的代码结构，便于维护和扩展
- 🌍 多源下载：支持国内外多种模型镜像源，适应不同网络环境
- 📊 实时监控：内置健康检查和性能指标接口
- 💾 模型缓存持久化：自动缓存模型文件，避免重复下载
- 🖥️ 管理后台：提供Web管理界面，支持用户认证、API密钥管理、调用统计等功能

## 快速开始

### 本地开发部署

````bash
# 1. 克隆项目
git clone https://github.com/0xByteBard404/SentiScore.git
cd SentiScore

# 2. 安装后端依赖
pip install -r requirements.txt

# 3. 安装前端依赖
cd frontend
npm install

# 4. 启动后端服务
cd ..
python app.py

# 5. 启动前端开发服务器（新终端窗口）
cd frontend
npm run dev
```

服务将在以下地址启动：
- 后端API: `http://127.0.0.1:5000`
- 前端管理后台: `http://localhost:5173`

### Docker部署

````bash
# 构建镜像
docker build -t sentiscore .

# 运行容器（带持久化缓存）
docker run -d -p 5000:5000 \
  -v $(pwd)/cemotion_cache:/app/.cemotion_cache \
  -v $(pwd)/modelscope_cache:/app/.cache/modelscope \
  sentiscore
```

### Docker Compose部署

```
# 创建 Docker Volume 用于数据库持久化（推荐）
./init_volume.sh  # Linux/macOS
# 或
init_volume.bat   # Windows

# 启动服务
docker-compose up -d
```

### 完整服务部署（包含前端管理后台）

```
# 创建 Docker Volume 用于数据库持久化（推荐）
docker volume create SentiScore_sqlite_data
# 或
./init_volume.sh  # Linux/macOS
# 或
init_volume.bat   # Windows

# 构建并启动完整的前后端服务
docker-compose -f docker-compose.full.yml up -d
```

### 一键部署脚本

为了简化部署过程，项目提供了两个一键部署脚本：

- `deploy.sh` - 适用于 Linux/macOS 系统的 Bash 脚本
- `deploy.ps1` - 适用于 Windows 系统的 PowerShell 脚本

这些脚本会自动检查 Docker 环境，停止正在运行的服务，删除旧镜像，然后重新构建和启动服务。

**Linux/macOS 使用方式：**
```bash
chmod +x deploy.sh
./deploy.sh
```

**Windows 使用方式：**
```powershell
./deploy.ps1
```

访问地址：
- 前端管理后台: `http://localhost:80`
- 后端API: `http://localhost:5000`

模型文件将被缓存到 `cemotion_cache` 和 `modelscope_cache` 目录中，避免每次容器启动时重新下载。首次运行时会下载所需模型，后续启动将直接使用缓存的模型文件。

数据库文件将被持久化存储在 Docker Volume 中，即使容器被删除，数据也不会丢失。

## 数据库持久化

SentiScore 使用 SQLite 作为数据库，并支持多种持久化方式：

### 推荐方式：使用 Docker Volume（推荐）

步骤 1：创建一个命名卷（Named Volume）

````bash
docker volume create SentiScore_sqlite_data
```

步骤 2：运行容器时挂载该卷到数据库文件所在目录

````bash
docker run -d \
  --name myapp \
  -v SentiScore_sqlite_data:/app/instance \
  your-app-image
```

注意：挂载的是目录，而不是单个文件，以避免权限或文件不存在的问题。

这样，即使容器被删除，SentiScore_sqlite_data 卷中的数据（包括 sentiscore.db）依然保留。下次启动新容器时，只需挂载同一个卷即可继续使用原有数据。

### 替代方式：绑定挂载（Bind Mount）到宿主机目录

如果你希望直接在宿主机上看到数据库文件（便于备份、调试等），可以使用绑定挂载：

```
# 假设宿主机目录为 /host/sqlite_data
mkdir -p /host/sqlite_data

docker run -d \
  --name myapp \
  -v /host/sqlite_data:/app/instance \
  your-app-image
```

这样，数据库文件会直接保存在宿主机的 `/host/sqlite_data/sentiscore.db` 中。

## API接口

### 单文本情感分析

````bash
curl -X POST http://localhost:5000/analyze \
     -H "Content-Type: application/json" \
     -d '{"text": "今天天气很好，我很开心"}'
```

响应示例：
```json
{
  "data": {
    "confidence": 0.9999,
    "emotion": "正面",
    "emotion_score": 0.999962,
    "text_length": 11
  },
  "timestamp": 1761632396
}
```

### 批量情感分析

````bash
curl -X POST http://localhost:5000/batch \
     -H "Content-Type: application/json" \
     -d '{"texts": ["今天天气很好", "我很开心", "但也有点累"]}'
```

响应示例：
```json
{
  "data": [
    {
      "confidence": 0.9999,
      "emotion": "正面",
      "emotion_score": 0.999963,
      "text_length": 6
    },
    {
      "confidence": 0.9999,
      "emotion": "正面",
      "emotion_score": 0.999962,
      "text_length": 4
    },
    {
      "confidence": 0.805,
      "emotion": "负面",
      "emotion_score": 0.097476,
      "text_length": 5
    }
  ],
  "timestamp": 1761632419
}
```

### 文本分词

````bash
curl -X POST http://localhost:5000/segment \
     -H "Content-Type: application/json" \
     -d '{"text": "今天天气很好，我很开心"}'
```

> 注意：单条文本长度不能超过2048个字符，超过部分会被截断处理

响应示例：

### 长文本分词

```bash
curl -X POST http://localhost:5000/segment/long \
     -H "Content-Type: application/json" \
     -H "X-API-Key: your_api_key_here" \
     -d '{"text": "这是一个超过2048字符的长文本..."}'
```

> 注意：长文本分词接口理论上支持任意长度文本，但建议不超过10000字符。系统会自动分块处理超长文本。

响应示例：
```
{
  "data": {
    "tokens": ["这是一个", "超过512字符", "的长文本..."],
    "text_length": 2048,
    "token_count": 3
  },
  "timestamp": 1761639525
}
```

## 管理后台功能

SentiScore 提供了完整的Web管理后台，用户可以通过浏览器界面管理API密钥、查看调用统计等。

主要功能包括：

1. **用户认证**
   - 用户注册和登录
   - JWT Token认证机制
   - 密码重置功能

2. **API密钥管理**
   - 创建、编辑、删除API密钥
   - 设置密钥权限（读取/写入）
   - 配额管理（设置调用上限）
   - 查看密钥使用情况

3. **调用统计**
   - 实时查看API调用情况
   - 图表展示调用趋势
   - 按接口类型统计使用情况

## 配置说明

通过环境变量配置服务：

- `FLASK_ENV` - 运行环境 (development/production)
- `MODEL_DOWNLOAD_STRATEGY` - 模型下载策略 (auto/cn_priority/global_priority)
- `BATCH_SIZE` - 批处理大小限制
- `LRU_CACHE_SIZE` - 缓存大小

更多详细配置请参考 [config.py](config.py) 文件。

## 许可证

本项目采用 MIT 许可证。

MIT License

Copyright (c) 2025 0xByteBard404
