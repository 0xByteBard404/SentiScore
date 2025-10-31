export interface LoginRequest {
  username: string
  password: string
  remember_me?: boolean
}

export interface LoginData {
  username_or_email: string
  password: string
}

export interface RegisterData {
  username: string
  email: string
  password: string
  confirm_password: string
}

export interface UserData {
  id: number
  username: string
  email: string
  plan_name: string
  quota_remaining: number
}

export interface UserProfile {
  id: number
  username: string
  email: string
  status: string
  email_verified: boolean
  created_at: string
  updated_at: string
  last_login_at: string | null
  login_attempts: number
  locked_until: string | null
  two_factor_enabled: boolean
  plan: {
    name: string
    quota_total: number
    quota_used: number
    quota_remaining: number
    reset_period?: string
    is_active: boolean
  } | null
}

export interface LoginResponseData {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
  user: UserData
}

export interface LoginResponse {
  data: LoginResponseData
  timestamp: number
}

export interface ApiKeyPlan {
  name: string
  quota_total: number
  quota_used: number
  quota_remaining: number
}

export interface ApiKeyInfo {
  api_key: string
  created_at: string
  plan: {
    name: string
    quota_total: number
    quota_used: number
    quota_remaining: number
  }
}

export interface ApiKeyInfoResponse {
  data: ApiKeyInfo
  timestamp: number
}

export interface ApiKey {
  id: number
  user_id: number
  name: string
  permissions: string
  is_active: boolean
  quota_total: number
  quota_used: number
  quota_remaining: number
  last_used_at: string | null
  created_at: string
  updated_at: string | null
}

export interface ApiKeyDetail extends ApiKey {
  key: string
}

export interface CreateApiKeyData {
  name: string
  permissions?: string
  quota_total?: number
}

export interface UpdateApiKeyData {
  name?: string
  permissions?: string
  is_active?: boolean
}

export interface ResetApiKeyResponse {
  data: {
    api_key: string
    message: string
  }
  timestamp: number
}