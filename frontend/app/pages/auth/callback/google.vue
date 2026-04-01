<script setup lang="ts">
definePageMeta({ layout: 'auth' })

const api = useApi()
const router = useRouter()
const route = useRoute()
const status = ref<'loading' | 'error'>('loading')
const errorMessage = ref('')

onMounted(async () => {
  const code = route.query.code as string

  if (!code) {
    status.value = 'error'
    errorMessage.value = 'Geen autorisatiecode ontvangen van Google'
    return
  }

  try {
    const data = await api.post<{ access_token: string; is_new_user: boolean }>('/auth/google', {
      code,
      redirect_uri: window.location.origin + '/auth/callback/google',
    })

    localStorage.setItem('auth_token', data.access_token)

    if (data.is_new_user) {
      router.push('/onboarding')
    } else {
      router.push('/dashboard')
    }
  } catch (e: any) {
    status.value = 'error'
    errorMessage.value = e.message || 'Google authenticatie mislukt'
  }
})
</script>

<template>
  <div class="text-center">
    <div v-if="status === 'loading'" class="space-y-4">
      <div class="w-16 h-16 mx-auto bg-emerald-50 rounded-2xl flex items-center justify-center">
        <svg class="w-8 h-8 text-emerald-600 animate-spin" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
        </svg>
      </div>
      <h2 class="text-xl font-bold text-gray-900">Even geduld...</h2>
      <p class="text-gray-500 text-sm">Je wordt ingelogd met Google</p>
    </div>

    <div v-else class="space-y-4">
      <div class="w-16 h-16 mx-auto bg-red-50 rounded-2xl flex items-center justify-center">
        <svg class="w-8 h-8 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
        </svg>
      </div>
      <h2 class="text-xl font-bold text-gray-900">Inloggen mislukt</h2>
      <p class="text-gray-500 text-sm">{{ errorMessage }}</p>
      <NuxtLink to="/login" class="inline-block mt-4 px-6 py-2.5 bg-emerald-600 text-white rounded-xl text-sm font-semibold hover:bg-emerald-700 transition-all">
        Terug naar inloggen
      </NuxtLink>
    </div>
  </div>
</template>
