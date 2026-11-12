import axios from 'axios'

export const TOKEN_KEY = 'dedupwire_token'
export const USER_KEY = 'dedupwire_user'

export const http = axios.create({
  baseURL: '/api',
  timeout: 20000,
})

http.interceptors.request.use((config) => {
  const token = localStorage.getItem(TOKEN_KEY)
  if (token) {
    config.headers = config.headers || {}
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

http.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error?.response?.status === 401) {
      localStorage.removeItem(TOKEN_KEY)
      localStorage.removeItem(USER_KEY)
      if (!location.pathname.startsWith('/login')) {
        location.href = '/login'
      }
    }
    const message =
      error?.response?.data?.message ||
      error?.response?.data?.detail ||
      error?.message ||
      '请求失败'
    return Promise.reject(new Error(message))
  },
)

export function extractFileName(disposition: string | undefined, fallback: string): string {
  if (!disposition) return fallback
  const match = /filename="?([^";]+)"?/.exec(disposition)
  return match ? match[1] : fallback
}
