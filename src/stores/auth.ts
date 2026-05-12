import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { getMe, postLogin, postLogout, postRegister, type AuthUserProfile } from '@/api/authApi'

async function parseJson(response: Response) {
  const text = await response.text().catch(() => '')
  if (!text.trim()) return null
  try {
    return JSON.parse(text)
  } catch {
    return null
  }
}

function extractErrorMessage(payload: unknown, fallback: string): string {
  if (payload && typeof payload === 'object') {
    const obj = payload as Record<string, unknown>
    if (typeof obj.detail === 'string' && obj.detail.trim()) return obj.detail.trim()
    if (typeof obj.message === 'string' && obj.message.trim()) return obj.message.trim()
  }
  return fallback
}

export const useAuthStore = defineStore('auth', () => {
  const user = ref<AuthUserProfile | null>(null)
  const loading = ref(false)
  const initialized = ref(false)

  const isLoggedIn = computed(() => !!user.value)

  async function fetchMe() {
    loading.value = true
    try {
      const response = await getMe()
      if (!response.ok) {
        user.value = null
        initialized.value = true
        return null
      }
      user.value = (await parseJson(response)) as AuthUserProfile | null
      initialized.value = true
      return user.value
    } finally {
      loading.value = false
    }
  }

  async function register(payload: { email: string; password: string; nickname?: string }) {
    loading.value = true
    try {
      const response = await postRegister(payload)
      const data = await parseJson(response)
      if (!response.ok) {
        throw new Error(extractErrorMessage(data, `注册失败 (${response.status})`))
      }
      user.value = data as AuthUserProfile
      initialized.value = true
      return user.value
    } finally {
      loading.value = false
    }
  }

  async function login(payload: { email: string; password: string }) {
    loading.value = true
    try {
      const response = await postLogin(payload)
      const data = await parseJson(response)
      if (!response.ok) {
        throw new Error(extractErrorMessage(data, `登录失败 (${response.status})`))
      }
      user.value = data as AuthUserProfile
      initialized.value = true
      return user.value
    } finally {
      loading.value = false
    }
  }

  async function logout() {
    loading.value = true
    try {
      await postLogout()
      user.value = null
      initialized.value = true
    } finally {
      loading.value = false
    }
  }

  return {
    user,
    loading,
    initialized,
    isLoggedIn,
    fetchMe,
    register,
    login,
    logout,
  }
})
