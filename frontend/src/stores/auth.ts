import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { UserData } from '@/api/auth'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(null)
  const user = ref<UserData | null>(null)
  const isAuthenticated = ref<boolean>(false)

  function setToken(newToken: string) {
    token.value = newToken
    isAuthenticated.value = true
    // 保存到localStorage
    localStorage.setItem('token', newToken)
  }

  function setUser(newUser: UserData) {
    user.value = newUser
    // 保存到localStorage
    localStorage.setItem('user', JSON.stringify(newUser))
  }

  function logout() {
    token.value = null
    user.value = null
    isAuthenticated.value = false
    localStorage.removeItem('token')
    localStorage.removeItem('user')
  }

  function initFromStorage() {
    const savedToken = localStorage.getItem('token')
    const savedUser = localStorage.getItem('user')
    
    if (savedToken) {
      token.value = savedToken
      isAuthenticated.value = true
    }
    
    if (savedUser) {
      user.value = JSON.parse(savedUser)
    }
  }

  return {
    token,
    user,
    isAuthenticated,
    setToken,
    setUser,
    logout,
    initFromStorage
  }
})