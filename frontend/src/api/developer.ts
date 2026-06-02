import api from '@/utils/request'

export interface LoginParams {
  email: string
  password: string
}

export interface Developer {
  id: string
  email: string
  balance: number
  status: number
}

export function login(data: LoginParams) {
  return api.post('/dev/login', data)
}

export function getProfile() {
  return api.get<Developer>('/dev/profile')
}

export function getBalance() {
  return api.get('/dev/balance')
}

export function recharge(amount: number) {
  return api.post('/dev/recharge', null, { params: { amount } })
}

export function getTransactions(params?: { limit?: number; offset?: number }) {
  return api.get('/dev/transactions', { params })
}
