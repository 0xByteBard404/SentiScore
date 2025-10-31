<template>
  <div class="history-container">
    <div class="page-header">
      <h1 class="page-title">API调用历史</h1>
      <p class="page-subtitle">查看和管理您的API调用记录</p>
    </div>
    
    <div class="content-section">
      <div class="filters-section">
        <div class="filter-group">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            @change="loadHistory"
            class="filter-input date-picker"
          />
          <el-input
            v-model="searchEndpoint"
            placeholder="搜索端点"
            class="filter-input search-input custom-search-input"
            @keyup.enter="loadHistory"
          />
          <el-button type="primary" @click="loadHistory" class="search-btn">
            <el-icon><Search /></el-icon> 搜索
          </el-button>
        </div>
      </div>
      
      <el-card class="history-card">
        <template #header>
          <div class="card-header">
            <h2>调用记录</h2>
          </div>
        </template>
        
        <el-table 
          :data="historyData.calls" 
          style="width: 100%" 
          v-loading="loading"
          stripe
          class="history-table custom-table"
        >
          <el-table-column prop="id" label="ID" width="80"></el-table-column>
          <el-table-column prop="endpoint" label="端点"></el-table-column>
          <el-table-column prop="method" label="方法" width="100"></el-table-column>
          <el-table-column prop="response_status" label="状态码" width="100">
            <template #default="scope">
              <el-tag :type="scope.row.response_status === 200 ? 'success' : 'danger'">
                {{ scope.row.response_status }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="response_time_ms" label="响应时间(ms)" width="150"></el-table-column>
          <el-table-column prop="created_at" label="调用时间" width="200"></el-table-column>
          <el-table-column label="操作" width="100">
            <template #default="scope">
              <el-button type="primary" text @click="viewDetails(scope.row)" class="detail-btn">详情</el-button>
            </template>
          </el-table-column>
        </el-table>
        
        <div class="pagination-container">
          <el-pagination
            v-model:current-page="pagination.currentPage"
            v-model:page-size="pagination.pageSize"
            :page-sizes="[10, 20, 50, 100]"
            :total="historyData.total"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="handleSizeChange"
            @current-change="handleCurrentChange"
            background
          />
        </div>
      </el-card>
    </div>
    
    <!-- 详情对话框 -->
    <el-dialog v-model="dialogVisible" title="调用详情" width="600px" class="detail-dialog">
      <el-form label-width="120px" class="detail-form">
        <el-form-item label="端点:">
          <span>{{ detailData.endpoint }}</span>
        </el-form-item>
        <el-form-item label="方法:">
          <span>{{ detailData.method }}</span>
        </el-form-item>
        <el-form-item label="状态码:">
          <el-tag :type="detailData.response_status === 200 ? 'success' : 'danger'">
            {{ detailData.response_status }}
          </el-tag>
        </el-form-item>
        <el-form-item label="响应时间:">
          <span>{{ detailData.response_time_ms }} ms</span>
        </el-form-item>
        <el-form-item label="调用时间:">
          <span>{{ detailData.created_at }}</span>
        </el-form-item>
        <el-form-item label="请求数据:">
          <pre class="json-display">{{ formatJson(detailData.request_data) }}</pre>
        </el-form-item>
        <el-form-item label="响应数据:">
          <pre class="json-display">{{ formatJson(detailData.response_data) }}</pre>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false" class="cancel-btn">关闭</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import { getApiCallHistory } from '@/api/user'
import type { ApiCallHistory } from '@/api/user'

// 数据状态
const loading = ref(false)
const dialogVisible = ref(false)

// 搜索条件
const dateRange = ref<[string, string]>(['', ''])
const searchEndpoint = ref('')

// 历史数据
const historyData = ref<ApiCallHistory>({
  total: 0,
  page: 1,
  limit: 20,
  total_pages: 0,
  calls: []
})

// 分页信息
const pagination = reactive({
  currentPage: 1,
  pageSize: 20,
  total: 0
})

// 详情数据
const detailData = ref({
  id: 0,
  endpoint: '',
  method: '',
  response_status: 200,
  response_time_ms: 0,
  created_at: '',
  request_data: {},
  response_data: {}
})

// 格式化JSON显示
const formatJson = (data: any) => {
  if (typeof data === 'object' && data !== null) {
    return JSON.stringify(data, null, 2)
  }
  return data
}

// 加载历史记录
const loadHistory = async () => {
  loading.value = true
  try {
    const [startDate, endDate] = dateRange.value || ['', '']
    const data = await getApiCallHistory(
      pagination.currentPage,
      pagination.pageSize,
      startDate,
      endDate,
      searchEndpoint.value
    )
    historyData.value = data
    pagination.total = data.total
  } catch (error: any) {
    ElMessage.error(error.response?.data?.message || '加载历史记录失败')
  } finally {
    loading.value = false
  }
}

// 查看详情
const viewDetails = (row: any) => {
  detailData.value = { ...row }
  dialogVisible.value = true
}

// 分页处理
const handleSizeChange = (val: number) => {
  pagination.pageSize = val
  loadHistory()
}

const handleCurrentChange = (val: number) => {
  pagination.currentPage = val
  loadHistory()
}

onMounted(() => {
  loadHistory()
})
</script>

<style scoped>
.history-container {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
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

.filters-section {
  margin-bottom: 20px;
}

.filter-group {
  display: flex;
  gap: 15px;
  flex-wrap: wrap;
  align-items: center;
}

.filter-input {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
}

/* 自定义搜索输入框样式 */
.custom-search-input :deep(.el-input__wrapper) {
  background: rgba(255, 255, 255, 0.05) !important;
  border: 1px solid rgba(255, 255, 255, 0.1) !important;
  border-radius: 8px !important;
  box-shadow: none !important;
}

.custom-search-input :deep(.el-input__wrapper:hover) {
  border-color: rgba(64, 158, 255, 0.5) !important;
}

.custom-search-input :deep(.el-input__wrapper.is-focus) {
  border-color: #409eff !important;
  box-shadow: 0 0 0 1px #409eff !important;
}

.custom-search-input :deep(.el-input__inner) {
  background: transparent !important;
  color: #fff !important;
  border: none !important;
}

.custom-search-input :deep(.el-input__inner::placeholder) {
  color: #a0c3ff !important;
}

.search-input {
  width: 250px;
}

.search-btn {
  background: linear-gradient(135deg, #409eff 0%, #1a73e8 100%);
  border: none;
  color: white;
  font-weight: 600;
  padding: 12px 24px;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.search-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 25px rgba(64, 158, 255, 0.3);
}

.history-card {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 15px;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  transition: all 0.3s ease;
}

.history-card:hover {
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

/* 自定义表格样式 - 重点修复表头背景色 */
.custom-table :deep(.el-table) {
  background: transparent !important;
  color: #fff !important;
}

.custom-table :deep(.el-table__header-wrapper) {
  background: transparent !important;
}

.custom-table :deep(.el-table__header) {
  background: transparent !important;
}

.custom-table :deep(.el-table__header th) {
  background: rgba(29, 43, 79, 0.8) !important; /* 深蓝色背景 */
  color: #a0c3ff !important;
  font-weight: 600 !important;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1) !important;
}

.custom-table :deep(.el-table__header th .cell) {
  color: #a0c3ff !important;
  background: transparent !important;
}

.custom-table :deep(.el-table__header th:hover) {
  background: rgba(29, 43, 79, 1) !important; /* 悬停时加深背景 */
}

/* 表格主体样式 */
.custom-table :deep(.el-table__body-wrapper) {
  background: transparent !important;
}

.custom-table :deep(.el-table__body) {
  background: transparent !important;
}

.custom-table :deep(.el-table__row) {
  background: rgba(255, 255, 255, 0.03) !important;
  color: #fff !important;
}

.custom-table :deep(.el-table__row--striped) {
  background: rgba(255, 255, 255, 0.05) !important;
}

.custom-table :deep(.el-table__row--striped td) {
  background: rgba(255, 255, 255, 0.05) !important;
  color: #fff !important;
}

.custom-table :deep(.el-table__row:hover) {
  background: rgba(64, 158, 255, 0.1) !important;
}

.custom-table :deep(.el-table__row:hover td) {
  background: rgba(64, 158, 255, 0.1) !important;
}

.custom-table :deep(.el-table__body td) {
  color: #fff !important;
  background: transparent !important;
  border: none !important;
}

.custom-table :deep(.el-table__body tr) {
  background: transparent !important;
}

.detail-btn {
  color: #409eff;
  font-weight: 500;
}

.detail-btn:hover {
  color: #66b1ff;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}

.pagination-container :deep(.el-pagination) {
  background: rgba(255, 255, 255, 0.05);
  padding: 15px;
  border-radius: 8px;
}

.pagination-container :deep(.el-pagination .el-pager li) {
  background: rgba(255, 255, 255, 0.05);
  color: #a0c3ff;
}

.pagination-container :deep(.el-pagination .el-pager li:hover) {
  color: #409eff;
}

.pagination-container :deep(.el-pagination .el-pager li.is-active) {
  background: #409eff;
  color: white;
}

.detail-dialog :deep(.el-dialog) {
  background: rgba(15, 26, 48, 0.9);
  border-radius: 15px;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(64, 158, 255, 0.3);
}

.detail-dialog :deep(.el-dialog__header) {
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  padding: 20px;
}

.detail-dialog :deep(.el-dialog__title) {
  color: #fff;
  font-weight: 600;
}

.detail-dialog :deep(.el-dialog__body) {
  padding: 20px;
}

.detail-form :deep(.el-form-item__label) {
  color: #a0c3ff;
  font-weight: 500;
}

.detail-form :deep(.el-form-item__content) {
  color: #fff;
}

.json-display {
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  padding: 15px;
  color: #a0c3ff;
  font-family: 'Courier New', monospace;
  font-size: 14px;
  max-height: 200px;
  overflow: auto;
  white-space: pre-wrap;
}

.cancel-btn {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: #a0c3ff;
  font-weight: 500;
  padding: 12px 24px;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.cancel-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(64, 158, 255, 0.3);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .filter-group {
    flex-direction: column;
    align-items: stretch;
  }
  
  .search-input {
    width: 100%;
  }
  
  .history-container {
    padding: 15px;
  }
}
</style>