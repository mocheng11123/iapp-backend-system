import api from '@/utils/request'

export interface App {
  id: string
  name: string
  api_key_prefix: string
  allow_enduser_login: boolean
  created_at: string
}

export interface AppDetail extends App {
  api_key?: string
}

export function getApps() {
  return api.get<App[]>('/dev/apps')
}

export function createApp(data: { name: string; allow_enduser_login?: boolean }) {
  return api.post<AppDetail>('/dev/apps', data)
}

export function getApp(id: string) {
  return api.get<App>(`/dev/apps/${id}`)
}

export function updateApp(id: string, data: any) {
  return api.put(`/dev/apps/${id}`, data)
}

export function deleteApp(id: string) {
  return api.delete(`/dev/apps/${id}`)
}

export function rotateApiKey(id: string) {
  return api.post(`/dev/apps/${id}/rotate-key`)
}

export function getDashboard() {
  return api.get('/dev/dashboard/overview')
}

export function getBillingPrediction() {
  return api.get('/dev/billing/prediction')
}
