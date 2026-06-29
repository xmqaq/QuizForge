import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api } from '@/composables/useApi'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('qf_token') || null)
  const user  = ref(null)

  const isLoggedIn = computed(() => !!token.value)
  const isAdmin    = computed(() => user.value?.role === 'admin')
  const isEditor   = computed(() => ['admin', 'editor'].includes(user.value?.role))

  async function fetchMe() {
    user.value = await api('/auth/me')
  }

  async function login(email, password) {
    const fd = new URLSearchParams({ username: email, password })
    const r = await fetch('/api/v1/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: fd,
    })
    const d = await r.json()
    if (!r.ok) throw new Error(d.detail || '登录失败')
    token.value = d.access_token
    localStorage.setItem('qf_token', token.value)
    await fetchMe()
  }

  async function register(email, username, password) {
    await api('/auth/register', { body: { email, username, password } })
  }

  function logout() {
    token.value = null
    user.value  = null
    localStorage.removeItem('qf_token')
  }

  return { token, user, isLoggedIn, isAdmin, isEditor, fetchMe, login, register, logout }
})
