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

// 用户套餐信息
export interface UserPlan {
  name: string
  quota_total: number
  quota_used: number
  quota_remaining: number
}

// 获取用户信息
export interface UserProfile {
  id: number
  username: string
  email: string
  created_at: string
  last_login: string | null
  is_active: boolean
  email_verified: boolean
}

// 更新用户信息请求体
export interface UpdateUserProfileRequest {
  username?: string
  email?: string
  old_password?: string
  new_password?: string
  confirm_password?: string
}

// 更新用户信息响应
export interface UpdateUserProfileResponse {
  data?: UserProfile
  message: string
  require_relogin?: boolean
}

export interface UserStatistics {
  period: string
  date_range: {
    start_date: string
    end_date: string
  }
  summary: {
    total_calls: number
    successful_calls: number
    failed_calls: number
    avg_response_time: number
  }
  daily_calls: Array<{
    date: string
    count: number
  }>
  endpoint_usage: Array<{
    endpoint: string
    count: number
  }>
  plan_info?: UserPlan  // 添加可选的套餐信息
  total_api_keys?: number  // 添加总API密钥数
}

export interface ApiCallHistory {
  total: number
  page: number
  limit: number
  total_pages: number
  calls: Array<{
    id: number
    user_id: number
    endpoint: string
    method: string
    request_data: any
    response_data: any
    response_status: number
    response_time_ms: number
    ip_address: string
    user_agent: string
    created_at: string
  }>
}

export interface OrderHistory {
  total: number
  page: number
  limit: number
  total_pages: number
  orders: Array<{
    id: number
    order_no: string
    user_id: number
    plan_id: number
    plan_name: string
    amount: number
    status: string
    created_at: string
    paid_at: string | null
    refunded_at: string | null
  }>
}

export const getUserProfile = async (): Promise<UserProfile> => {
  try {
    const response = await apiClient.get('/auth/profile')
    return response.data.data
  } catch (error) {
    throw error
  }
}

export const updateUserProfile = async (data: UpdateUserProfileRequest): Promise<UpdateUserProfileResponse> => {
  try {
    const response = await apiClient.put('/auth/profile', data)
    return response.data
  } catch (error) {
    throw error
  }
}

export const getUserStatistics = async (
  period: string = 'week',
  startDate?: string,
  endDate?: string
): Promise<UserStatistics> => {
  try {
    const params: Record<string, string> = { period }
    if (startDate) params.start_date = startDate
    if (endDate) params.end_date = endDate
    
    const response = await apiClient.get('/auth/statistics', { params })
    return response.data.data
  } catch (error) {
    throw error
  }
}

export const getApiCallHistory = async (
  page: number = 1,
  limit: number = 20,
  startDate?: string,
  endDate?: string,
  endpoint?: string
): Promise<ApiCallHistory> => {
  try {
    const params: Record<string, string | number> = { page, limit }
    if (startDate) params.start_date = startDate
    if (endDate) params.end_date = endDate
    if (endpoint) params.endpoint = endpoint
    
    const response = await apiClient.get('/auth/calls/history', { params })
    return response.data.data
  } catch (error) {
    throw error
  }
}

export const getOrderHistory = async (
  page: number = 1,
  limit: number = 20,
  status?: string,
  startDate?: string,
  endDate?: string
): Promise<OrderHistory> => {
  try {
    const params: Record<string, string | number> = { page, limit }
    if (status) params.status = status
    if (startDate) params.start_date = startDate
    if (endDate) params.end_date = endDate
    
    const response = await apiClient.get('/auth/orders', { params })
    return response.data.data
  } catch (error) {
    throw error
  }
}