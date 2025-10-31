<template>
  <div class="profile-container">
    <div class="page-header">
      <h1 class="page-title">个人资料</h1>
      <p class="page-subtitle">管理您的账户信息和安全设置</p>
    </div>
    
    <div class="profile-content">
      <el-card class="profile-card">
        <template #header>
          <div class="card-header">
            <h2>基本信息</h2>
          </div>
        </template>
        
        <el-form 
          :model="form" 
          :rules="rules" 
          ref="profileForm" 
          label-width="100px"
          class="profile-form"
        >
          <el-form-item label="用户ID" prop="id">
            <el-input v-model="form.id" disabled class="profile-input"></el-input>
          </el-form-item>
          
          <el-form-item label="用户名" prop="username">
            <el-input v-model="form.username" class="profile-input"></el-input>
          </el-form-item>
          
          <el-form-item label="邮箱" prop="email">
            <el-input v-model="form.email" class="profile-input"></el-input>
          </el-form-item>
          
          <el-form-item label="注册时间" prop="created_at">
            <el-input v-model="form.created_at" disabled class="profile-input"></el-input>
          </el-form-item>
          
          <el-form-item>
            <el-button type="primary" @click="onSubmit" :loading="loading" class="submit-btn">保存修改</el-button>
            <el-button @click="resetForm" class="reset-btn">重置</el-button>
          </el-form-item>
        </el-form>
      </el-card>
      
      <el-card class="password-card">
        <template #header>
          <div class="card-header">
            <h2>修改密码</h2>
          </div>
        </template>
        
        <el-form 
          :model="passwordForm" 
          :rules="passwordRules" 
          ref="passwordFormRef" 
          label-width="100px"
          class="password-form"
        >
          <el-form-item label="原密码" prop="old_password">
            <el-input v-model="passwordForm.old_password" type="password" show-password class="password-input"></el-input>
          </el-form-item>
          
          <el-form-item label="新密码" prop="new_password">
            <el-input v-model="passwordForm.new_password" type="password" show-password class="password-input"></el-input>
          </el-form-item>
          
          <el-form-item label="确认密码" prop="confirm_password">
            <el-input v-model="passwordForm.confirm_password" type="password" show-password class="password-input"></el-input>
          </el-form-item>
          
          <el-form-item>
            <el-button type="primary" @click="onChangePassword" :loading="passwordLoading" class="submit-btn">修改密码</el-button>
          </el-form-item>
        </el-form>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { getUserProfile, updateUserProfile } from '@/api/user'
import type { UserProfile, UpdateUserProfileRequest } from '@/api/user'
import { useRouter } from 'vue-router'

const authStore = useAuthStore()
const router = useRouter()
const profileForm = ref<FormInstance>()
const passwordFormRef = ref<FormInstance>()
const loading = ref(false)
const passwordLoading = ref(false)

const form = reactive<UserProfile>({
  id: 0,
  username: '',
  email: '',
  created_at: '',
  last_login: null,
  is_active: true,
  email_verified: false
})

const passwordForm = reactive({
  old_password: '',
  new_password: '',
  confirm_password: ''
})

const rules = reactive<FormRules>({
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 50, message: '用户名长度应在3-50个字符之间', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' }
  ]
})

const passwordRules = reactive<FormRules>({
  old_password: [
    { required: true, message: '请输入原密码', trigger: 'blur' }
  ],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少6位', trigger: 'blur' }
  ],
  confirm_password: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    { 
      validator: (rule: any, value: string, callback: any) => {
        if (value !== passwordForm.new_password) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
})

// 加载用户信息
const loadProfile = async () => {
  try {
    const data = await getUserProfile()
    Object.assign(form, data)
  } catch (error: any) {
    ElMessage.error(error.response?.data?.message || '加载用户信息失败')
  }
}

// 提交表单
const onSubmit = async () => {
  if (!profileForm.value) return
  
  await profileForm.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      try {
        const updateData: UpdateUserProfileRequest = {
          username: form.username,
          email: form.email
        }
        await updateUserProfile(updateData)
        ElMessage.success('资料更新成功')
        // 更新authStore中的用户信息
        authStore.setUser({
          ...authStore.user!,
          username: form.username,
          email: form.email
        })
      } catch (error: any) {
        ElMessage.error(error.response?.data?.message || '更新失败')
      } finally {
        loading.value = false
      }
    }
  })
}

// 修改密码
const onChangePassword = async () => {
  if (!passwordFormRef.value) return
  
  await passwordFormRef.value.validate(async (valid) => {
    if (valid) {
      passwordLoading.value = true
      try {
        // 调用API修改密码
        const updateData: UpdateUserProfileRequest = {
          old_password: passwordForm.old_password,
          new_password: passwordForm.new_password,
          confirm_password: passwordForm.confirm_password
        }
        const response = await updateUserProfile(updateData)
        
        ElMessage.success('密码修改成功')
        
        // 如果需要重新登录，提示用户并跳转到登录页
        if (response.require_relogin) {
          ElMessageBox.alert('密码修改成功，请使用新密码重新登录', '提示', {
            confirmButtonText: '确定',
            type: 'success',
            callback: () => {
              // 清除认证状态并跳转到登录页
              authStore.logout()
              router.push('/login')
            }
          })
        }
        
        // 重置表单
        passwordForm.old_password = ''
        passwordForm.new_password = ''
        passwordForm.confirm_password = ''
      } catch (error: any) {
        ElMessage.error(error.response?.data?.message || '密码修改失败')
      } finally {
        passwordLoading.value = false
      }
    }
  })
}

// 重置表单
const resetForm = () => {
  loadProfile()
}

onMounted(() => {
  loadProfile()
})
</script>

<style scoped>
.profile-container {
  padding: 20px;
  max-width: 1200px;
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
}

.profile-content {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
  gap: 30px;
}

.profile-card,
.password-card {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 15px;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  transition: all 0.3s ease;
}

.profile-card:hover,
.password-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 15px 35px rgba(0, 0, 0, 0.2);
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

.profile-form,
.password-form {
  padding: 20px;
}

.profile-input :deep(.el-input__wrapper),
.password-input :deep(.el-input__wrapper) {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  box-shadow: none;
  transition: all 0.3s ease;
}

.profile-input :deep(.el-input__wrapper:hover),
.password-input :deep(.el-input__wrapper:hover) {
  border-color: rgba(64, 158, 255, 0.5);
}

.profile-input :deep(.el-input__wrapper.is-focus),
.password-input :deep(.el-input__wrapper.is-focus) {
  border-color: #409eff;
  box-shadow: 0 0 0 1px #409eff;
}

.profile-input :deep(.el-input__inner),
.password-input :deep(.el-input__inner) {
  background: transparent;
  color: #fff;
}

.profile-input :deep(.el-input__inner::placeholder),
.password-input :deep(.el-input__inner::placeholder) {
  color: #a0c3ff;
}

.profile-input :deep(.el-form-item__label),
.password-input :deep(.el-form-item__label) {
  color: #a0c3ff;
  font-weight: 500;
}

.submit-btn {
  background: linear-gradient(135deg, #409eff 0%, #1a73e8 100%);
  border: none;
  color: white;
  font-weight: 600;
  padding: 12px 30px;
  border-radius: 8px;
  transition: all 0.3s ease;
  margin-right: 15px;
}

.submit-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 25px rgba(64, 158, 255, 0.3);
}

.reset-btn {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: #a0c3ff;
  font-weight: 500;
  padding: 12px 30px;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.reset-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(64, 158, 255, 0.3);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .profile-content {
    grid-template-columns: 1fr;
  }
  
  .profile-container {
    padding: 15px;
  }
  
  .page-title {
    font-size: 1.8rem;
  }
  
  .submit-btn,
  .reset-btn {
    width: 100%;
    margin-bottom: 10px;
    margin-right: 0;
  }
}
</style>