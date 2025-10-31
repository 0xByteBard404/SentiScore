import axios from 'axios'

// 创建axios实例
const apiClient = axios.create({
  baseURL: '', // 使用相对路径
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 添加请求拦截器
apiClient.interceptors.request.use(
  (config) => {
    // 在发送请求之前做些什么
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    // 对请求错误做些什么
    return Promise.reject(error)
  }
)

// 添加响应拦截器
apiClient.interceptors.response.use(
  (response) => {
    // 对响应数据做点什么
    return response
  },
  (error) => {
    // 对响应错误做点什么
    if (error.response?.status === 401) {
      // token过期或无效，清除本地存储
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// 登录接口
// 请求和响应类型定义
export interface LoginRequest {
  username_or_email: string
  password: string
  remember_me?: boolean
}

export interface LoginResponseData {
  access_token: string
  user: ProfileData
}

export interface LoginResponse {
  data: LoginResponseData
  timestamp: number
}

export interface ProfileData {
  id: number
  username: string
  email: string
  plan_name: string
  quota_remaining: number
}

export interface ProfileResponse {
  data: ProfileData
  timestamp: number
}

export interface APIKeyData {
  id: number
  name: string
  key: string
  permissions: string
  is_active: boolean
  quota_total: number
  quota_used: number
  created_at: string
  updated_at: string
  last_used_at: string | null
}

export interface APIKeyResponse {
  data: APIKeyData
  timestamp: number
}

export interface APIKeyListResponse {
  data: APIKeyData[]
  total: number
  page: number
  limit: number
  timestamp: number
}

export interface CreateAPIKeyRequest {
  name: string
  permissions?: string
  quota_total?: number
}

export interface CreateAPIKeyResponse {
  data: APIKeyData
  timestamp: number
}

export interface UpdateAPIKeyRequest {
  name?: string
  permissions?: string
  is_active?: boolean
  quota_total?: number
}

export interface OrderData {
  id: number
  order_id: string
  plan_name: string
  amount: number
  currency: string
  status: string
  created_at: string
  updated_at: string
}

export interface OrderListResponse {
  data: OrderData[]
  total: number
  page: number
  limit: number
  timestamp: number
}

export interface CallHistoryData {
  id: number
  api_key_id: number
  endpoint: string
  method: string
  request_data: Record<string, any>
  response_status: number
  response_data: Record<string, any>
  ip_address: string
  user_agent: string
  created_at: string
}

export interface CallHistoryResponse {
  data: CallHistoryData[]
  total: number
  page: number
  limit: number
  timestamp: number
}

export const login = async (data: LoginRequest): Promise<LoginResponseData> => {
  try {
    const response = await apiClient.post<LoginResponse>('/auth/login', data)
    return response.data.data
  } catch (error) {
    throw error
  }
}

// 获取用户信息（原getUserInfo）
export const getProfile = async (): Promise<ProfileData> => {
  try {
    const response = await apiClient.get<ProfileResponse>('/auth/profile')
    return response.data.data
  } catch (error) {
    throw error
  }
}

// 获取API密钥列表
export const getApiKeys = async (params = {}): Promise<APIKeyListResponse> => {
  try {
    const response = await apiClient.get<APIKeyListResponse>('/auth/api-keys', { params })
    return response.data
  } catch (error) {
    throw error
  }
}

// 获取API密钥详情
export const getApiKey = async (id: number): Promise<APIKeyData> => {
  try {
    const response = await apiClient.get<APIKeyResponse>(`/auth/api-keys/${id}`)
    return response.data.data
  } catch (error) {
    throw error
  }
}

// 创建API密钥
export const createApiKey = async (data: CreateAPIKeyRequest): Promise<CreateAPIKeyResponse> => {
  try {
    const response = await apiClient.post<CreateAPIKeyResponse>('/auth/api-keys', data)
    return response.data
  } catch (error) {
    throw error
  }
}

// 更新API密钥
export const updateApiKey = async (id: number, data: UpdateAPIKeyRequest): Promise<APIKeyResponse> => {
  try {
    const response = await apiClient.put<APIKeyResponse>(`/auth/api-keys/${id}`, data)
    return response.data
  } catch (error) {
    throw error
  }
}

// 修改密码
export const changePassword = async (data: { 
  current_password: string; 
  new_password: string; 
  confirm_password: string 
}) => {
  try {
    const response = await apiClient.post('/auth/change-password', data)
    return response.data
  } catch (error) {
    throw error
  }
}

// 删除API密钥
export const deleteApiKey = async (id: number) => {
  try {
    const response = await apiClient.delete(`/auth/api-keys/${id}`)
    return response.data
  } catch (error) {
    throw error
  }
}

// 获取订单历史
export const getOrderHistory = async (params: { page: number; limit: number }) => {
  try {
    const response = await apiClient.get('/auth/orders', { params })
    return response.data
  } catch (error) {
    throw error
  }
}

// 获取调用历史
export const getCallHistory = async (params: { page: number; limit: number }) => {
  try {
    const response = await apiClient.get('/auth/calls/history', { params })
    return response.data
  } catch (error) {
    throw error
  }
}

// 用户注册
export interface RegisterRequest {
  username: string
  email: string
  password: string
  confirm_password: string
}

export const register = async (userData: RegisterRequest) => {
  try {
    const response = await apiClient.post('/auth/register', userData)
    return response.data
  } catch (error) {
    throw error
  }
}

// 用户登出
export const logout = async () => {
  try {
    const response = await apiClient.post('/auth/logout')
    return response.data
  } catch (error) {
    throw error
  }
}