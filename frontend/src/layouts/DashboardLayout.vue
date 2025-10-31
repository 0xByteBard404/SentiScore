<template>
  <el-container class="dashboard-layout">
    <!-- 侧边栏 -->
    <el-aside width="200px" class="sidebar">
      <el-menu
        :default-active="activeMenu"
        class="sidebar-menu"
        background-color="#1d2b4f"
        text-color="#a0c3ff"
        active-text-color="#409eff"
        router
      >
        <el-menu-item index="/dashboard">
          <el-icon><Odometer /></el-icon>
          <span>仪表板</span>
        </el-menu-item>
        
        <el-menu-item index="/dashboard/profile">
          <el-icon><User /></el-icon>
          <span>个人资料</span>
        </el-menu-item>
        
        <el-menu-item index="/dashboard/keys">
          <el-icon><Key /></el-icon>
          <span>密钥管理</span>
        </el-menu-item>
        
        <el-menu-item index="/dashboard/history">
          <el-icon><Document /></el-icon>
          <span>调用历史</span>
        </el-menu-item>
        
        <el-menu-item index="/dashboard/orders">
          <el-icon><List /></el-icon>
          <span>订单记录</span>
        </el-menu-item>
        
        <el-menu-item index="/dashboard/docs">
          <el-icon><Reading /></el-icon>
          <span>开发文档</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <!-- 主内容区 -->
    <el-container>
      <!-- 主体内容 -->
      <el-main class="main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { 
  Odometer, 
  User, 
  Key, 
  Document, 
  List, 
  Reading
} from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const activeMenu = computed(() => {
  const { meta, path } = route
  // 如果当前路由设置了activeMenu，则使用它
  if (meta.activeMenu) {
    return meta.activeMenu as string
  }
  return path
})

// 页面加载时获取用户信息
onMounted(() => {
  if (!authStore.user) {
    authStore.getProfile()
  }
})
</script>

<style scoped>
.dashboard-layout {
  height: 100vh;
  width: 100vw;
  margin: 0;
  padding: 0;
  overflow: hidden;
}

.sidebar {
  background: linear-gradient(135deg, #1d2b4f 0%, #0f1a30 100%);
  overflow: hidden;
  box-shadow: 2px 0 10px rgba(0, 0, 0, 0.2);
  height: 100vh;
}

.sidebar-menu {
  border: none;
  height: 100%;
}

.sidebar-menu :deep(.el-menu-item) {
  padding: 0 20px;
  height: 50px;
  display: flex;
  align-items: center;
  transition: all 0.3s ease;
}

.sidebar-menu :deep(.el-menu-item:hover) {
  background: rgba(64, 158, 255, 0.1) !important;
}

.sidebar-menu :deep(.el-menu-item.is-active) {
  background: rgba(64, 158, 255, 0.2) !important;
  border-left: 3px solid #409eff;
}

.main {
  background: linear-gradient(135deg, #1d2b4f 0%, #0f1a30 100%);
  padding: 20px;
  overflow-y: auto;
  color: #fff;
  height: 100vh;
  width: calc(100vw - 200px);
  /* 隐藏滚动条但保持滚动功能 */
  scrollbar-width: none;
  -ms-overflow-style: none;
}

.main::-webkit-scrollbar {
  display: none;
}
</style>