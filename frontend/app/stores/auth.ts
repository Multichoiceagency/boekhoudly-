import { defineStore } from 'pinia'

interface User {
  id: string
  email: string
  full_name: string
  company_id: string | null
}

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null as User | null,
    token: null as string | null,
  }),

  getters: {
    isLoggedIn: (state) => !!state.token,
  },

  actions: {
    setToken(token: string) {
      this.token = token
      localStorage.setItem('auth_token', token)
    },

    setUser(user: User) {
      this.user = user
    },

    logout() {
      this.user = null
      this.token = null
      localStorage.removeItem('auth_token')
    },

    init() {
      const token = localStorage.getItem('auth_token')
      if (token) {
        this.token = token
      }
    },
  },
})
