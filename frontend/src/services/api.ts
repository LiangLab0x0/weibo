/**
 * API服务模块
 * 
 * 封装与后端API的通信
 */

import axios, { AxiosInstance, AxiosResponse } from 'axios'
import { message } from 'antd'

// API基础配置
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '/api/v1'

// 创建axios实例
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
apiClient.interceptors.request.use(
  (config) => {
    // 可以在这里添加认证token
    // const token = localStorage.getItem('token')
    // if (token) {
    //   config.headers.Authorization = `Bearer ${token}`
    // }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    return response
  },
  (error) => {
    const errorMessage = error.response?.data?.message || error.message || '请求失败'
    message.error(errorMessage)
    return Promise.reject(error)
  }
)

// 类型定义
export interface TimeRange {
  start_date?: string
  end_date?: string
}

export interface LoginRequest {
  username: string
  password: string
}

export interface UserInfo {
  nickname: string
  followers_count: string
  following_count: string
  weibo_count: string
}

export interface LoginResponse {
  success: boolean
  user_info?: UserInfo
  message: string
  error?: string
}

export interface QRLoginStatus {
  task_id: string
  status: string
  qr_status: 'waiting' | 'scanned' | 'confirmed' | 'expired' | 'error'
  message: string
  qr_code?: string
  user_info?: UserInfo
  error?: string
}

export interface AnalysisRequest {
  time_range?: TimeRange
  keywords?: string[]
  max_posts?: number
}

export interface AnalysisResult {
  post_id: string
  content: string
  date: string
  risk_score: number
  risk_reason: string
  risk_category?: string
  suggestion?: string
  url?: string
}

export interface DeleteRequest {
  post_ids: string[]
  confirm: boolean
}

export interface TaskResponse {
  task_id: string
  status: string
  message: string
}

export interface TaskStatus {
  task_id: string
  status: string
  progress?: number
  message?: string
  result?: any
  error?: string
}

export interface DeleteResult {
  post_id: string
  success: boolean
  error?: string
  timestamp: string
}

// API方法
export const api = {
  /**
   * 扫码登录微博（默认方式）
   */
  loginWeibo: async (request?: Partial<LoginRequest>): Promise<TaskResponse> => {
    const response = await apiClient.post<TaskResponse>('/weibo/login', request || {})
    return response.data
  },

  /**
   * 密码登录微博（备用方式）
   */
  loginWeiboPassword: async (request: LoginRequest): Promise<TaskResponse> => {
    const response = await apiClient.post<TaskResponse>('/weibo/login/password', request)
    return response.data
  },

  /**
   * 检查扫码登录状态
   */
  checkQRLoginStatus: async (taskId: string): Promise<QRLoginStatus> => {
    const response = await apiClient.get<QRLoginStatus>(`/weibo/login/qr-status/${taskId}`)
    return response.data
  },

  /**
   * 分析微博内容
   */
  analyzeContent: async (request: AnalysisRequest): Promise<TaskResponse> => {
    const response = await apiClient.post<TaskResponse>('/weibo/analyze', request)
    return response.data
  },

  /**
   * 批量删除微博
   */
  deletePosts: async (request: DeleteRequest): Promise<TaskResponse> => {
    const response = await apiClient.post<TaskResponse>('/weibo/delete', request)
    return response.data
  },

  /**
   * 获取任务状态
   */
  getTaskStatus: async (taskId: string): Promise<TaskStatus> => {
    const response = await apiClient.get<TaskStatus>(`/weibo/task/${taskId}`)
    return response.data
  },

  /**
   * 取消任务
   */
  cancelTask: async (taskId: string): Promise<{ success: boolean; message: string }> => {
    const response = await apiClient.delete(`/weibo/task/${taskId}`)
    return response.data
  },

  /**
   * 获取系统统计信息
   */
  getStats: async (): Promise<{
    active_tasks: number
    reserved_tasks: number
    total_pending: number
    max_delete_per_hour: number
    operation_delay_range: string
  }> => {
    const response = await apiClient.get('/weibo/stats')
    return response.data
  }
}

export default api 