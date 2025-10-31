<template>
  <div class="orders-container">
    <div class="page-header">
      <h1 class="page-title">订单管理</h1>
      <p class="page-subtitle">查看和管理您的订单记录</p>
    </div>
    
    <div class="content-section">
      <div class="filters-section">
        <div class="filter-group">
          <el-select v-model="orderStatus" placeholder="订单状态" clearable @change="loadOrders" class="filter-input">
            <el-option label="全部" value=""></el-option>
            <el-option label="待支付" value="pending"></el-option>
            <el-option label="已支付" value="paid"></el-option>
            <el-option label="已取消" value="cancelled"></el-option>
            <el-option label="已退款" value="refunded"></el-option>
          </el-select>
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            @change="loadOrders"
            class="filter-input"
          />
          <el-button type="primary" @click="loadOrders" class="search-btn">
            <el-icon><Search /></el-icon> 搜索
          </el-button>
        </div>
      </div>
      
      <el-card class="orders-card">
        <template #header>
          <div class="card-header">
            <h2>订单记录</h2>
          </div>
        </template>
        
        <el-table 
          :data="ordersData.orders" 
          style="width: 100%" 
          v-loading="loading"
          stripe
          class="orders-table"
        >
          <el-table-column prop="order_no" label="订单号" width="180"></el-table-column>
          <el-table-column prop="plan_name" label="套餐名称" width="120"></el-table-column>
          <el-table-column prop="amount" label="金额" width="100">
            <template #default="scope">
              ¥{{ scope.row.amount }}
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="100">
            <template #default="scope">
              <el-tag :type="getStatusTypeTag(scope.row.status)">
                {{ getStatusText(scope.row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="创建时间" width="200"></el-table-column>
          <el-table-column prop="paid_at" label="支付时间" width="200"></el-table-column>
          <el-table-column label="操作" width="150">
            <template #default="scope">
              <el-button type="primary" text @click="viewOrder(scope.row)" class="detail-btn">详情</el-button>
              <el-button 
                v-if="scope.row.status === 'pending'" 
                type="success" 
                text 
                @click="payOrder(scope.row)"
                class="action-btn"
              >
                支付
              </el-button>
              <el-button 
                v-if="scope.row.status === 'paid'" 
                type="warning" 
                text 
                @click="refundOrder(scope.row)"
                class="action-btn"
              >
                退款
              </el-button>
            </template>
          </el-table-column>
        </el-table>
        
        <div class="pagination-container">
          <el-pagination
            v-model:current-page="pagination.currentPage"
            v-model:page-size="pagination.pageSize"
            :page-sizes="[10, 20, 50, 100]"
            :total="ordersData.total"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="handleSizeChange"
            @current-change="handleCurrentChange"
            background
          />
        </div>
      </el-card>
    </div>
    
    <!-- 订单详情对话框 -->
    <el-dialog v-model="dialogVisible" title="订单详情" width="600px" class="detail-dialog">
      <el-form label-width="120px" class="detail-form">
        <el-form-item label="订单号:">
          <span>{{ orderDetail.order_no }}</span>
        </el-form-item>
        <el-form-item label="套餐名称:">
          <span>{{ orderDetail.plan_name }}</span>
        </el-form-item>
        <el-form-item label="金额:">
          <span>¥{{ orderDetail.amount }}</span>
        </el-form-item>
        <el-form-item label="状态:">
          <el-tag :type="getStatusTypeTag(orderDetail.status)">
            {{ getStatusText(orderDetail.status) }}
          </el-tag>
        </el-form-item>
        <el-form-item label="创建时间:">
          <span>{{ orderDetail.created_at }}</span>
        </el-form-item>
        <el-form-item label="支付时间:">
          <span>{{ orderDetail.paid_at || '未支付' }}</span>
        </el-form-item>
        <el-form-item label="退款时间:">
          <span>{{ orderDetail.refunded_at || '未退款' }}</span>
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
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import { getOrderHistory } from '@/api/user'
import type { OrderHistory } from '@/api/user'
import type { TagProps } from 'element-plus'

// 数据状态
const loading = ref(false)
const dialogVisible = ref(false)

// 搜索条件
const orderStatus = ref('')
const dateRange = ref<[string, string]>(['', ''])

// 订单数据
const ordersData = ref<OrderHistory>({
  total: 0,
  page: 1,
  limit: 20,
  total_pages: 0,
  orders: []
})

// 分页信息
const pagination = reactive({
  currentPage: 1,
  pageSize: 20,
  total: 0
})

// 订单详情
const orderDetail = ref({
  id: 0,
  order_no: '',
  user_id: 0,
  plan_id: 0,
  plan_name: '',
  amount: 0,
  status: '',
  created_at: '',
  paid_at: '',
  refunded_at: ''
})

// 加载订单数据
const loadOrders = async () => {
  loading.value = true
  try {
    const [startDate, endDate] = dateRange.value || ['', '']
    const data = await getOrderHistory(
      pagination.currentPage,
      pagination.pageSize,
      orderStatus.value,
      startDate,
      endDate
    )
    ordersData.value = data
    pagination.total = data.total
  } catch (error: any) {
    ElMessage.error(error.response?.data?.message || '加载订单数据失败')
  } finally {
    loading.value = false
  }
}

// 查看订单详情
const viewOrder = (row: any) => {
  orderDetail.value = { ...row }
  dialogVisible.value = true
}

// 支付订单
const payOrder = (row: any) => {
  ElMessageBox.confirm('确认要支付此订单吗？', '支付确认', {
    confirmButtonText: '确认',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(() => {
    // 这里应该调用后端API支付订单
    ElMessage.success('支付成功')
    loadOrders()
  }).catch(() => {
    // 用户取消操作
  })
}

// 退款订单
const refundOrder = (row: any) => {
  ElMessageBox.confirm('确认要申请退款吗？', '退款确认', {
    confirmButtonText: '确认',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(() => {
    // 这里应该调用后端API退款订单
    ElMessage.success('退款申请已提交')
    loadOrders()
  }).catch(() => {
    // 用户取消操作
  })
}

// 获取状态文本
const getStatusText = (status: string) => {
  const statusMap: Record<string, string> = {
    pending: '待支付',
    paid: '已支付',
    cancelled: '已取消',
    refunded: '已退款'
  }
  return statusMap[status] || status
}

// 获取状态标签类型
const getStatusTypeTag = (status: string): TagProps['type'] => {
  const typeMap: Record<string, TagProps['type']> = {
    pending: 'warning',
    paid: 'success',
    cancelled: 'info',
    refunded: 'danger'
  }
  return typeMap[status] || 'info'
}

// 分页处理
const handleSizeChange = (val: number) => {
  pagination.pageSize = val
  loadOrders()
}

const handleCurrentChange = (val: number) => {
  pagination.currentPage = val
  loadOrders()
}

onMounted(() => {
  loadOrders()
})
</script>

<style scoped>
.orders-container {
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

.filter-input :deep(.el-input__wrapper),
.filter-input :deep(.el-select__wrapper) {
  background: transparent;
  box-shadow: none;
}

.filter-input :deep(.el-input__inner),
.filter-input :deep(.el-select__placeholder) {
  background: transparent;
  color: #fff;
}

.filter-input :deep(.el-input__inner::placeholder),
.filter-input :deep(.el-select__placeholder) {
  color: #a0c3ff;
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

.orders-card {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 15px;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  transition: all 0.3s ease;
}

.orders-card:hover {
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

.orders-table {
  background: transparent;
}

.orders-table :deep(.el-table__header th) {
  background: rgba(255, 255, 255, 0.05);
  color: #a0c3ff;
}

.orders-table :deep(.el-table__row) {
  background: rgba(255, 255, 255, 0.03);
}

.orders-table :deep(.el-table__row:hover) {
  background: rgba(64, 158, 255, 0.1);
}

.detail-btn,
.action-btn {
  color: #409eff;
  font-weight: 500;
  margin-right: 10px;
}

.detail-btn:hover,
.action-btn:hover {
  color: #66b1ff;
}

.action-btn[type="success"] {
  color: #67c23a;
}

.action-btn[type="success"]:hover {
  color: #85ce61;
}

.action-btn[type="warning"] {
  color: #e6a23c;
}

.action-btn[type="warning"]:hover {
  color: #ebb563;
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
  
  .orders-container {
    padding: 15px;
  }
  
  .detail-btn,
  .action-btn {
    display: block;
    margin-bottom: 5px;
    margin-right: 0;
  }
}
</style>