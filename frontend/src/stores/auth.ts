import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { fetchMe, login as loginApi } from '../api/auth'
import { TOKEN_KEY, USER_KEY } from '../api/http'
import type { User } from '../types'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string>(localStorage.getItem(TOKEN_KEY) || '')
  const user = ref<User | null>(readStoredUser())
  const loginError = ref<string | null>(null)
  const loading = ref(false)

  function readStoredUser(): User | null {
    const raw = localStorage.getItem(USER_KEY)
    if (!raw) return null
    try {
      return JSON.parse(raw) as User
    } catch {
      return null
    }
  }

  function persist() {
    if (token.value) localStorage.setItem(TOKEN_KEY, token.value)
    else localStorage.removeItem(TOKEN_KEY)
    if (user.value) localStorage.setItem(USER_KEY, JSON.stringify(user.value))
    else localStorage.removeItem(USER_KEY)
  }

  async function login(email: string, password: string): Promise<boolean> {
    loading.value = true
    loginError.value = null
    try {
      const response = await loginApi(email, password)
      token.value = response.access_token
      user.value = response.user
      persist()
      return true
    } catch (exc) {
      loginError.value = exc instanceof Error ? exc.message : '登录失败'
      return false
    } finally {
      loading.value = false
    }
  }

  async function restore(): Promise<void> {
    if (!token.value) return
    try {
      user.value = await fetchMe()
      persist()
    } catch {
      logout()
    }
  }

  function logout() {
    token.value = ''
    user.value = null
    persist()
  }

  const isAuthenticated = computed(() => Boolean(token.value && user.value))
  const isAdmin = computed(() => user.value?.role === 'admin')
  const role = computed(() => user.value?.role || '')

  return { token, user, loginError, loading, isAuthenticated, isAdmin, role, login, restore, logout }
})
