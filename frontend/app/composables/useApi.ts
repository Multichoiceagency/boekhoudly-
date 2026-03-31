export function useApi() {
  const config = useRuntimeConfig()
  const baseUrl = config.public.apiUrl as string

  async function $fetch<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const token = localStorage.getItem('auth_token')

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string> || {}),
    }

    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }

    const response = await fetch(`${baseUrl}/api${endpoint}`, {
      ...options,
      headers,
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Onbekende fout' }))
      throw new Error(error.detail || `HTTP ${response.status}`)
    }

    return response.json()
  }

  return {
    get: <T>(endpoint: string) => $fetch<T>(endpoint),
    post: <T>(endpoint: string, body?: unknown) =>
      $fetch<T>(endpoint, { method: 'POST', body: JSON.stringify(body) }),
    put: <T>(endpoint: string, body?: unknown) =>
      $fetch<T>(endpoint, { method: 'PUT', body: JSON.stringify(body) }),
    delete: <T>(endpoint: string) =>
      $fetch<T>(endpoint, { method: 'DELETE' }),
    upload: async <T>(endpoint: string, file: File): Promise<T> => {
      const token = localStorage.getItem('auth_token')
      const formData = new FormData()
      formData.append('file', file)

      const headers: Record<string, string> = {}
      if (token) headers['Authorization'] = `Bearer ${token}`

      const response = await fetch(`${baseUrl}/api${endpoint}`, {
        method: 'POST',
        headers,
        body: formData,
      })

      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Upload fout' }))
        throw new Error(error.detail)
      }

      return response.json()
    },
  }
}
