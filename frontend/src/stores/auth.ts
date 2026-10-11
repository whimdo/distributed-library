import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { getCurrentUser, login as loginRequest } from '@/api/client'
import type { AuthUser, UserRole } from '@/types'

const TOKEN_KEY = 'library_access_token'
const USER_KEY = 'library_auth_user'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem(TOKEN_KEY) || '')
  const saved = localStorage.getItem(USER_KEY)
  const user = ref<AuthUser | null>(saved ? JSON.parse(saved) : null)
  const authenticated = computed(() => Boolean(token.value && user.value))
  const isGlobalAdmin = computed(() => user.value?.role === 'ADMIN')
  const isSiteAdmin = computed(() => user.value?.role === 'SITE_ADMIN')
  const isStudent = computed(() => user.value?.role === 'STUDENT')

  function save(accessToken: string, account: AuthUser) {
    token.value = accessToken; user.value = account
    localStorage.setItem(TOKEN_KEY, accessToken)
    localStorage.setItem(USER_KEY, JSON.stringify(account))
  }

  async function login(username: string, password: string) {
    const response = await loginRequest(username, password)
    save(response.access_token, response.user)
    return response.user
  }

  async function restore() {
    if (!token.value) return false
    try { const account = await getCurrentUser(); save(token.value, account); return true }
    catch { logout(); return false }
  }

  function logout() {
    token.value = ''; user.value = null
    localStorage.removeItem(TOKEN_KEY); localStorage.removeItem(USER_KEY)
  }

  function hasRole(roles?: UserRole[]) { return !roles?.length || Boolean(user.value && roles.includes(user.value.role)) }

  return { token, user, authenticated, isGlobalAdmin, isSiteAdmin, isStudent, login, restore, logout, hasRole }
})
