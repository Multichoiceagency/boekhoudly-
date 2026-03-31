export function useAuth() {
  const api = useApi()
  const user = useState<{ id: string; email: string; full_name: string } | null>('user', () => null)
  const isLoggedIn = computed(() => !!user.value)

  async function login(email: string, password: string) {
    const data = await api.post<{ access_token: string }>('/auth/login', { email, password })
    localStorage.setItem('auth_token', data.access_token)
    await fetchUser()
  }

  async function register(email: string, password: string, fullName: string, companyName?: string) {
    await api.post('/auth/register', {
      email,
      password,
      full_name: fullName,
      company_name: companyName,
    })
    await login(email, password)
  }

  async function fetchUser() {
    try {
      user.value = await api.get('/auth/me')
    } catch {
      user.value = null
      localStorage.removeItem('auth_token')
    }
  }

  function logout() {
    user.value = null
    localStorage.removeItem('auth_token')
    navigateTo('/')
  }

  return { user, isLoggedIn, login, register, fetchUser, logout }
}
