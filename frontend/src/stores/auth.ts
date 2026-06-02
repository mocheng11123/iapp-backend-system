import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login as apiLogin, getProfile } from '@/api/developer'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || '')
  const user = ref<any>(null)

  const isAuthenticated = computed(() => !!token.value)

  async function login(email: string, password: string) {
    const res = await apiLogin({ email, password })
    token.value = res.access_token
    localStorage.setItem('token', res.access_token)
    await fetchProfile()
  }

  async function fetchProfile() {
    if (!token.value) return
    try {
      user.value = await getProfile()
    } catch (e) {
      logout()
    }
  }

  function logout() {
    token.value = ''
    user.value = null
    localStorage.removeItem('token')
  }

  return { token, user, isAuthenticated, login, logout, fetchProfile }
})
