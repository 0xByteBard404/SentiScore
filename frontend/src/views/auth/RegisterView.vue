<template>
  <div class="register-container">
    <div class="register-card">
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
        ref="registerFormRef" 
        :model="registerForm" 
        :rules="registerRules" 
        label-width="0px"
        @submit.prevent="handleRegister"
        class="register-form"
      >
        <el-form-item prop="username">
          <el-input 
            v-model="registerForm.username" 
            placeholder="用户名"
            :prefix-icon="User"
            size="large"
            class="register-input"
          />
        </el-form-item>
        
        <el-form-item prop="email">
          <el-input 
            v-model="registerForm.email" 
            placeholder="邮箱地址"
            :prefix-icon="Message"
            size="large"
            type="email"
            class="register-input"
          />
        </el-form-item>
        
        <el-form-item prop="password">
          <el-input 
            v-model="registerForm.password" 
            placeholder="密码"
            :prefix-icon="Lock"
            size="large"
            type="password"
            show-password
            class="register-input"
          />
        </el-form-item>
        
        <el-form-item prop="confirmPassword">
          <el-input 
            v-model="registerForm.confirmPassword" 
            placeholder="确认密码"
            :prefix-icon="Lock"
            size="large"
            type="password"
            show-password
            class="register-input"
          />
        </el-form-item>
        
        <el-form-item>
          <el-button 
            type="primary" 
            size="large" 
            native-type="submit"
            :loading="loading"
            class="register-btn"
            block
          >
            注册账户
          </el-button>
        </el-form-item>
      </el-form>
      
      <div class="login-link">
        已有账户？<el-button type="text" @click="goToLogin">立即登录</el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { User, Message, Lock } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import type { RegisterData } from '@/types/auth'

const router = useRouter()
const authStore = useAuthStore()

const loading = ref(false)
const registerFormRef = ref<FormInstance>()

const registerForm = reactive({
  username: '',
  email: '',
  password: '',
  confirmPassword: ''
})

const registerRules = reactive<FormRules>({
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度应在3-20个字符之间', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱地址', trigger: 'blur' },
    { type: 'email', message: '请输入有效的邮箱地址', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 30, message: '密码长度应在6-30个字符之间', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    { 
      validator: (rule, value, callback) => {
        if (value !== registerForm.password) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
})

const handleRegister = async () => {
  if (!registerFormRef.value) return
  
  await registerFormRef.value.validate(async (valid) => {
    if (!valid) return
    
    loading.value = true
    try {
      const registerData: RegisterData = {
        username: registerForm.username,
        email: registerForm.email,
        password: registerForm.password,
        confirm_password: registerForm.confirmPassword
      }
      
      await authStore.register(registerData)
      ElMessage.success('注册成功')
      router.push('/dashboard')
    } catch (error: any) {
      ElMessage.error(error.message || '注册失败')
    } finally {
      loading.value = false
    }
  })
}

const goToLogin = () => {
  router.push('/login')
}
</script>

<style scoped>
.register-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #1d2b4f 0%, #0f1a30 100%);
  position: relative;
  overflow: hidden;
}

.register-container::before {
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

.register-card {
  width: 100%;
  max-width: 400px;
  padding: 40px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 15px;
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

.register-form {
  margin-bottom: 20px;
}

.register-input :deep(.el-input__wrapper) {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  box-shadow: none;
  transition: all 0.3s ease;
}

.register-input :deep(.el-input__wrapper:hover) {
  border-color: rgba(64, 158, 255, 0.5);
}

.register-input :deep(.el-input__wrapper.is-focus) {
  border-color: #409eff;
  box-shadow: 0 0 0 1px #409eff;
}

.register-input :deep(.el-input__inner) {
  background: transparent;
  color: #fff;
}

.register-input :deep(.el-input__inner::placeholder) {
  color: #a0c3ff;
}

.register-input :deep(.el-input__prefix) {
  color: #a0c3ff;
}

.register-btn {
  margin-top: 20px;
  padding: 15px;
  font-size: 1rem;
  border-radius: 8px;
  background: linear-gradient(135deg, #409eff 0%, #1a73e8 100%);
  border: none;
  color: white;
  font-weight: 600;
  transition: all 0.3s ease;
}

.register-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 25px rgba(64, 158, 255, 0.3);
}

.login-link {
  text-align: center;
  margin-top: 20px;
  font-size: 14px;
  color: #a0c3ff;
}

.login-link :deep(.el-button) {
  color: #409eff;
  font-weight: 600;
}

.login-link :deep(.el-button:hover) {
  color: #66b1ff;
}

/* 响应式设计 */
@media (max-width: 480px) {
  .register-card {
    margin: 20px;
    padding: 30px 20px;
  }
}
</style>