<template>
  <div class="keys-manager-view">
    <div class="page-header">
      <h1 class="page-title">API密钥管理</h1>
      <p class="page-subtitle">管理您的API密钥，控制访问权限和配额</p>
    </div>
    
    <div class="content-section">
      <div class="header-actions">
        <el-button type="primary" @click="showCreateDialog = true" size="large" class="create-btn">
          <el-icon><Plus /></el-icon> 创建新密钥
        </el-button>
        <el-button @click="loadApiKeys" class="refresh-btn">
          <el-icon><Refresh /></el-icon> 刷新
        </el-button>
      </div>
      
      <el-card class="keys-card">
        <template #header>
          <div class="card-header">
            <h2>所有API密钥</h2>
          </div>
        </template>
        
        <el-table 
          :data="apiKeys" 
          style="width: 100%" 
          v-loading="loading" 
          stripe
          class="keys-table"
        >
          <el-table-column prop="name" label="密钥名称" width="180">
            <template #default="scope">
              <div class="key-name-cell">
                <strong>{{ scope.row.name }}</strong>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="permissions" label="权限" width="150">
            <template #default="scope">
              <el-tag v-for="perm in scope.row.permissions.split(',')" :key="perm" class="permission-tag">
                {{ perm }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="is_active" label="状态" width="120">
            <template #default="scope">
              <el-tag :type="scope.row.is_active ? 'success' : 'danger'" size="small">
                {{ scope.row.is_active ? '启用' : '禁用' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="配额使用情况" width="220">
            <template #default="scope">
              <div class="quota-info">
                <div class="quota-numbers">
                  <span class="used">{{ scope.row.quota_used }}</span>
                  <span class="separator">/</span>
                  <span class="total">{{ scope.row.quota_total }}</span>
                </div>
                <el-progress 
                  :percentage="Math.round((scope.row.quota_used / scope.row.quota_total) * 100)" 
                  :stroke-width="8" 
                  :color="getQuotaColor(scope.row.quota_used, scope.row.quota_total)"
                  class="quota-progress"
                />
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="创建时间" width="180">
            <template #default="scope">
              {{ formatDate(scope.row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column prop="last_used_at" label="最后使用" width="180">
            <template #default="scope">
              {{ scope.row.last_used_at ? formatDate(scope.row.last_used_at) : '从未使用' }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="220" fixed="right">
            <template #default="scope">
              <div class="action-buttons">
                <el-button size="small" @click="viewKey(scope.row)" type="primary" plain>
                  查看
                </el-button>
                <el-button size="small" @click="editKey(scope.row)" type="warning" plain>
                  编辑
                </el-button>
                <el-button 
                  size="small" 
                  :type="scope.row.is_active ? 'danger' : 'success'" 
                  plain
                  @click="toggleKeyStatus(scope.row)"
                >
                  {{ scope.row.is_active ? '禁用' : '启用' }}
                </el-button>
              </div>
            </template>
          </el-table-column>
        </el-table>
        
        <div class="empty-state" v-if="!loading && apiKeys.length === 0">
          <el-icon size="48" class="empty-icon"><Key /></el-icon>
          <p>暂无API密钥</p>
          <el-button type="primary" @click="showCreateDialog = true">创建您的第一个密钥</el-button>
        </div>
      </el-card>
    </div>

    <!-- 创建API密钥对话框 -->
    <el-dialog v-model="showCreateDialog" title="创建新API密钥" width="500px" class="key-dialog custom-dialog custom-create-dialog">
      <el-form :model="newKeyForm" :rules="createRules" ref="createFormRef" label-width="100px">
        <el-form-item label="密钥名称" prop="name">
          <el-input v-model="newKeyForm.name" placeholder="请输入密钥名称" class="dialog-input" />
        </el-form-item>
        <el-form-item label="权限" prop="permissions">
          <el-checkbox-group v-model="newKeyForm.permissions">
            <el-checkbox label="read">读取</el-checkbox>
            <el-checkbox label="write">写入</el-checkbox>
          </el-checkbox-group>
        </el-form-item>
        <el-form-item label="配额总额" prop="quota_total">
          <el-input-number 
            v-model="newKeyForm.quota_total" 
            :min="1" 
            :max="10000000000" 
            controls-position="right" 
            style="width: 100%" 
            class="dialog-input"
          />
          <div class="quota-hint">设置此密钥的调用配额上限</div>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showCreateDialog = false" class="cancel-btn">取消</el-button>
          <el-button type="primary" @click="createKey" :loading="creating" class="confirm-btn">创建</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 编辑API密钥对话框 -->
    <el-dialog v-model="showEditDialog" title="编辑API密钥" width="500px" class="key-dialog custom-dialog custom-edit-dialog">
      <el-form :model="editKeyForm" :rules="editRules" ref="editFormRef" label-width="100px">
        <el-form-item label="密钥名称" prop="name">
          <el-input v-model="editKeyForm.name" placeholder="请输入密钥名称" class="dialog-input" />
        </el-form-item>
        <el-form-item label="权限" prop="permissions">
          <el-checkbox-group v-model="editKeyForm.permissions">
            <el-checkbox label="read">读取</el-checkbox>
            <el-checkbox label="write">写入</el-checkbox>
          </el-checkbox-group>
        </el-form-item>
        <el-form-item label="状态" prop="is_active">
          <el-switch 
            v-model="editKeyForm.is_active" 
            active-text="启用" 
            inactive-text="禁用" 
            :active-value="true"
            :inactive-value="false"
          />
        </el-form-item>
        <el-form-item label="配额总额" prop="quota_total">
          <el-input-number 
            v-model="editKeyForm.quota_total" 
            :min="1" 
            :max="10000000000" 
            controls-position="right" 
            style="width: 100%" 
            class="dialog-input"
          />
          <div class="quota-hint">设置此密钥的调用配额上限</div>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showEditDialog = false" class="cancel-btn">取消</el-button>
          <el-button type="primary" @click="updateKey" :loading="updating" class="confirm-btn">保存</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 查看API密钥对话框 -->
    <el-dialog v-model="showViewDialog" title="查看API密钥" width="600px" class="key-dialog custom-dialog custom-view-dialog">
      <div class="view-key-display" v-if="currentKey">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="密钥名称">{{ currentKey.name }}</el-descriptions-item>
          <el-descriptions-item label="权限">
            <el-tag v-for="perm in currentKey.permissions.split(',')" :key="perm" class="permission-tag">
              {{ perm }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="currentKey.is_active ? 'success' : 'danger'">
              {{ currentKey.is_active ? '启用' : '禁用' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="配额使用情况">
            <div class="quota-details">
              <div class="quota-numbers">
                <span class="used">{{ currentKey.quota_used }}</span>
                <span class="separator">/</span>
                <span class="total">{{ currentKey.quota_total }}</span>
              </div>
              <el-progress 
                :percentage="Math.round((currentKey.quota_used / currentKey.quota_total) * 100)" 
                :stroke-width="10" 
                :color="getQuotaColor(currentKey.quota_used, currentKey.quota_total)"
                class="quota-progress"
              />
            </div>
          </el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ formatDate(currentKey.created_at) }}</el-descriptions-item>
          <el-descriptions-item label="最后使用">
            {{ currentKey.last_used_at ? formatDate(currentKey.last_used_at) : '从未使用' }}
          </el-descriptions-item>
          <el-descriptions-item label="API密钥">
            <div class="key-display">
              <el-input v-model="currentKey.key" readonly class="dialog-input" />
              <el-button type="primary" @click="copyKeyToClipboard(currentKey.key)" :icon="CopyDocument">复制</el-button>
            </div>
          </el-descriptions-item>
        </el-descriptions>
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button type="primary" @click="showViewDialog = false" class="confirm-btn">关闭</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 新创建的密钥显示对话框 -->
    <el-dialog v-model="showNewKeyDialog" title="API密钥已创建" width="500px" class="key-dialog custom-dialog custom-new-key-dialog">
      <div class="new-key-display">
        <div class="success-icon">
          <el-icon size="48" color="#67c23a"><SuccessFilled /></el-icon>
        </div>
        <p class="success-message">请妥善保管您的新API密钥，一旦关闭此对话框将无法再次查看。</p>
        <el-input v-model="newlyCreatedKey" readonly class="dialog-input" />
        <el-button type="primary" @click="copyNewKeyToClipboard" :icon="CopyDocument">复制到剪贴板</el-button>
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button type="primary" @click="showNewKeyDialog = false" class="confirm-btn">确定</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { 
  CopyDocument, 
  Plus, 
  Refresh, 
  Key, 
  SuccessFilled 
} from '@element-plus/icons-vue'
import { formatDate } from '@/utils/date'
import { getApiKeys, createApiKey, updateApiKey, getApiKey } from '@/api/auth'

interface APIKey {
  id: number
  name: string
  key: string
  permissions: string
  is_active: boolean
  quota_total: number
  quota_used: number
  created_at: string
  last_used_at: string | null
}

const apiKeys = ref<APIKey[]>([])
const loading = ref(false)
const creating = ref(false)
const updating = ref(false)
const showCreateDialog = ref(false)
const showEditDialog = ref(false)
const showViewDialog = ref(false)
const showNewKeyDialog = ref(false)
const newlyCreatedKey = ref('')
const currentKey = ref<APIKey | null>(null)

const createFormRef = ref<FormInstance>()
const editFormRef = ref<FormInstance>()

const newKeyForm = reactive({
  name: '',
  permissions: ['read', 'write'],
  quota_total: 1000
})

const editKeyForm = reactive({
  id: 0,
  name: '',
  permissions: ['read', 'write'],
  is_active: true,
  quota_total: 1000
})

const createRules = reactive<FormRules>({
  name: [
    { required: true, message: '请输入密钥名称', trigger: 'blur' },
    { min: 1, max: 100, message: '长度应在1到100个字符之间', trigger: 'blur' }
  ]
})

const editRules = reactive<FormRules>({
  name: [
    { required: true, message: '请输入密钥名称', trigger: 'blur' },
    { min: 1, max: 100, message: '长度应在1到100个字符之间', trigger: 'blur' }
  ]
})

// 获取配额颜色
const getQuotaColor = (used: number, total: number) => {
  const percentage = (used / total) * 100
  if (percentage < 50) return '#67c23a'
  if (percentage < 80) return '#e6a23c'
  return '#f56c6c'
}

// 加载API密钥列表
const loadApiKeys = async () => {
  loading.value = true
  try {
    const response = await getApiKeys()
    apiKeys.value = response.data || []
  } catch (error) {
    ElMessage.error('获取API密钥列表失败')
    console.error('获取API密钥列表失败:', error)
  } finally {
    loading.value = false
  }
}

// 创建API密钥
const createKey = async () => {
  if (!createFormRef.value) return
  
  await createFormRef.value.validate(async (valid) => {
    if (!valid) return
    
    creating.value = true
    try {
      const response = await createApiKey({
        name: newKeyForm.name,
        permissions: newKeyForm.permissions.join(','),
        quota_total: newKeyForm.quota_total
      })
      
      newlyCreatedKey.value = response.data.key
      showCreateDialog.value = false
      showNewKeyDialog.value = true
      
      // 重置表单
      newKeyForm.name = ''
      newKeyForm.permissions = ['read', 'write']
      newKeyForm.quota_total = 1000
      
      // 重新加载密钥列表
      await loadApiKeys()
      
      ElMessage.success('API密钥创建成功')
    } catch (error) {
      ElMessage.error('创建API密钥失败')
      console.error('创建API密钥失败:', error)
    } finally {
      creating.value = false
    }
  })
}

// 查看API密钥
const viewKey = async (key: APIKey) => {
  try {
    const response = await getApiKey(key.id)
    currentKey.value = response
    showViewDialog.value = true
  } catch (error) {
    ElMessage.error('获取API密钥详情失败')
    console.error('获取API密钥详情失败:', error)
  }
}

// 编辑API密钥
const editKey = (key: APIKey) => {
  editKeyForm.id = key.id
  editKeyForm.name = key.name
  editKeyForm.permissions = key.permissions.split(',')
  editKeyForm.is_active = key.is_active
  editKeyForm.quota_total = key.quota_total
  showEditDialog.value = true
}

// 更新API密钥
const updateKey = async () => {
  if (!editFormRef.value) return
  
  await editFormRef.value.validate(async (valid) => {
    if (!valid) return
    
    updating.value = true
    try {
      await updateApiKey(editKeyForm.id, {
        name: editKeyForm.name,
        permissions: editKeyForm.permissions.join(','),
        is_active: editKeyForm.is_active,
        quota_total: editKeyForm.quota_total
      })
      
      showEditDialog.value = false
      await loadApiKeys()
      ElMessage.success('API密钥更新成功')
    } catch (error) {
      ElMessage.error('更新API密钥失败')
      console.error('更新API密钥失败:', error)
    } finally {
      updating.value = false
    }
  })
}

// 切换API密钥状态（启用/禁用）
const toggleKeyStatus = async (key: APIKey) => {
  try {
    await ElMessageBox.confirm(
      `确定要${key.is_active ? '禁用' : '启用'}这个API密钥吗？`,
      `${key.is_active ? '禁用' : '启用'}密钥`,
      {
        type: 'warning',
        confirmButtonText: key.is_active ? '禁用' : '启用',
        cancelButtonText: '取消'
      }
    )
    
    await updateApiKey(key.id, {
      is_active: !key.is_active
    })
    
    await loadApiKeys()
    ElMessage.success(`${key.is_active ? '禁用' : '启用'}API密钥成功`)
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(`${key.is_active ? '禁用' : '启用'}API密钥失败`)
      console.error(`${key.is_active ? '禁用' : '启用'}API密钥失败:`, error)
    }
  }
}

// 复制密钥到剪贴板
const copyKeyToClipboard = async (key: string) => {
  try {
    await navigator.clipboard.writeText(key)
    ElMessage.success('密钥已复制到剪贴板')
  } catch (error) {
    ElMessage.error('复制失败')
  }
}

// 复制新密钥到剪贴板
const copyNewKeyToClipboard = async () => {
  try {
    await navigator.clipboard.writeText(newlyCreatedKey.value)
    ElMessage.success('密钥已复制到剪贴板')
  } catch (error) {
    ElMessage.error('复制失败')
  }
}

// 页面加载时获取API密钥列表
onMounted(() => {
  loadApiKeys()
})
</script>

<style scoped>
.keys-manager-view {
  max-width: 1400px;
  margin: 0 auto;
  padding: 20px;
  /* 隐藏滚动条但保持滚动功能 */
  scrollbar-width: none;
  -ms-overflow-style: none;
}

.keys-manager-view::-webkit-scrollbar {
  display: none;
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

.header-actions {
  display: flex;
  justify-content: flex-end;
  gap: 15px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.create-btn {
  background: linear-gradient(135deg, #409eff 0%, #1a73e8 100%);
  border: none;
  color: white;
  font-weight: 600;
  padding: 12px 24px;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.create-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 25px rgba(64, 158, 255, 0.3);
}

.refresh-btn {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: #a0c3ff;
  font-weight: 500;
  padding: 12px 24px;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.refresh-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(64, 158, 255, 0.3);
}

.keys-card {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 15px;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  transition: all 0.3s ease;
}

.keys-card:hover {
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

.keys-table {
  background: transparent;
}

.keys-table :deep(.el-table__header th) {
  background: rgba(255, 255, 255, 0.05);
  color: #a0c3ff;
}

.keys-table :deep(.el-table__row) {
  background: rgba(255, 255, 255, 0.03);
}

.keys-table :deep(.el-table__row:hover) {
  background: rgba(64, 158, 255, 0.1);
}

.permission-tag {
  margin-right: 5px;
  background: rgba(64, 158, 255, 0.2);
  border-color: rgba(64, 158, 255, 0.3);
  color: #409eff;
}

.quota-info {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.quota-numbers {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 14px;
}

.quota-numbers .used {
  font-weight: bold;
  color: #fff;
}

.quota-numbers .separator {
  color: #a0c3ff;
}

.quota-numbers .total {
  color: #a0c3ff;
}

.quota-progress {
  margin-top: 5px;
}

.action-buttons {
  display: flex;
  gap: 5px;
  flex-wrap: wrap;
}

.action-buttons .el-button {
  margin: 0;
}

.empty-state {
  text-align: center;
  padding: 60px 0;
  color: #a0c3ff;
}

.empty-icon {
  margin-bottom: 20px;
  color: #409eff;
}

.empty-state p {
  font-size: 16px;
  margin-bottom: 20px;
}

/* 自定义对话框样式 - 使用最高优先级确保生效 */
.custom-dialog.custom-create-dialog :deep(.el-dialog),
.custom-dialog.custom-edit-dialog :deep(.el-dialog),
.custom-dialog.custom-view-dialog :deep(.el-dialog),
.custom-dialog.custom-new-key-dialog :deep(.el-dialog) {
  background: rgba(15, 26, 48, 0.95) !important;
  border-radius: 15px !important;
  backdrop-filter: blur(10px) !important;
  border: 1px solid rgba(64, 158, 255, 0.3) !important;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.3) !important;
}

.custom-dialog.custom-create-dialog :deep(.el-dialog__header),
.custom-dialog.custom-edit-dialog :deep(.el-dialog__header),
.custom-dialog.custom-view-dialog :deep(.el-dialog__header),
.custom-dialog.custom-new-key-dialog :deep(.el-dialog__header) {
  border-bottom: 1px solid rgba(255, 255, 255, 0.1) !important;
  padding: 20px !important;
  background: rgba(29, 43, 79, 0.5) !important;
}

.custom-dialog.custom-create-dialog :deep(.el-dialog__title),
.custom-dialog.custom-edit-dialog :deep(.el-dialog__title),
.custom-dialog.custom-view-dialog :deep(.el-dialog__title),
.custom-dialog.custom-new-key-dialog :deep(.el-dialog__title) {
  color: #fff !important;
  font-weight: 600 !important;
  font-size: 1.25rem !important;
}

.custom-dialog.custom-create-dialog :deep(.el-dialog__body),
.custom-dialog.custom-edit-dialog :deep(.el-dialog__body),
.custom-dialog.custom-view-dialog :deep(.el-dialog__body),
.custom-dialog.custom-new-key-dialog :deep(.el-dialog__body) {
  padding: 20px !important;
  background: rgba(15, 26, 48, 0.7) !important;
  color: #fff !important;
}

.custom-dialog.custom-create-dialog :deep(.el-dialog__footer),
.custom-dialog.custom-edit-dialog :deep(.el-dialog__footer),
.custom-dialog.custom-view-dialog :deep(.el-dialog__footer),
.custom-dialog.custom-new-key-dialog :deep(.el-dialog__footer) {
  border-top: 1px solid rgba(255, 255, 255, 0.1) !important;
  padding: 20px !important;
  background: rgba(15, 26, 48, 0.7) !important;
}

.custom-dialog.custom-create-dialog :deep(.el-descriptions__body),
.custom-dialog.custom-edit-dialog :deep(.el-descriptions__body),
.custom-dialog.custom-view-dialog :deep(.el-descriptions__body),
.custom-dialog.custom-new-key-dialog :deep(.el-descriptions__body) {
  background: rgba(255, 255, 255, 0.03) !important;
  border-radius: 8px !important;
  border: 1px solid rgba(255, 255, 255, 0.1) !important;
}

.custom-dialog.custom-create-dialog :deep(.el-descriptions__label),
.custom-dialog.custom-edit-dialog :deep(.el-descriptions__label),
.custom-dialog.custom-view-dialog :deep(.el-descriptions__label),
.custom-dialog.custom-new-key-dialog :deep(.el-descriptions__label) {
  background: rgba(255, 255, 255, 0.05) !important;
  color: #a0c3ff !important;
  font-weight: 500 !important;
}

.custom-dialog.custom-create-dialog :deep(.el-descriptions__content),
.custom-dialog.custom-edit-dialog :deep(.el-descriptions__content),
.custom-dialog.custom-view-dialog :deep(.el-descriptions__content),
.custom-dialog.custom-new-key-dialog :deep(.el-descriptions__content) {
  color: #fff !important;
}

.custom-dialog.custom-create-dialog :deep(.el-form-item__label),
.custom-dialog.custom-edit-dialog :deep(.el-form-item__label),
.custom-dialog.custom-view-dialog :deep(.el-form-item__label),
.custom-dialog.custom-new-key-dialog :deep(.el-form-item__label) {
  color: #a0c3ff !important;
}

.dialog-input :deep(.el-input__wrapper),
.dialog-input :deep(.el-input-number__decrease),
.dialog-input :deep(.el-input-number__increase) {
  background: rgba(255, 255, 255, 0.05) !important;
  border: 1px solid rgba(255, 255, 255, 0.1) !important;
  border-radius: 8px !important;
  box-shadow: none !important;
  transition: all 0.3s ease;
}

.dialog-input :deep(.el-input__wrapper:hover),
.dialog-input :deep(.el-input-number__decrease:hover),
.dialog-input :deep(.el-input-number__increase:hover) {
  border-color: rgba(64, 158, 255, 0.5) !important;
}

.dialog-input :deep(.el-input__wrapper.is-focus),
.dialog-input :deep(.el-input-number.is-focus) {
  border-color: #409eff !important;
  box-shadow: 0 0 0 1px #409eff !important;
}

.dialog-input :deep(.el-input__inner) {
  background: transparent !important;
  color: #fff !important;
}

.dialog-input :deep(.el-input__inner::placeholder) {
  color: #a0c3ff !important;
}

.quota-hint {
  font-size: 12px;
  color: #a0c3ff;
  margin-top: 5px;
}

.cancel-btn {
  background: rgba(255, 255, 255, 0.05) !important;
  border: 1px solid rgba(255, 255, 255, 0.1) !important;
  color: #a0c3ff !important;
  font-weight: 500;
  padding: 12px 24px;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.cancel-btn:hover {
  background: rgba(255, 255, 255, 0.1) !important;
  border-color: rgba(64, 158, 255, 0.3) !important;
}

.confirm-btn {
  background: linear-gradient(135deg, #409eff 0%, #1a73e8 100%) !important;
  border: none !important;
  color: white !important;
  font-weight: 600;
  padding: 12px 24px;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.confirm-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 25px rgba(64, 158, 255, 0.3) !important;
}

.success-icon {
  text-align: center;
  margin-bottom: 20px;
}

.success-message {
  text-align: center;
  margin-bottom: 20px;
  color: #a0c3ff;
}

.key-name-cell strong {
  color: #409eff;
}

.quota-details .quota-progress {
  margin-top: 10px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .header-actions {
    justify-content: center;
  }
  
  .action-buttons {
    flex-direction: column;
  }
  
  .keys-manager-view {
    padding: 15px;
  }
}
</style>