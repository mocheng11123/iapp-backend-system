import api from '@/utils/request'

export interface Feedback {
  id: string
  title: string
  content: string
  status: number
  username?: string
  created_at: string
}

export function getFeedbacks(params?: { status?: number }) {
  return api.get<Feedback[]>('/dev/feedback', { params })
}

export function updateFeedbackStatus(id: string, data: { status: number }) {
  return api.put(`/dev/feedback/${id}/status`, data)
}

export function replyFeedback(id: string, data: { reply_content: string }) {
  return api.post(`/dev/feedback/${id}/reply`, data)
}

export function getTransactions(params?: { limit?: number; offset?: number }) {
  return api.get('/dev/transactions', { params })
}
