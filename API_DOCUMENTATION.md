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

```json
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

``json
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

```json
{
  "text": "待分析的中文文本"
}
```

**请求示例**:

```bash
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

```json
{
  "texts": ["文本1", "文本2", "..."]
}
```

**请求示例**:

```bash
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

```json
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

```json
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

## 使用示例

### Python 示例

```
import requests
import json

# 单文本分析
def analyze_single_text(text):
    response = requests.post(
        'http://localhost:5000/analyze',
        headers={'Content-Type': 'application/json'},
        data=json.dumps({'text': text})
    )
    
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"请求失败: {response.status_code}")

# 批量分析
def analyze_batch_texts(texts):
    response = requests.post(
        'http://localhost:5000/batch',
        headers={'Content-Type': 'application/json'},
        data=json.dumps({'texts': texts})
    )
    
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"请求失败: {response.status_code}")

# 单文本分词
def segment_single_text(text):
    response = requests.post(
        'http://localhost:5000/segment',
        headers={'Content-Type': 'application/json'},
        data=json.dumps({'text': text})
    )
    
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"请求失败: {response.status_code}")

# 批量分词
def segment_batch_texts(texts):
    response = requests.post(
        'http://localhost:5000/segment/batch',
        headers={'Content-Type': 'application/json'},
        data=json.dumps({'texts': texts})
    )
    
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"请求失败: {response.status_code}")

# 使用示例
try:
    # 单文本分析
    result = analyze_single_text("今天天气很好，我很开心")
    print(f"情感: {result['data']['emotion']}")
    print(f"得分: {result['data']['emotion_score']}")
    
    # 批量分析
    texts = ["今天天气很好", "我很开心", "但也有点累"]
    result = analyze_batch_texts(texts)
    for i, item in enumerate(result['data']):
        print(f"文本: {texts[i]}")
        print(f"  情感: {item['emotion']}")
        print(f"  得分: {item['emotion_score']}")
        
    # 单文本分词
    result = segment_single_text("今天天气很好，我很开心")
    print(f"分词结果: {' '.join(result['data']['segments'])}")
    
    # 批量分词
    result = segment_batch_texts(["今天天气很好", "我很开心"])
    for i, item in enumerate(result['data']):
        print(f"文本 {i+1} 分词结果: {' '.join(item['segments'])}")
except Exception as e:
    print(f"错误: {e}")
```

### JavaScript 示例

```
// 单文本分析
async function analyzeSingleText(text) {
    const response = await fetch('http://localhost:5000/analyze', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({text: text})
    });
    
    if (response.ok) {
        return await response.json();
    } else {
        throw new Error(`请求失败: ${response.status}`);
    }
}

// 批量分析
async function analyzeBatchTexts(texts) {
    const response = await fetch('http://localhost:5000/batch', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({texts: texts})
    });
    
    if (response.ok) {
        return await response.json();
    } else {
        throw new Error(`请求失败: ${response.status}`);
    }
}

// 单文本分词
async function segmentSingleText(text) {
    const response = await fetch('http://localhost:5000/segment', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({text: text})
    });
    
    if (response.ok) {
        return await response.json();
    } else {
        throw new Error(`请求失败: ${response.status}`);
    }
}

// 批量分词
async function segmentBatchTexts(texts) {
    const response = await fetch('http://localhost:5000/segment/batch', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({texts: texts})
    });
    
    if (response.ok) {
        return await response.json();
    } else {
        throw new Error(`请求失败: ${response.status}`);
    }
}

// 使用示例
(async () => {
    try {
        // 单文本分析
        const singleResult = await analyzeSingleText("今天天气很好，我很开心");
        console.log("情感:", singleResult.data.emotion);
        console.log("得分:", singleResult.data.emotion_score);
        
        // 批量分析
        const texts = ["今天天气很好", "我很开心", "但也有点累"];
        const batchResult = await analyzeBatchTexts(texts);
        batchResult.data.forEach((item, index) => {
            console.log(`文本: ${texts[index]}`);
            console.log(`  情感: ${item.emotion}`);
            console.log(`  得分: ${item.emotion_score}`);
        });
        
        // 单文本分词
        const segmentResult = await segmentSingleText("今天天气很好，我很开心");
        console.log("分词结果:", segmentResult.data.segments.join(' '));
        
        // 批量分词
        const segmentBatchResult = await segmentBatchTexts(["今天天气很好", "我很开心"]);
        segmentBatchResult.data.forEach((item, index) => {
            console.log(`文本 ${index+1} 分词结果:`, item.segments.join(' '));
        });
    } catch (error) {
        console.error("错误:", error);
    }
})();
```

## 限制与注意事项

1. **文本长度限制**: 建议单条文本不超过1000字符
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

```bash
# Docker方式查看日志
docker-compose logs

# 直接运行方式查看日志
tail -f app.log
```