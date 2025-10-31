<script setup lang="ts">
import { computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'
import { 
  User, 
  Lock, 
  Document,
  Key,
  Histogram,
  Tickets,
  Guide,
  SwitchButton
} from '@element-plus/icons-vue'

const authStore = useAuthStore()
const router = useRouter()

const isLoggedIn = computed(() => authStore.isAuthenticated)

const handleProfile = () => {
  router.push('/dashboard/profile')
}

const handleLogout = async () => {
  await authStore.logout()
  router.push('/login')
}

const handleHome = () => {
  router.push('/')
}
</script>

<template>
  <el-container class="app-container">
    <el-header class="app-header">
      <div class="header-content">
        <div class="nav">
          <el-menu 
            :default-active="$route.path" 
            mode="horizontal" 
            background-color="#1d2b4f"
            text-color="#a0c3ff"
            active-text-color="#409eff"
            class="nav-menu"
          >
            <div class="header-logo">
              <h2>SentiScore</h2>
            </div>
            <div class="menu-items-wrapper">
              <el-menu-item index="/" @click="handleHome">首页</el-menu-item>
              <el-menu-item 
                v-if="isLoggedIn" 
                index="/dashboard"
                @click="router.push('/dashboard')"
              >
                仪表板
              </el-menu-item>
            </div>
          </el-menu>
        </div>
        <div class="user-actions">
          <template v-if="isLoggedIn">
            <el-dropdown class="user-dropdown">
              <el-button type="primary" class="user-button">
                {{ authStore.user?.username }}
                <el-icon class="el-icon--right">
                  <User />
                </el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu class="custom-dropdown-menu">
                  <el-dropdown-item @click="handleProfile">
                    <el-icon><User /></el-icon>
                    个人资料
                  </el-dropdown-item>
                  <el-dropdown-item divided @click="handleLogout">
                    <el-icon><SwitchButton /></el-icon>
                    退出登录
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </template>
          <template v-else>
            <el-button 
              type="primary" 
              @click="$router.push({ name: 'Login' })"
              class="auth-button"
            >
              登录
            </el-button>
            <el-button 
              @click="$router.push({ name: 'Register' })"
              class="auth-button"
            >
              注册
            </el-button>
          </template>
        </div>
      </div>
    </el-header>
    
    <el-main class="app-main">
      <router-view />
    </el-main>
  </el-container>
</template>

<style scoped>
.app-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.app-header {
  background: linear-gradient(135deg, #1d2b4f 0%, #0f1a30 100%);
  color: #fff;
  padding: 0;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
  z-index: 1000;
  height: 60px;
  flex-shrink: 0;
}

.header-content {
  display: flex;
  align-items: center;
  height: 100%;
  padding: 0 20px;
}

.nav {
  flex: 1;
  margin: 0 20px;
  height: 100%;
}

.nav-menu {
  height: 100%;
  border: none !important;
}

.nav :deep(.el-menu) {
  display: flex;
  align-items: center;
  height: 100%;
  border: none !important;
}

.nav :deep(.el-menu-item) {
  height: 100%;
  display: flex;
  align-items: center;
  border: none !important;
  padding: 0 20px;
  transition: all 0.3s ease;
}

.nav :deep(.el-menu-item:hover) {
  background: rgba(64, 158, 255, 0.1) !important;
}

.nav :deep(.el-menu-item.is-active) {
  background: rgba(64, 158, 255, 0.2) !important;
}

.menu-items-wrapper {
  margin-left: 30px; /* 向右平移30像素 */
  display: flex;
  align-items: center;
}

.header-logo h2 {
  margin: 0 20px 0 0;
  color: #fff;
  font-size: 1.5rem;
  height: 100%;
  display: flex;
  align-items: center;
  font-weight: 600;
  background: linear-gradient(90deg, #409eff, #67c23a);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.user-actions {
  display: flex;
  gap: 10px;
  height: 100%;
  align-items: center;
}

.user-button,
.auth-button {
  height: 32px;
  margin: 0;
  background: rgba(64, 158, 255, 0.1);
  border: 1px solid rgba(64, 158, 255, 0.3);
  color: #409eff;
  backdrop-filter: blur(10px);
  transition: all 0.3s ease;
}

.user-button:hover,
.auth-button:hover {
  background: rgba(64, 158, 255, 0.2);
  border-color: rgba(64, 158, 255, 0.5);
  transform: translateY(-2px);
}

/* 自定义下拉菜单样式 - 确保与系统色调一致 */
.custom-dropdown-menu {
  background: rgba(15, 26, 48, 0.95) !important;
  border: 1px solid rgba(64, 158, 255, 0.3) !important;
  backdrop-filter: blur(10px);
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.3) !important;
  border-radius: 8px !important;
}

:deep(.custom-dropdown-menu .el-dropdown-menu__item) {
  color: #a0c3ff !important;
  transition: all 0.3s ease;
  border-radius: 4px !important;
  margin: 2px 4px !important;
}

:deep(.custom-dropdown-menu .el-dropdown-menu__item:hover) {
  background: rgba(64, 158, 255, 0.2) !important;
  color: #409eff !important;
}

:deep(.custom-dropdown-menu .el-dropdown-menu__item--divided) {
  border-top: 1px solid rgba(255, 255, 255, 0.1) !important;
  margin: 4px 0 !important;
  padding-top: 4px !important;
}

:deep(.custom-dropdown-menu .el-dropdown-menu__item i) {
  margin-right: 8px;
  color: #a0c3ff;
}

:deep(.custom-dropdown-menu .el-dropdown-menu__item:hover i) {
  color: #409eff;
}

.app-main {
  background: linear-gradient(135deg, #1d2b4f 0%, #0f1a30 100%);
  padding: 0;
  flex: 1;
  overflow-y: auto;
  color: #fff;
  /* 隐藏滚动条但保持滚动功能 */
  scrollbar-width: none;
  -ms-overflow-style: none;
}

.app-main::-webkit-scrollbar {
  display: none;
}
</style>