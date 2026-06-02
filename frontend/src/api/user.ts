import api from '@/utils/request'

export interface User {
  id: string
  username: string
  status: number
  custom_data: any
  last_login_at?: string
  created_at: string
}

export interface UserQueryParams {
  app_id?: string
  search?: string
  page?: number
  page_size?: number
}

export function getUsers(params?: UserQueryParams) {
  return api.get<User[]>('/api/v1/users', { params })
}

export function getUser(id: string) {
  return api.get<User>(`/api/v1/users/${id}`)
}

export function createUser(data: { username: string; password?: string; custom_data?: any }) {
  return api.post('/api/v1/users', data)
}

export function updateUser(id: string, data: { custom_data?: any }) {
  return api.put(`/api/v1/users/${id}`, data)
}

export function deleteUser(id: string) {
  return api.delete(`/api/v1/users/${id}`)
}

export function toggleUserStatus(id: string, enable: boolean) {
  return api.post(`/api/v1/users/${id}/disable`, null, { params: { enable } })
}

export function exportUsers(format: string = 'csv') {
  window.open(`/api/v1/users/export?format=${format}`, '_blank')
}

export function getUserBalance(id: string) {
  return api.get(`/api/v1/users/${id}/balance`)
}

export function getUserTransactions(id: string, params?: { limit?: number; offset?: number }) {
  return api.get(`/api/v1/users/${id}/transactions`, { params })
}

export function addBalance(id: string, data: { amount: number; reason?: string }) {
  return api.post(`/api/v1/users/${id}/balance/add`, data)
}

export function subBalance(id: string, data: { amount: number; reason?: string }) {
  return api.post(`/api/v1/users/${id}/balance/sub`, data)
}
