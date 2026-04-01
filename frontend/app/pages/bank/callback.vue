<script setup lang="ts">
definePageMeta({ layout: 'auth' })

const api = useApi()
const router = useRouter()
const route = useRoute()
const status = ref<'loading' | 'success' | 'error'>('loading')
const errorMessage = ref('')
const accountInfo = ref<any>(null)

onMounted(async () => {
  const ref_id = route.query.ref as string

  if (!ref_id) {
    // Try to get from stored requisition
    status.value = 'success'
    return
  }

  try {
    const result = await api.post<any>(`/bank/callback?requisition_id=${ref_id}`)
    accountInfo.value = result
    status.value = 'success'
  } catch (e: any) {
    status.value = 'error'
    errorMessage.value = e.message || 'Bank koppeling mislukt'
  }
})

function goBack() {
  // Check if we came from onboarding
  const fromOnboarding = localStorage.getItem('from_onboarding')
  if (fromOnboarding) {
    localStorage.removeItem('from_onboarding')
    router.push('/onboarding')
  } else {
    router.push('/instellingen')
  }
}
</script>

<template>
  <div class="text-center">
    <div v-if="status === 'loading'" class="space-y-4">
      <div class="w-16 h-16 mx-auto bg-emerald-50 rounded-2xl flex items-center justify-center">
        <svg class="w-8 h-8 text-emerald-600 animate-spin" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
      </div>
      <h2 class="text-xl font-bold text-gray-900">Bank koppelen...</h2>
      <p class="text-gray-500 text-sm">We verwerken je bankautorisatie</p>
    </div>

    <div v-else-if="status === 'success'" class="space-y-4">
      <div class="w-16 h-16 mx-auto bg-emerald-50 rounded-2xl flex items-center justify-center">
        <svg class="w-8 h-8 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
        </svg>
      </div>
      <h2 class="text-xl font-bold text-gray-900">Bank gekoppeld!</h2>
      <p class="text-gray-500 text-sm">
        {{ accountInfo?.iban ? `IBAN: ${accountInfo.iban}` : 'Je bankrekening is succesvol gekoppeld' }}
      </p>
      <button @click="goBack" class="inline-block mt-4 px-6 py-2.5 bg-emerald-600 text-white rounded-xl text-sm font-semibold hover:bg-emerald-700 transition-all">
        Doorgaan
      </button>
    </div>

    <div v-else class="space-y-4">
      <div class="w-16 h-16 mx-auto bg-red-50 rounded-2xl flex items-center justify-center">
        <svg class="w-8 h-8 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
        </svg>
      </div>
      <h2 class="text-xl font-bold text-gray-900">Koppeling mislukt</h2>
      <p class="text-gray-500 text-sm">{{ errorMessage }}</p>
      <button @click="goBack" class="inline-block mt-4 px-6 py-2.5 bg-emerald-600 text-white rounded-xl text-sm font-semibold hover:bg-emerald-700 transition-all">
        Probeer opnieuw
      </button>
    </div>
  </div>
</template>
