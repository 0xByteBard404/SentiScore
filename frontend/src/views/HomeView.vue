<template>
  <div class="home-container">
    <div class="hero-section">
      <div class="hero-content">
        <div class="logo-container">
          <div class="logo-icon">
            <svg viewBox="0 0 100 100" class="logo-svg">
              <circle cx="50" cy="50" r="45" fill="none" stroke="#409eff" stroke-width="2"/>
              <circle cx="50" cy="50" r="35" fill="none" stroke="#409eff" stroke-width="2"/>
              <circle cx="50" cy="50" r="25" fill="none" stroke="#409eff" stroke-width="2"/>
              <circle cx="50" cy="50" r="15" fill="#409eff"/>
            </svg>
          </div>
          <h1 class="main-title">SentiScore</h1>
        </div>
        <p class="subtitle">智能情感分析与文本处理平台</p>
        <div class="welcome-message" v-if="authStore.user">
          <p class="welcome-text">欢迎回来, <span class="username">{{ authStore.user.username }}</span></p>
        </div>
        <div class="action-buttons">
          <el-button type="primary" size="large" @click="goToDashboard" class="action-button">
            <el-icon><Histogram /></el-icon>
            进入管理平台
          </el-button>
          <el-button 
            v-if="authStore.user" 
            type="info" 
            size="large" 
            @click="handleLogout" 
            class="action-button logout-btn"
          >
            <el-icon><SwitchButton /></el-icon>
            退出登录
          </el-button>
        </div>
      </div>
    </div>
    
    <div class="features-section">
      <div class="features-grid">
        <div class="feature-card">
          <div class="feature-icon">
            <el-icon size="24" color="#409eff"><ChatLineRound /></el-icon>
          </div>
          <h3>情感分析</h3>
          <p>基于深度学习的情感识别技术，准确分析文本情感倾向</p>
        </div>
        
        <div class="feature-card">
          <div class="feature-icon">
            <el-icon size="24" color="#67c23a"><Document /></el-icon>
          </div>
          <h3>文本分词</h3>
          <p>精准的中文文本分词服务，支持多种分词模式</p>
        </div>
        
        <div class="feature-card">
          <div class="feature-icon">
            <el-icon size="24" color="#e6a23c"><DataLine /></el-icon>
          </div>
          <h3>数据统计</h3>
          <p>实时监控API调用情况，提供详细的数据分析报告</p>
        </div>
        
        <div class="feature-card">
          <div class="feature-icon">
            <el-icon size="24" color="#f56c6c"><Lock /></el-icon>
          </div>
          <h3>安全保障</h3>
          <p>企业级安全防护，保障您的数据和API调用安全</p>
        </div>
      </div>
    </div>
    
    <div class="footer-section">
      <p class="copyright">© 2025 SentiScore 情感分析平台. 保留所有权利.</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'
import { 
  Histogram, 
  SwitchButton, 
  ChatLineRound, 
  Document, 
  DataLine, 
  Lock 
} from '@element-plus/icons-vue'

const router = useRouter()
const authStore = useAuthStore()

const handleLogout = () => {
  authStore.logout()
  ElMessage.success('已退出登录')
  router.push('/login')
}

const goToDashboard = () => {
  router.push('/dashboard')
}
</script>

<style scoped>
.home-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #1d2b4f 0%, #0f1a30 100%);
  color: #fff;
  overflow-x: hidden;
}

.hero-section {
  padding: 80px 20px 60px;
  text-align: center;
  background: radial-gradient(circle at center, rgba(64, 158, 255, 0.1) 0%, transparent 70%);
  position: relative;
  overflow: hidden;
}

.hero-section::before {
  content: "";
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: radial-gradient(circle, rgba(64, 158, 255, 0.05) 0%, transparent 70%);
  animation: rotate 20s linear infinite;
  z-index: -1;
}

@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.hero-content {
  max-width: 800px;
  margin: 0 auto;
  position: relative;
  z-index: 1;
}

.logo-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 30px;
}

.logo-icon {
  width: 120px;
  height: 120px;
  margin-bottom: 20px;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% {
    transform: scale(1);
    box-shadow: 0 0 0 0 rgba(64, 158, 255, 0.4);
  }
  50% {
    transform: scale(1.05);
    box-shadow: 0 0 0 10px rgba(64, 158, 255, 0);
  }
  100% {
    transform: scale(1);
    box-shadow: 0 0 0 0 rgba(64, 158, 255, 0);
  }
}

.logo-svg {
  width: 100%;
  height: 100%;
}

.main-title {
  font-size: 3rem;
  font-weight: 700;
  margin: 0;
  background: linear-gradient(90deg, #409eff, #67c23a);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  text-shadow: 0 0 20px rgba(64, 158, 255, 0.3);
}

.subtitle {
  font-size: 1.2rem;
  color: #a0c3ff;
  margin: 15px 0 30px;
  font-weight: 300;
}

.welcome-message {
  margin: 30px 0;
}

.welcome-text {
  font-size: 1.1rem;
  color: #c0d9ff;
}

.username {
  color: #409eff;
  font-weight: 600;
}

.action-buttons {
  display: flex;
  justify-content: center;
  gap: 20px;
  margin-top: 30px;
  flex-wrap: wrap;
}

.action-button {
  padding: 15px 30px;
  font-size: 1rem;
  border-radius: 30px;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(255, 255, 255, 0.05);
  transition: all 0.3s ease;
}

.action-button:hover {
  transform: translateY(-3px);
  box-shadow: 0 10px 25px rgba(64, 158, 255, 0.3);
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(64, 158, 255, 0.3);
}

.action-button :deep(.el-icon) {
  margin-right: 8px;
}

.logout-btn {
  background: rgba(255, 255, 255, 0.03);
}

.logout-btn:hover {
  background: rgba(245, 108, 108, 0.1);
  border-color: rgba(245, 108, 108, 0.3);
  box-shadow: 0 10px 25px rgba(245, 108, 108, 0.2);
}

.features-section {
  padding: 60px 20px;
  background: rgba(15, 26, 48, 0.7);
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 30px;
  max-width: 1200px;
  margin: 0 auto;
}

.feature-card {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 15px;
  padding: 30px 20px;
  text-align: center;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  transition: all 0.3s ease;
}

.feature-card:hover {
  transform: translateY(-10px);
  box-shadow: 0 15px 35px rgba(0, 0, 0, 0.2);
  border-color: rgba(64, 158, 255, 0.3);
}

.feature-icon {
  width: 60px;
  height: 60px;
  margin: 0 auto 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(64, 158, 255, 0.1);
  border-radius: 50%;
  transition: all 0.3s ease;
}

.feature-card:hover .feature-icon {
  background: rgba(64, 158, 255, 0.2);
  transform: scale(1.1);
}

.feature-card h3 {
  font-size: 1.3rem;
  margin: 0 0 15px;
  color: #fff;
}

.feature-card p {
  font-size: 0.95rem;
  color: #a0c3ff;
  line-height: 1.6;
  margin: 0;
}

.footer-section {
  padding: 30px 20px;
  text-align: center;
  background: rgba(10, 18, 35, 0.8);
}

.copyright {
  color: #6b8cbc;
  font-size: 0.9rem;
  margin: 0;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .hero-section {
    padding: 60px 20px 40px;
  }
  
  .main-title {
    font-size: 2.2rem;
  }
  
  .subtitle {
    font-size: 1rem;
  }
  
  .action-buttons {
    flex-direction: column;
    align-items: center;
    gap: 15px;
  }
  
  .action-button {
    width: 80%;
    max-width: 300px;
  }
  
  .features-grid {
    grid-template-columns: 1fr;
    gap: 20px;
  }
}
</style>