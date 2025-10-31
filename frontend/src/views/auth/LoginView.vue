<template>
  <div class="login-container">
    <div class="login-card">
      <div class="logo-section">
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
      
      <el-form 
        :model="form" 
        :rules="rules" 
        ref="loginForm" 
        class="login-form"
        @submit.prevent="handleSubmit"
      >
        <h2 class="title">用户登录</h2>
        <el-form-item prop="username_or_email">
          <el-input 
            v-model="form.username_or_email" 
            placeholder="用户名或邮箱" 
            prefix-icon="User"
            class="login-input"
          ></el-input>
        </el-form-item>
        <el-form-item prop="password">
          <el-input 
            v-model="form.password" 
            type="password" 
            placeholder="密码"
            prefix-icon="Lock"
            show-password
            class="login-input"
          ></el-input>
        </el-form-item>
        <el-form-item>
          <el-button 
            type="primary" 
            @click="handleSubmit" 
            class="login-btn"
            :loading="loading"
          >
            {{ loading ? '登录中...' : '登录' }}
          </el-button>
        </el-form-item>
      </el-form>
      
      <div class="login-footer">
        <p>还没有账户？<el-button type="text" @click="$router.push('/register')">立即注册</el-button></p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import type { FormInstance } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import { login } from '@/api/auth'
import type { LoginRequest } from '@/api/auth'

const router = useRouter()
const authStore = useAuthStore()

const loginForm = ref<FormInstance>()
const loading = ref(false)

const form = reactive({
  username_or_email: '',
  password: ''
})

const rules = {
  username_or_email: [{ required: true, message: '请输入用户名或邮箱', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

const handleSubmit = async () => {
  if (!loginForm.value) return
  
  await loginForm.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      try {
        const response = await login({
          username_or_email: form.username_or_email,
          password: form.password
        } as LoginRequest)
        
        // 现在response就是LoginResponseData类型
        if (response.access_token) {
          // 登录成功
          authStore.setToken(response.access_token)
          authStore.setUser(response.user)
          
          ElMessage.success('登录成功')
          
          // 跳转到首页
          router.push('/dashboard')
        } else {
          ElMessage.error('登录失败')
        }
      } catch (error: any) {
        console.error('Login error:', error)
        ElMessage.error(error.response?.data?.error || '登录失败，请检查用户名和密码')
      } finally {
        loading.value = false
      }
    }
  })
}
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background: linear-gradient(135deg, #1d2b4f 0%, #0f1a30 100%);
  position: relative;
  overflow: hidden;
}

.login-container::before {
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

.login-card {
  width: 100%;
  max-width: 400px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 15px;
  padding: 40px;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 15px 35px rgba(0, 0, 0, 0.2);
  position: relative;
  z-index: 1;
}

.logo-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 30px;
}

.logo-icon {
  width: 80px;
  height: 80px;
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
  font-size: 2rem;
  font-weight: 700;
  margin: 0;
  background: linear-gradient(90deg, #409eff, #67c23a);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.title {
  text-align: center;
  margin-bottom: 30px;
  color: #fff;
  font-size: 1.5rem;
  font-weight: 600;
}

.login-form {
  margin-bottom: 20px;
}

.login-input :deep(.el-input__wrapper) {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  box-shadow: none;
  transition: all 0.3s ease;
}

.login-input :deep(.el-input__wrapper:hover) {
  border-color: rgba(64, 158, 255, 0.5);
}

.login-input :deep(.el-input__wrapper.is-focus) {
  border-color: #409eff;
  box-shadow: 0 0 0 1px #409eff;
}

.login-input :deep(.el-input__inner) {
  background: transparent;
  color: #fff;
}

.login-input :deep(.el-input__inner::placeholder) {
  color: #a0c3ff;
}

.login-input :deep(.el-input__prefix) {
  color: #a0c3ff;
}

.login-btn {
  width: 100%;
  padding: 15px;
  font-size: 1rem;
  border-radius: 8px;
  background: linear-gradient(135deg, #409eff 0%, #1a73e8 100%);
  border: none;
  color: white;
  font-weight: 600;
  transition: all 0.3s ease;
}

.login-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 25px rgba(64, 158, 255, 0.3);
}

.login-footer {
  text-align: center;
  color: #a0c3ff;
}

.login-footer :deep(.el-button) {
  color: #409eff;
  font-weight: 600;
}

.login-footer :deep(.el-button:hover) {
  color: #66b1ff;
}

/* 响应式设计 */
@media (max-width: 480px) {
  .login-card {
    margin: 20px;
    padding: 30px 20px;
  }
}
</style>