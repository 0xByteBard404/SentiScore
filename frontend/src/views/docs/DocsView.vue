<template>
  <div class="docs-view">
    <div class="page-header">
      <h1 class="page-title">开发文档</h1>
      <p class="page-subtitle">SentiScore 情感分析 API 接口文档</p>
    </div>
    
    <div class="content-section">
      <el-card class="doc-card">
        <template #header>
          <div class="card-header">
            <h2>API接口文档</h2>
          </div>
        </template>
        
        <div class="doc-content">
          <h3>基础说明</h3>
          <p>SentiScore 情感分析 API 提供中文文本情感分析服务，支持单文本和批量分析。</p>
          
          <h4>认证方式</h4>
          <p>所有 API 请求都需要通过 API Key 进行认证。您可以在"密钥管理"页面创建和管理您的 API 密钥。</p>
          <p>在请求头中添加 <code>X-API-Key</code> 字段：</p>
          <pre class="code-block"><code>X-API-Key: your_api_key_here</code></pre>
          
          <h4>响应格式</h4>
          <p>所有 API 响应都采用统一的 JSON 格式：</p>
          <pre class="code-block"><code>{
  "code": 200,
  "message": "success",
  "data": { /* 具体数据 */ }
}</code></pre>
          
          <h3>单文本情感分析</h3>
          <p><strong>POST /analyze</strong></p>
          <p>对单个中文文本进行情感分析</p>
          
          <h4>请求参数</h4>
          <el-table :data="singleTextParams" border style="width: 100%" class="doc-table">
            <el-table-column prop="name" label="参数名" width="120" />
            <el-table-column prop="type" label="类型" width="100" />
            <el-table-column prop="required" label="必填" width="80">
              <template #default="scope">
                <el-tag :type="scope.row.required ? 'success' : 'info'">
                  {{ scope.row.required ? '是' : '否' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="description" label="说明" />
          </el-table>
          
          <h4>请求示例</h4>
          <pre class="code-block"><code>curl -X POST http://localhost:5000/analyze \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_api_key_here" \
  -d '{"text": "这个产品非常好用，我很喜欢！"}'</code></pre>
          
          <h4>响应示例</h4>
          <pre class="code-block"><code>{
  "code": 200,
  "message": "success",
  "data": {
    "emotion_score": 0.923456,
    "emotion": "正面",
    "confidence": 0.9235,
    "text_length": 15
  }
}</code></pre>
          
          <h3>批量情感分析</h3>
          <p><strong>POST /batch</strong></p>
          <p>对多个中文文本进行批量情感分析</p>
          
          <h4>请求参数</h4>
          <el-table :data="batchParams" border style="width: 100%" class="doc-table">
            <el-table-column prop="name" label="参数名" width="120" />
            <el-table-column prop="type" label="类型" width="100" />
            <el-table-column prop="required" label="必填" width="80">
              <template #default="scope">
                <el-tag :type="scope.row.required ? 'success' : 'info'">
                  {{ scope.row.required ? '是' : '否' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="description" label="说明" />
          </el-table>
          
          <h4>请求示例</h4>
          <pre class="code-block"><code>curl -X POST http://localhost:5000/batch \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_api_key_here" \
  -d '{"texts": ["这个产品非常好用", "服务态度有待改善", "一般般吧"]}'</code></pre>
          
          <h4>响应示例</h4>
          <pre class="code-block"><code>{
  "code": 200,
  "message": "success",
  "data": {
    "results": [
      {
        "text": "这个产品非常好用",
        "emotion_score": 0.876543,
        "emotion": "正面",
        "confidence": 0.8765,
        "text_length": 8
      },
      {
        "text": "服务态度有待改善",
        "emotion_score": 0.234567,
        "emotion": "负面",
        "confidence": 0.7654,
        "text_length": 8
      },
      {
        "text": "一般般吧",
        "emotion_score": 0.543210,
        "emotion": "中性",
        "confidence": 0.9136,
        "text_length": 4
      }
    ],
    "total_count": 3
  }
}</code></pre>
          
          <h3>单文本分词</h3>
          <p><strong>POST /segment</strong></p>
          <p>对单个中文文本进行分词处理</p>
          
          <h4>请求参数</h4>
          <el-table :data="singleSegmentParams" border style="width: 100%" class="doc-table">
            <el-table-column prop="name" label="参数名" width="120" />
            <el-table-column prop="type" label="类型" width="100" />
            <el-table-column prop="required" label="必填" width="80">
              <template #default="scope">
                <el-tag :type="scope.row.required ? 'success' : 'info'">
                  {{ scope.row.required ? '是' : '否' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="description" label="说明" />
          </el-table>
          
          <h4>请求示例</h4>
          <pre class="code-block"><code>curl -X POST http://localhost:5000/segment \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_api_key_here" \
  -d '{"text": "我爱自然语言处理技术"}'</code></pre>
          
          <h4>响应示例</h4>
          <pre class="code-block"><code>{
  "code": 200,
  "message": "success",
  "data": {
    "segments": ["我", "爱", "自然语言", "处理", "技术"],
    "segment_count": 5,
    "text_length": 9
  }
}</code></pre>
          
          <h3>批量文本分词</h3>
          <p><strong>POST /segment/batch</strong></p>
          <p>对多个中文文本进行批量分词处理</p>
          
          <h4>请求参数</h4>
          <el-table :data="batchSegmentParams" border style="width: 100%" class="doc-table">
            <el-table-column prop="name" label="参数名" width="120" />
            <el-table-column prop="type" label="类型" width="100" />
            <el-table-column prop="required" label="必填" width="80">
              <template #default="scope">
                <el-tag :type="scope.row.required ? 'success' : 'info'">
                  {{ scope.row.required ? '是' : '否' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="description" label="说明" />
          </el-table>
          
          <h4>请求示例</h4>
          <pre class="code-block"><code>curl -X POST http://localhost:5000/segment/batch \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_api_key_here" \
  -d '{"texts": ["我爱自然语言处理", "今天天气真好", "编程很有趣"]}'</code></pre>
          
          <h4>响应示例</h4>
          <pre class="code-block"><code>{
  "code": 200,
  "message": "success",
  "data": {
    "results": [
      {
        "text": "我爱自然语言处理",
        "segments": ["我", "爱", "自然语言", "处理"],
        "segment_count": 4
      },
      {
        "text": "今天天气真好",
        "segments": ["今天", "天气", "真好"],
        "segment_count": 3
      },
      {
        "text": "编程很有趣",
        "segments": ["编程", "很", "有趣"],
        "segment_count": 3
      }
    ],
    "total_count": 3
  }
}</code></pre>
          
          <h3>响应字段说明</h3>
          <el-table :data="responseFields" border style="width: 100%" class="doc-table">
            <el-table-column prop="field" label="字段名" width="150" />
            <el-table-column prop="description" label="说明" />
            <el-table-column prop="range" label="取值范围" width="200" />
          </el-table>
          
          <h3>错误码说明</h3>
          <el-table :data="errorCodes" border style="width: 100%" class="doc-table">
            <el-table-column prop="code" label="错误码" width="100" />
            <el-table-column prop="message" label="错误信息" />
            <el-table-column prop="description" label="说明" />
          </el-table>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const singleTextParams = ref([
  { name: 'text', type: 'string', required: true, description: '需要分析的中文文本' }
])

const batchParams = ref([
  { name: 'texts', type: 'array', required: true, description: '需要分析的中文文本数组' }
])

const singleSegmentParams = ref([
  { name: 'text', type: 'string', required: true, description: '需要分词的中文文本' }
])

const batchSegmentParams = ref([
  { name: 'texts', type: 'array', required: true, description: '需要分词的中文文本数组' }
])

const responseFields = ref([
  { field: 'emotion_score', description: '情感分数，越接近1表示越正面，越接近0表示越负面', range: '0-1' },
  { field: 'emotion', description: '情感分类结果', range: '正面/负面/中性' },
  { field: 'confidence', description: '置信度', range: '0-1' },
  { field: 'text_length', description: '文本长度', range: '整数' },
  { field: 'segments', description: '分词结果数组', range: '字符串数组' },
  { field: 'segment_count', description: '分词数量', range: '整数' }
])

const errorCodes = ref([
  { code: 400, message: '请求参数错误', description: '请求参数不符合要求' },
  { code: 401, message: '认证失败', description: 'API Key无效或缺失' },
  { code: 403, message: '配额不足', description: '账户配额已用完' },
  { code: 422, message: '文本分析失败', description: '输入文本无法分析' },
  { code: 500, message: '服务器内部错误', description: '服务暂时异常' }
])
</script>

<style scoped>
.docs-view {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.page-header {
  margin-bottom: 30px;
  text-align: center;
}

.page-title {
  font-size: 2rem;
  font-weight: 700;
  margin: 0 0 10px 0;
  color: #fff;
  background: linear-gradient(90deg, #409eff, #67c23a);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.page-subtitle {
  font-size: 1.1rem;
  color: #a0c3ff;
  margin: 0;
  text-align: center;
}

.content-section {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 15px;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  padding: 20px;
  transition: all 0.3s ease;
}

.content-section:hover {
  transform: translateY(-3px);
  box-shadow: 0 15px 35px rgba(0, 0, 0, 0.2);
  border-color: rgba(64, 158, 255, 0.3);
}

.doc-card {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 15px;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  transition: all 0.3s ease;
}

.doc-card:hover {
  border-color: rgba(64, 158, 255, 0.3);
}

.card-header {
  padding: 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.card-header h2 {
  font-size: 1.5rem;
  font-weight: 600;
  margin: 0;
  color: #fff;
}

.doc-content h3 {
  margin-top: 30px;
  margin-bottom: 15px;
  padding-bottom: 10px;
  color: #fff;
  font-size: 1.3rem;
  font-weight: 600;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.doc-content h4 {
  margin-top: 20px;
  margin-bottom: 10px;
  color: #a0c3ff;
  font-size: 1.1rem;
  font-weight: 500;
}

.doc-content p {
  line-height: 1.6;
  margin-bottom: 10px;
  color: #c0d9ff;
}

.code-block {
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  padding: 15px;
  color: #a0c3ff;
  font-family: 'Courier New', monospace;
  font-size: 14px;
  overflow-x: auto;
  margin: 15px 0;
}

.doc-table {
  background: transparent;
  margin: 15px 0;
}

.doc-table :deep(.el-table__header th) {
  background: rgba(255, 255, 255, 0.05);
  color: #a0c3ff;
}

.doc-table :deep(.el-table__row) {
  background: rgba(255, 255, 255, 0.03);
}

.doc-table :deep(.el-table__row:hover) {
  background: rgba(64, 158, 255, 0.1);
}

.doc-table :deep(.el-table__cell) {
  color: #c0d9ff;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .docs-view {
    padding: 15px;
  }
  
  .doc-content h3 {
    font-size: 1.2rem;
  }
  
  .doc-content h4 {
    font-size: 1rem;
  }
}
</style>