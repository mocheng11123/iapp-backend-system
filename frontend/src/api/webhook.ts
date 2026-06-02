import api from '@/utils/request'

export interface Webhook {
  id: string
  url: string
  events: string[]
  retry_count: number
  retry_interval: number
  is_active: boolean
}

export function createWebhook(data: { url: string; events: string[]; retry_count?: number; retry_interval?: number }) {
  return api.post<Webhook>('/dev/webhooks', data)
}

export function getWebhooks(params?: { app_id?: string }) {
  return api.get<Webhook[]>('/dev/webhooks', { params })
}

export function updateWebhook(id: string, data: Partial<Webhook>) {
  return api.put(`/dev/webhooks/${id}`, data)
}

export function deleteWebhook(id: string) {
  return api.delete(`/dev/webhooks/${id}`)
}
