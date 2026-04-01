<script setup lang="ts">
const api = useApi()
const connections = ref<any[]>([])
const bankConnections = ref<any[]>([])
const loading = ref(true)
const error = ref('')

const providers = [
  {
    key: 'google_drive',
    name: 'Google Drive',
    description: 'Importeer facturen en bonnetjes vanuit Google Drive',
    icon: `<svg viewBox="0 0 24 24" class="w-6 h-6"><path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 01-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z"/><path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/><path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/><path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/></svg>`,
    color: 'bg-blue-50 border-blue-100',
  },
  {
    key: 'dropbox',
    name: 'Dropbox',
    description: 'Synchroniseer documenten vanuit Dropbox',
    icon: `<svg viewBox="0 0 24 24" class="w-6 h-6"><path fill="#0061FF" d="M6 2l6 3.75L6 9.5 0 5.75zM18 2l6 3.75-6 3.75-6-3.75zM0 13.25L6 9.5l6 3.75L6 17zM18 9.5l6 3.75L18 17l-6-3.75zM6 18.25l6-3.75 6 3.75-6 3.75z"/></svg>`,
    color: 'bg-blue-50 border-blue-200',
  },
  {
    key: 'onedrive',
    name: 'OneDrive',
    description: 'Koppel je OneDrive voor automatische import',
    icon: `<svg viewBox="0 0 24 24" class="w-6 h-6"><path fill="#0078D4" d="M14.5 18h-11C1.57 18 0 16.43 0 14.5c0-1.93 1.57-3.5 3.5-3.5.17 0 .34.01.5.04C4.58 8.76 6.6 7 9 7c2.03 0 3.78 1.23 4.53 3h.97c2.21 0 4 1.79 4 4s-1.79 4-4 4z"/><path fill="#0364B8" d="M20.5 18h-8l4-7h.5c2.76 0 5 2.24 5 5 0 1.1-.9 2-2 2z"/></svg>`,
    color: 'bg-sky-50 border-sky-100',
  },
]

async function loadConnections() {
  loading.value = true
  try {
    const [cloud, bank] = await Promise.all([
      api.get<any[]>('/cloud/connections'),
      api.get<any[]>('/bank/connections'),
    ])
    connections.value = cloud
    bankConnections.value = bank
  } catch (e: any) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

function getConnection(providerKey: string) {
  return connections.value.find(c => c.provider === providerKey)
}

async function connectProvider(providerKey: string) {
  try {
    const urlKey = providerKey.replace(/_/g, '-')
    const data = await api.get<{ url: string }>(`/cloud/auth-url/${providerKey}`)
    window.location.href = data.url
  } catch (e: any) {
    error.value = e.message || 'Kon koppeling niet starten'
  }
}

async function disconnectProvider(connectionId: string) {
  if (!confirm('Weet je zeker dat je deze koppeling wilt verwijderen?')) return
  try {
    await api.delete(`/cloud/connections/${connectionId}`)
    await loadConnections()
  } catch (e: any) {
    error.value = e.message
  }
}

async function disconnectBank(connectionId: string) {
  if (!confirm('Weet je zeker dat je deze bankkoppeling wilt verwijderen?')) return
  try {
    await api.delete(`/bank/connections/${connectionId}`)
    await loadConnections()
  } catch (e: any) {
    error.value = e.message
  }
}

onMounted(loadConnections)
</script>

<template>
  <div class="space-y-6">
    <!-- Error -->
    <div v-if="error" class="p-3 bg-red-50 border border-red-100 rounded-xl text-sm text-red-600">
      {{ error }}
    </div>

    <!-- Bank Connections -->
    <div>
      <h3 class="text-base font-semibold text-gray-900 mb-3">Bankkoppelingen</h3>
      <p class="text-sm text-gray-500 mb-4">Koppel je bankrekening voor automatische transactie-import via PSD2</p>

      <div v-if="bankConnections.length" class="space-y-2 mb-4">
        <div v-for="conn in bankConnections" :key="conn.id" class="flex items-center justify-between p-4 bg-white border border-gray-100 rounded-xl">
          <div class="flex items-center gap-3">
            <img v-if="conn.institution_logo" :src="conn.institution_logo" class="w-8 h-8 rounded-lg" />
            <div v-else class="w-8 h-8 bg-emerald-100 rounded-lg flex items-center justify-center text-emerald-600 font-bold text-xs">B</div>
            <div>
              <p class="text-sm font-medium text-gray-900">{{ conn.institution_name }}</p>
              <p class="text-xs text-gray-500">{{ conn.iban || 'Koppeling actief' }}</p>
            </div>
          </div>
          <div class="flex items-center gap-3">
            <span class="text-xs px-2 py-1 rounded-full font-medium" :class="conn.status === 'linked' ? 'bg-emerald-100 text-emerald-700' : 'bg-yellow-100 text-yellow-700'">
              {{ conn.status === 'linked' ? 'Verbonden' : conn.status }}
            </span>
            <button @click="disconnectBank(conn.id)" class="text-xs text-red-500 hover:text-red-700 font-medium">Ontkoppelen</button>
          </div>
        </div>
      </div>

      <NuxtLink to="/instellingen?tab=bank" class="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-emerald-700 bg-emerald-50 rounded-xl hover:bg-emerald-100 transition-colors">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" /></svg>
        Bank toevoegen
      </NuxtLink>
    </div>

    <!-- Divider -->
    <div class="border-t border-gray-100"></div>

    <!-- Cloud Storage -->
    <div>
      <h3 class="text-base font-semibold text-gray-900 mb-3">Cloud Opslag</h3>
      <p class="text-sm text-gray-500 mb-4">Importeer documenten rechtstreeks vanuit je cloud opslag</p>

      <div class="space-y-3">
        <div v-for="provider in providers" :key="provider.key" class="flex items-center justify-between p-4 bg-white border border-gray-100 rounded-xl hover:shadow-sm transition-all">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-xl flex items-center justify-center" :class="provider.color" v-html="provider.icon"></div>
            <div>
              <p class="text-sm font-medium text-gray-900">{{ provider.name }}</p>
              <p v-if="getConnection(provider.key)" class="text-xs text-emerald-600">
                {{ getConnection(provider.key).email }} - {{ getConnection(provider.key).files_imported || 0 }} bestanden geimporteerd
              </p>
              <p v-else class="text-xs text-gray-500">{{ provider.description }}</p>
            </div>
          </div>
          <div>
            <div v-if="getConnection(provider.key)" class="flex items-center gap-2">
              <span class="text-xs px-2 py-1 bg-emerald-100 text-emerald-700 rounded-full font-medium">Verbonden</span>
              <button @click="disconnectProvider(getConnection(provider.key).id)" class="text-xs text-red-500 hover:text-red-700 font-medium">Ontkoppelen</button>
            </div>
            <button v-else @click="connectProvider(provider.key)" class="px-4 py-2 text-sm font-medium text-emerald-700 bg-emerald-50 rounded-xl hover:bg-emerald-100 transition-colors">
              Koppelen
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex justify-center py-4">
      <svg class="w-5 h-5 text-emerald-600 animate-spin" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
      </svg>
    </div>
  </div>
</template>
