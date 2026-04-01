export function useAuth() {
  const api = useApi()
  const user = useState<{
    id: string
    email: string
    full_name: string
    role?: string
    avatar_url?: string
    oauth_provider?: string
    onboarding_completed?: boolean
    onboarding_step?: number
    company_id?: string
  } | null>('user', () => null)
  const isLoggedIn = computed(() => !!user.value)
  const isAdmin = computed(() => user.value?.role === 'admin')
  const needsOnboarding = computed(() => user.value && !user.value.onboarding_completed)

  async function login(email: string, password: string) {
    const data = await api.post<{ access_token: string; is_new_user: boolean }>('/auth/login', { email, password })
    localStorage.setItem('auth_token', data.access_token)
    await fetchUser()
    return data
  }

  async function register(email: string, password: string, fullName: string, companyName?: string) {
    const data = await api.post<{ access_token: string; is_new_user: boolean }>('/auth/register', {
      email,
      password,
      full_name: fullName,
      company_name: companyName,
    })
    localStorage.setItem('auth_token', data.access_token)
    await fetchUser()
    return data
  }

  async function sendVerificationCode(email: string) {
    return api.post<{ message: string; is_new_user: boolean }>('/auth/send-code', { email })
  }

  async function verifyCode(email: string, code: string, fullName?: string) {
    const data = await api.post<{ access_token: string; is_new_user: boolean }>('/auth/verify-code', {
      email,
      code,
      full_name: fullName,
    })
    localStorage.setItem('auth_token', data.access_token)
    await fetchUser()
    return data
  }

  async function loginWithGoogle(code: string, redirectUri?: string) {
    const data = await api.post<{ access_token: string; is_new_user: boolean }>('/auth/google', {
      code,
      redirect_uri: redirectUri,
    })
    localStorage.setItem('auth_token', data.access_token)
    await fetchUser()
    return data
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
    navigateTo('/login')
  }

  return { user, isLoggedIn, isAdmin, needsOnboarding, login, register, sendVerificationCode, verifyCode, loginWithGoogle, fetchUser, logout }
}
