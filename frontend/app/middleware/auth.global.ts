import { useWorkspaceStore } from '~/stores/workspace'

/**
 * Global auth middleware — protects all routes except public ones.
 * Redirects unauthenticated users to /login.
 * Redirects authenticated users who haven't completed onboarding to /onboarding.
 */
export default defineNuxtRouteMiddleware(async (to) => {
  // Only run on client side (SSR is disabled, but defensive)
  if (import.meta.server) return

  const publicRoutes = ['/login', '/registreren', '/auth/callback/google', '/wachtwoord-vergeten']
  const isPublicRoute = publicRoutes.some((route) => to.path.startsWith(route))

  const token = localStorage.getItem('auth_token')

  // No token → redirect to login (unless already on a public route)
  if (!token) {
    if (!isPublicRoute) {
      return navigateTo('/login')
    }
    return
  }

  // Has token but on login/register page → redirect to dashboard
  if (token && (to.path === '/login' || to.path === '/registreren')) {
    return navigateTo('/dashboard')
  }

  // For protected routes, verify token and check onboarding
  if (!isPublicRoute) {
    const { user, fetchUser } = useAuth()

    // Fetch user if not loaded yet
    if (!user.value) {
      await fetchUser()
    }

    // Token was invalid (fetchUser cleared it)
    if (!user.value) {
      return navigateTo('/login')
    }

    // Onboarding not completed → force to onboarding page (unless already there)
    if (!user.value.onboarding_completed && to.path !== '/onboarding') {
      return navigateTo('/onboarding')
    }

    // Onboarding completed but trying to access onboarding page → dashboard
    if (user.value.onboarding_completed && to.path === '/onboarding') {
      return navigateTo('/dashboard')
    }

    // Load workspace data from backend if not loaded yet
    if (user.value.onboarding_completed) {
      const ws = useWorkspaceStore()
      if (!ws.loaded && !ws.loading) {
        ws.loadAll()
      }
    }
  }
})
