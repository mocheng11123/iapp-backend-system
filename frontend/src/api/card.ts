import api from '@/utils/request'

export interface CardBatch {
  id: string
  name: string
  type: number
  amount?: number
  duration_days?: number
  total_quantity: number
  remaining_quantity: number
  price_per_card: number
  total_price: number
  created_at: string
}

export function createCardBatch(data: {
  name: string
  type: number
  amount?: number
  duration_days?: number
  quantity: number
}) {
  return api.post<CardBatch>('/dev/card/batches', data)
}

export function getCardBatches(appId?: string) {
  return api.get<CardBatch[]>('/dev/card/batches', { params: { app_id: appId } })
}

export function exportCards(batchId: string) {
  return api.get(`/dev/card/batches/${batchId}/cards`, {
    responseType: 'blob',
  })
}

export function revokeBatch(batchId: string) {
  return api.post(`/dev/card/batches/${batchId}/revoke`)
}
