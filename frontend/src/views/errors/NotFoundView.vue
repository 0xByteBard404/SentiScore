<template>
  <div class="not-found">
    <div class="content">
      <div class="error-container">
        <div class="error-icon">
          <el-icon size="80" color="#f56c6c"><Warning /></el-icon>
        </div>
        <h1 class="error-title">404</h1>
        <p class="error-subtitle">抱歉，您访问的页面不存在</p>
        <div class="error-actions">
          <el-button type="primary" @click="goHome" class="home-btn">返回首页</el-button>
          <el-button @click="goBack" class="back-btn">返回上一页</el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { Warning } from '@element-plus/icons-vue'

const router = useRouter()

const goHome = () => {
  router.push('/')
}

const goBack = () => {
  router.go(-1)
}
</script>

<style scoped>
.not-found {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  width: 100%;
  background: linear-gradient(135deg, #1d2b4f 0%, #0f1a30 100%);
}

.content {
  text-align: center;
  padding: 20px;
}

.error-container {
  max-width: 500px;
  padding: 40px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 15px;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 15px 35px rgba(0, 0, 0, 0.2);
}

.error-icon {
  margin-bottom: 30px;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% {
    transform: scale(1);
    opacity: 0.8;
  }
  50% {
    transform: scale(1.1);
    opacity: 1;
  }
  100% {
    transform: scale(1);
    opacity: 0.8;
  }
}

.error-title {
  font-size: 4rem;
  font-weight: 700;
  margin: 0 0 20px 0;
  color: #f56c6c;
  text-shadow: 0 0 20px rgba(245, 108, 108, 0.3);
}

.error-subtitle {
  font-size: 1.2rem;
  color: #a0c3ff;
  margin: 0 0 30px 0;
}

.home-btn {
  background: linear-gradient(135deg, #409eff 0%, #1a73e8 100%);
  border: none;
  color: white;
  font-weight: 600;
  padding: 12px 30px;
  border-radius: 8px;
  margin: 0 15px;
  transition: all 0.3s ease;
}

.home-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 25px rgba(64, 158, 255, 0.3);
}

.back-btn {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: #a0c3ff;
  font-weight: 500;
  padding: 12px 30px;
  border-radius: 8px;
  margin: 0 15px;
  transition: all 0.3s ease;
}

.back-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(64, 158, 255, 0.3);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .error-container {
    padding: 30px 20px;
    margin: 20px;
  }
  
  .error-title {
    font-size: 3rem;
  }
  
  .home-btn,
  .back-btn {
    display: block;
    width: 100%;
    margin: 10px 0;
  }
}
</style>