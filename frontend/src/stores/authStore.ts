import { reactive, computed } from 'vue'

interface User {
  id: string
  name: string
  email: string
  created_at: string
}

interface AuthState {
  token: string | null
  user: User | null
}

const state = reactive<AuthState>({
  token: localStorage.getItem('access_token'),
  user: null,
})

export const authStore = {
  state,

  isAuthenticated: computed(() => !!state.token),

  setToken(token: string) {
    state.token = token
    localStorage.setItem('access_token', token)
  },

  setUser(user: User) {
    state.user = user
  },

  logout() {
    state.token = null
    state.user = null
    localStorage.removeItem('access_token')
  },

  getToken(): string | null {
    return state.token
  },
}
