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

## 快速开始

### 本地开发部署

```bash
# 1. 克隆项目
git clone https://github.com/0xByteBard404/SentiScore.git
cd SentiScore

# 2. 安装依赖
pip install -r requirements.txt

# 3. 运行服务
python app.py
```

服务将在 `http://127.0.0.1:5000` 上启动。

### Docker部署

```bash
# 构建镜像
docker build -t sentiscore .

# 运行容器
docker run -d -p 5000:5000 sentiscore
```

### Docker Compose部署

```bash
docker-compose up -d
```

## API接口

### 单文本情感分析

```bash
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

```bash
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

```bash
curl -X POST http://localhost:5000/segment \
     -H "Content-Type: application/json" \
     -d '{"text": "今天天气很好，我很开心"}'
```

响应示例：
```json
{
  "data": {
    "tokens": ["今天", "天气", "很", "好", "，", "我", "很", "开心"],
    "text_length": 11,
    "token_count": 8
  },
  "timestamp": 1761639505
}
```

### 批量文本分词

```bash
curl -X POST http://localhost:5000/segment/batch \
     -H "Content-Type: application/json" \
     -d '{"texts": ["今天天气很好", "我很开心"]}'
```

响应示例：
```json
{
  "data": [
    {
      "tokens": ["今天", "天气", "很", "好"],
      "text_length": 6,
      "token_count": 4
    },
    {
      "tokens": ["我", "很", "开心"],
      "text_length": 4,
      "token_count": 3
    }
  ],
  "timestamp": 1761639525
}
```

## 配置说明

通过环境变量配置服务：

- `FLASK_ENV` - 运行环境 (development/production)
- `MODEL_DOWNLOAD_STRATEGY` - 模型下载策略 (auto/cn_priority/global_priority)
- `BATCH_SIZE` - 批处理大小限制
- `LRU_CACHE_SIZE` - 缓存大小

更多详细配置请参考 [config.py](config.py) 文件。