# SentiScore API 接口文档

## 概述

SentiScore 是一个基于深度学习的情感分析服务，提供对中文文本的高精度情感分析能力。该服务通过 RESTful API 接口提供服务，支持单文本和批量文本的情感分析，以及文本分词功能。

## 基础信息

- **基础URL**: `http://localhost:5000`
- **协议**: HTTP/HTTPS
- **编码**: UTF-8
- **数据格式**: JSON

## 状态码

| 状态码 | 描述           |
| ------ | -------------- |
| 200    | 请求成功       |
| 400    | 请求参数错误   |
| 404    | 接口不存在     |
| 405    | 请求方法不支持 |
| 500    | 服务器内部错误 |

## 错误响应格式

所有错误响应都遵循统一的格式：

````json
{
  "code": "错误代码",
  "message": "错误描述",
  "details": "详细错误信息（可选）"
}
```

## API 接口

### 1. 健康检查

检查服务运行状态。

**请求方式**: `GET`

**请求路径**: `/health`

**请求参数**: 无

**响应示例**:

```json
{
  "status": "healthy",
  "timestamp": 1700000000,
  "model_ready": true,
  "version": "v1.0.0",
  "gpu_available": false
}
```

**响应字段说明**:

| 字段名        | 类型    | 描述             |
| ------------- | ------- | ---------------- |
| status        | string  | 服务状态         |
| timestamp     | integer | 时间戳           |
| model_ready   | boolean | 模型是否就绪     |
| version       | string  | 服务版本         |
| gpu_available | boolean | GPU是否可用      |

### 2. 单文本情感分析

对单个中文文本进行情感分析，返回情感极性和置信度。

**请求方式**: `POST`

**请求路径**: `/analyze`

**请求头**: 
- `Content-Type: application/json`

**请求参数**:

````json
{
  "text": "待分析的中文文本"
}
```

**请求示例**:

````bash
curl -X POST http://localhost:5000/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "今天天气真好，我很开心"}'
```

**成功响应示例**:

```json
{
  "data": {
    "emotion_score": 0.9876,
    "emotion": "正面",
    "confidence": 0.9752,
    "text_length": 11
  },
  "timestamp": 1700000000
}
```

**响应字段说明**:

| 字段名        | 类型    | 描述                           |
| ------------- | ------- | ------------------------------ |
| emotion_score | float   | 情感得分，范围[0,1]            |
| emotion       | string  | 情感极性，"正面"或"负面"       |
| confidence    | float   | 置信度，越接近1表示越确定      |
| text_length   | integer | 原始文本长度                   |

### 3. 批量情感分析

对多个中文文本进行批量情感分析。

**请求方式**: `POST`

**请求路径**: `/batch`

**请求头**: 
- `Content-Type: application/json`

**请求参数**:

````json
{
  "texts": ["文本1", "文本2", "..."]
}
```

**请求示例**:

````bash
curl -X POST http://localhost:5000/batch \
  -H "Content-Type: application/json" \
  -d '{"texts": ["今天天气真好", "我很不开心"]}'
```

**成功响应示例**:

```json
{
  "data": [
    {
      "emotion_score": 0.9234,
      "emotion": "正面",
      "confidence": 0.8468,
      "text_length": 6
    },
    {
      "emotion_score": 0.2345,
      "emotion": "负面",
      "confidence": 0.5310,
      "text_length": 5
    }
  ],
  "timestamp": 1700000000
}
```

### 4. 文本分词

对中文文本进行分词处理。

**请求方式**: `POST`

**请求路径**: `/segment`

**请求头**: 
- `Content-Type: application/json`

**请求参数**:

````json
{
  "text": "待分词的中文文本"
}
```

**请求示例**:

```bash
curl -X POST http://localhost:5000/segment \
  -H "Content-Type: application/json" \
  -d '{"text": "今天天气很好，我很开心"}'
```

**成功响应示例**:

```json
{
  "data": {
    "tokens": ["今天", "天气", "很", "好", "，", "我", "很", "开心"],
    "text_length": 11,
    "token_count": 8
  },
  "timestamp": 1700000000
}
```

**响应字段说明**:

| 字段名       | 类型           | 描述             |
| ------------ | -------------- | ---------------- |
| tokens       | array[string]  | 分词结果数组     |
| text_length  | integer        | 原始文本长度     |
| token_count  | integer        | 分词数量         |

### 5. 批量文本分词

对多个中文文本进行批量分词处理。

**请求方式**: `POST`

**请求路径**: `/segment/batch`

**请求头**: 
- `Content-Type: application/json`

**请求参数**:

````json
{
  "texts": ["文本1", "文本2", "..."]
}
```

**请求示例**:

```bash
curl -X POST http://localhost:5000/segment/batch \
  -H "Content-Type: application/json" \
  -d '{"texts": ["今天天气很好", "我很不开心"]}'
```

**成功响应示例**:

```json
{
  "data": [
    {
      "tokens": ["今天", "天气", "很", "好"],
      "text_length": 6,
      "token_count": 4
    },
    {
      "tokens": ["我", "很", "不", "开心"],
      "text_length": 5,
      "token_count": 4
    }
  ],
  "timestamp": 1700000000
}
```

**响应字段说明**:

| 字段名       | 类型           | 描述             |
| ------------ | -------------- | ---------------- |
| tokens       | array[string]  | 分词结果数组     |
| text_length  | integer        | 原始文本长度     |
| token_count  | integer        | 分词数量         |

### 6. 长文本情感分析

对超过512字符的长文本进行情感分析，系统会自动将文本分块处理后再合并结果。

**请求方式**: `POST`

**请求路径**: `/analyze/long`

**请求头**: 
- `Content-Type: application/json`

**请求参数**:

````json
{
  "text": "待分析的长中文文本（可超过512字符）",
  "chunk_size": 512  // 可选，分块大小，默认512
}
```

**请求示例**:

```bash
curl -X POST http://localhost:5000/analyze/long \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_api_key_here" \
  -d '{"text": "这是一个超过512字符的长文本..."}'
```

**成功响应示例**:

```json
{
  "data": {
    "emotion_score": 0.9876,
    "emotion": "正面",
    "confidence": 0.9752,
    "text_length": 1024,
    "chunk_size": 512
  },
  "timestamp": 1700000000
}
```

**响应字段说明**:

| 字段名        | 类型    | 描述                           |
| ------------- | ------- | ------------------------------ |
| emotion_score | float   | 情感得分，范围[0,1]            |
| emotion       | string  | 情感极性，"正面"或"负面"       |
| confidence    | float   | 置信度，越接近1表示越确定      |
| text_length   | integer | 原始文本长度                   |
| chunk_size    | integer | 分块大小                       |

### 7. 长文本分词

对超过2048字符的长文本进行分词处理，系统会自动将文本分块处理后再合并结果。

**请求方式**: `POST`

**请求路径**: `/segment/long`

**请求头**: 
- `Content-Type: application/json`

**请求参数**:

````json
{
  "text": "待分词的长中文文本（可超过2048字符）",
  "chunk_size": 512  // 可选，分块大小，默认512
}
```

**请求示例**:

```bash
curl -X POST http://localhost:5000/segment/long \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_api_key_here" \
  -d '{"text": "这是一个超过2048字符的长文本..."}'
```

**成功响应示例**:

```json
{
  "data": {
    "segments": ["这是", "一个", "超过", "..."],
    "text_length": 2500,
    "segment_count": 320,
    "chunk_size": 512
  },
  "timestamp": 1700000000
}
```

**响应字段说明**:

| 字段名       | 类型           | 描述             |
| ------------ | -------------- | ---------------- |
| segments     | array[string]  | 分词结果数组     |
| text_length  | integer        | 原始文本长度     |
| segment_count| integer        | 分词数量         |
| chunk_size   | integer        | 分块大小         |

## 限制与注意事项

1. **文本长度限制**: 
   - 普通分词接口(/segment)：单条文本长度不能超过2048个字符，超过部分会被截断
   - 长文本分词接口(/segment/long)：单条文本长度理论上无限制，但建议不超过10000字符
   - 模型限制：底层分词模型最大序列长度为512字符，系统会自动处理超长文本
2. **批量处理限制**: 单次批量处理建议不超过100条文本
3. **首次请求延迟**: 服务启动后首次加载模型需要时间，属于正常现象
4. **缓存机制**: 服务内置LRU缓存，重复请求可获得更快响应
5. **编码问题**: 确保客户端正确处理UTF-8编码的JSON响应

## 性能优化建议

1. **批量处理**: 对于多个文本，使用批量接口比逐个调用单文本接口更高效
2. **缓存利用**: 重复分析相同文本会直接返回缓存结果，提高响应速度
3. **连接复用**: 在可能的情况下，复用HTTP连接以减少连接开销

## 故障排除

### 常见问题

1. **中文显示为Unicode编码**
   - 确保客户端正确处理UTF-8编码的JSON响应
   - 检查HTTP响应头中的Content-Type是否包含charset=utf-8

2. **首次请求响应较慢**
   - 服务启动后首次加载模型需要时间，这是正常现象
   - 可通过预热接口减少首次请求延迟

3. **请求返回500错误**
   - 检查文本是否为空或格式不正确
   - 查看服务日志获取详细错误信息

### 日志查看

````bash
# Docker方式查看日志
docker-compose logs

# 直接运行方式查看日志
tail -f app.log
```
