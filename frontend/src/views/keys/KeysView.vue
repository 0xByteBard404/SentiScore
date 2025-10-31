<template>
  <div class="keys-view">
    <h1>API密钥管理</h1>
    
    <div class="api-key-card">
      <h2>您的API密钥</h2>
      
      <div class="api-key-display" v-if="apiKey">
        <div class="key-info">
          <el-text class="key-value" :type="showKey ? 'primary' : 'info'">
            {{ showKey ? apiKey : '••••••••••••••••••••••••••••••••' }}
          </el-text>
          <div class="key-actions">
            <el-button 
              link 
              @click="toggleKeyVisibility"
              :icon="showKey ? View : Hide"
            >
              {{ showKey ? '隐藏' : '显示' }}
            </el-button>
            <el-button 
              link 
              @click="copyToClipboard"
              :icon="CopyDocument"
            >
              复制
            </el-button>
          </div>
        </div>
        
        <div class="key-details">
          <el-descriptions :column="2" size="small" border>
            <el-descriptions-item label="创建时间">
              {{ formatDate(apiKeyInfo.created_at) }}
            </el-descriptions-item>
            <el-descriptions-item label="套餐名称">
              {{ apiKeyInfo.plan?.name || 'Free' }}
            </el-descriptions-item>
            <el-descriptions-item label="总配额">
              {{ apiKeyInfo.plan?.quota_total || 1000 }}
            </el-descriptions-item>
            <el-descriptions-item label="剩余配额">
              {{ apiKeyInfo.plan?.quota_remaining || 1000 }}
            </el-descriptions-item>
          </el-descriptions>
        </div>
        
        <div class="key-actions-bottom">
          <el-button 
            type="danger" 
            @click="resetApiKey"
            :loading="resetting"
          >
            重置API密钥
          </el-button>
          <el-text class="mx-1" type="warning" size="small">
            重置后旧密钥将失效，请更新所有使用该密钥的应用
          </el-text>
        </div>
      </div>
      
      <div class="no-key" v-else>
        <el-empty description="暂无API密钥信息" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { CopyDocument, View, Hide } from '@element-plus/icons-vue'
import { getApiKeyInfo, resetApiKey } from '@/api/auth'
import type { ApiKeyInfo } from '@/types/auth'
import { formatDate } from '@/utils/date'

const apiKey = ref<string>('')
const apiKeyInfo = ref<ApiKeyInfo>({
  api_key: '',
  created_at: '',
  plan: {
    name: 'Free',
    quota_total: 1000,
    quota_used: 0,
    quota_remaining: 1000
  }
})
const showKey = ref(false)
const resetting = ref(false)

const toggleKeyVisibility = () => {
  showKey.value = !showKey.value
}

const copyToClipboard = async () => {
  try {
    await navigator.clipboard.writeText(apiKey.value)
    ElMessage.success('API密钥已复制到剪贴板')
  } catch (error) {
    ElMessage.error('复制失败，请手动复制')
  }
}

const resetApiKey = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要重置API密钥吗？重置后旧密钥将立即失效，您需要更新所有使用该密钥的应用。',
      '确认重置',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    
    resetting.value = true
    const response = await resetApiKey()
    apiKeyInfo.value = response.data
    apiKey.value = response.data.api_key
    showKey.value = false
    ElMessage.success('API密钥重置成功')
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '重置API密钥失败')
    }
  } finally {
    resetting.value = false
  }
}

const fetchApiKeyInfo = async () => {
  try {
    const response = await getApiKeyInfo()
    apiKeyInfo.value = response.data
    apiKey.value = response.data.api_key
  } catch (error: any) {
    ElMessage.error(error.message || '获取API密钥信息失败')
  }
}

onMounted(() => {
  fetchApiKeyInfo()
})
</script>

<style scoped>
.keys-view {
  padding: 20px;
}

.api-key-card {
  background: var(--el-bg-color);
  border-radius: 8px;
  padding: 24px;
  box-shadow: var(--el-box-shadow-light);
}

.api-key-card h2 {
  margin-top: 0;
  margin-bottom: 24px;
  color: var(--el-text-color-primary);
}

.key-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding: 16px;
  background: var(--el-fill-color-light);
  border-radius: 4px;
}

.key-value {
  font-family: monospace;
  font-size: 16px;
  word-break: break-all;
}

.key-actions {
  display: flex;
  gap: 12px;
}

.key-details {
  margin-bottom: 24px;
}

.key-actions-bottom {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.no-key {
  text-align: center;
  padding: 40px 0;
}
</style>