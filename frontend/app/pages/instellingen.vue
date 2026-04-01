<template>
  <div class="space-y-6">
    <h1 class="text-2xl font-bold text-slate-900">Instellingen</h1>

    <div class="flex gap-1 bg-surface-100 p-1 rounded-lg w-fit">
      <button v-for="tab in tabs" :key="tab" @click="activeTab = tab" class="px-4 py-2 text-sm font-medium rounded-md transition-colors" :class="activeTab === tab ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-600 hover:text-slate-900'">{{ tab }}</button>
    </div>

    <!-- Bedrijf -->
    <div v-if="activeTab === 'Bedrijf'" class="bg-white rounded-xl border border-surface-200 shadow-sm p-6">
      <h2 class="text-lg font-semibold text-slate-900 mb-6">Bedrijfsgegevens - {{ ws.activeCompany.name }}</h2>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-2xl">
        <div><label class="block text-sm font-medium text-slate-700 mb-1">Bedrijfsnaam</label><input v-model="brandingForm.companyName" type="text" class="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm focus:ring-2 focus:ring-primary-500" /></div>
        <div><label class="block text-sm font-medium text-slate-700 mb-1">KvK-nummer</label><input v-model="brandingForm.kvk" type="text" class="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm" /></div>
        <div><label class="block text-sm font-medium text-slate-700 mb-1">BTW-nummer</label><input v-model="brandingForm.btw" type="text" class="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm" /></div>
        <div><label class="block text-sm font-medium text-slate-700 mb-1">IBAN</label><input v-model="brandingForm.iban" type="text" class="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm" /></div>
        <div><label class="block text-sm font-medium text-slate-700 mb-1">E-mailadres</label><input v-model="brandingForm.email" type="email" class="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm" /></div>
        <div><label class="block text-sm font-medium text-slate-700 mb-1">Telefoon</label><input v-model="brandingForm.phone" type="text" class="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm" /></div>
        <div><label class="block text-sm font-medium text-slate-700 mb-1">Website</label><input v-model="brandingForm.website" type="text" class="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm" /></div>
        <div class="md:col-span-2"><label class="block text-sm font-medium text-slate-700 mb-1">Adres</label><input v-model="brandingForm.address" type="text" class="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm" /></div>
        <div><label class="block text-sm font-medium text-slate-700 mb-1">Postcode</label><input v-model="brandingForm.postcode" type="text" class="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm" /></div>
        <div><label class="block text-sm font-medium text-slate-700 mb-1">Plaats</label><input v-model="brandingForm.city" type="text" class="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm" /></div>
      </div>
      <div class="mt-6 pt-4 border-t border-surface-200">
        <button @click="saveBranding" class="bg-primary-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-primary-700">Opslaan</button>
        <span v-if="saved" class="ml-3 text-sm text-emerald-600">Opgeslagen!</span>
      </div>
    </div>

    <!-- Branding -->
    <div v-if="activeTab === 'Branding'" class="space-y-6">
      <div class="bg-white rounded-xl border border-surface-200 shadow-sm p-6">
        <h2 class="text-lg font-semibold text-slate-900 mb-6">Huisstijl - {{ ws.activeCompany.name }}</h2>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <!-- Logo upload -->
          <div>
            <label class="block text-sm font-medium text-slate-700 mb-2">Logo</label>
            <div class="border-2 border-dashed border-surface-300 rounded-xl p-6 text-center cursor-pointer hover:border-primary-400" @click="$refs.logoInput?.click()">
              <input ref="logoInput" type="file" accept="image/*" class="hidden" @change="handleLogoUpload" />
              <div v-if="brandingForm.logo" class="flex justify-center mb-2">
                <img :src="brandingForm.logo" class="max-h-16" />
              </div>
              <p class="text-sm text-slate-500">{{ brandingForm.logo ? 'Klik om te wijzigen' : 'Upload je logo (PNG, SVG)' }}</p>
            </div>
          </div>
          <!-- Primary color -->
          <div>
            <label class="block text-sm font-medium text-slate-700 mb-2">Primaire kleur</label>
            <div class="flex items-center gap-4">
              <input type="color" v-model="brandingForm.primaryColor" class="w-12 h-12 rounded-lg border border-surface-200 cursor-pointer" />
              <input type="text" v-model="brandingForm.primaryColor" class="px-3 py-2 border border-surface-200 rounded-lg text-sm w-32 font-mono" />
            </div>
            <div class="flex gap-2 mt-3">
              <button v-for="color in presetColors" :key="color" @click="brandingForm.primaryColor = color" class="w-8 h-8 rounded-lg border-2 transition-all" :style="{ backgroundColor: color }" :class="brandingForm.primaryColor === color ? 'border-slate-900 scale-110' : 'border-transparent'"></button>
            </div>
          </div>
        </div>

        <!-- Preview -->
        <div class="mt-8 pt-6 border-t border-surface-200">
          <h3 class="text-sm font-semibold text-slate-700 mb-4">Voorbeeld factuur header</h3>
          <div class="border border-surface-200 rounded-lg p-6" :style="{ borderTop: '4px solid ' + brandingForm.primaryColor }">
            <div class="flex justify-between">
              <div>
                <div v-if="brandingForm.logo" class="mb-2"><img :src="brandingForm.logo" class="max-h-10" /></div>
                <p class="text-lg font-bold" :style="{ color: brandingForm.primaryColor }">{{ brandingForm.companyName }}</p>
                <p class="text-xs text-slate-500">{{ brandingForm.address }}, {{ brandingForm.postcode }} {{ brandingForm.city }}</p>
              </div>
              <div class="text-right">
                <h4 class="text-xl font-bold text-slate-900">FACTUUR</h4>
                <p class="text-sm text-slate-500">INV-2026-043</p>
              </div>
            </div>
          </div>
        </div>

        <div class="mt-6 pt-4 border-t border-surface-200">
          <button @click="saveBranding" class="bg-primary-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-primary-700">Branding opslaan</button>
        </div>
      </div>
    </div>

    <!-- Gebruikers -->
    <div v-if="activeTab === 'Gebruikers'" class="bg-white rounded-xl border border-surface-200 shadow-sm p-6">
      <div class="flex items-center justify-between mb-6">
        <h2 class="text-lg font-semibold text-slate-900">Gebruikers</h2>
        <button class="bg-primary-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-primary-700">+ Uitnodigen</button>
      </div>
      <div class="space-y-3">
        <div class="flex items-center justify-between py-3 px-4 bg-surface-50 rounded-lg">
          <div class="flex items-center gap-3">
            <div class="w-8 h-8 bg-primary-100 text-primary-600 rounded-full flex items-center justify-center text-sm font-semibold">JD</div>
            <div><p class="text-sm font-medium text-slate-900">Jan de Vries</p><p class="text-xs text-slate-500">jan@devries-digital.nl</p></div>
          </div>
          <span class="text-xs font-medium text-primary-600 bg-primary-50 px-2 py-1 rounded">Eigenaar</span>
        </div>
      </div>
    </div>

    <!-- Integraties -->
    <div v-if="activeTab === 'Integraties'" class="bg-white rounded-xl border border-surface-200 shadow-sm p-6">
      <h2 class="text-lg font-semibold text-slate-900 mb-6">Integraties</h2>
      <div class="space-y-4">
        <div v-for="integration in integrations" :key="integration.name" class="flex items-center justify-between py-3 px-4 border border-surface-200 rounded-lg">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 bg-surface-100 rounded-lg flex items-center justify-center text-lg">{{ integration.icon }}</div>
            <div><p class="text-sm font-medium text-slate-900">{{ integration.name }}</p><p class="text-xs text-slate-500">{{ integration.description }}</p></div>
          </div>
          <button class="px-3 py-1.5 rounded-lg text-sm font-medium transition-colors" :class="integration.connected ? 'bg-emerald-100 text-emerald-700' : 'bg-primary-600 text-white hover:bg-primary-700'">
            {{ integration.connected ? 'Verbonden' : 'Verbinden' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Abonnement -->
    <div v-if="activeTab === 'Abonnement'" class="bg-white rounded-xl border border-surface-200 shadow-sm p-6">
      <h2 class="text-lg font-semibold text-slate-900 mb-6">Abonnement</h2>
      <div class="bg-primary-50 border border-primary-200 rounded-xl p-6">
        <div class="flex items-center justify-between">
          <div><p class="text-lg font-bold text-primary-900">FiscalFlow Pro</p><p class="text-sm text-primary-600 mt-1">Onbeperkt documenten, AI classificatie, BTW aangiftes, Jaarrekening</p></div>
          <div class="text-right"><p class="text-2xl font-bold text-primary-900">€ 49<span class="text-sm font-normal">/maand</span></p></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const ws = useWorkspaceStore()
const activeTab = ref('Bedrijf')
const tabs = ['Bedrijf', 'Branding', 'Gebruikers', 'Integraties', 'Abonnement']
const saved = ref(false)
const presetColors = ['#4F46E5', '#2563EB', '#0891B2', '#059669', '#D97706', '#DC2626', '#7C3AED', '#EC4899']

const brandingForm = reactive({ ...ws.activeCompany.branding })

watch(() => ws.activeCompanyId, () => {
  Object.assign(brandingForm, ws.activeCompany.branding)
})

function saveBranding() {
  ws.updateBranding(ws.activeCompanyId, { ...brandingForm })
  saved.value = true
  setTimeout(() => { saved.value = false }, 2000)
}

function handleLogoUpload(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (file) {
    const reader = new FileReader()
    reader.onload = () => { brandingForm.logo = reader.result as string }
    reader.readAsDataURL(file)
  }
}

const integrations = [
  { name: 'ING Bank', description: 'Automatische bankkoppeling via PSD2', icon: '🏦', connected: true },
  { name: 'Mollie', description: 'Betalingen verwerken', icon: '💳', connected: false },
  { name: 'Belastingdienst', description: 'BTW aangifte via Digipoort', icon: '🏛️', connected: false },
  { name: 'KvK', description: 'Jaarrekening deponeren', icon: '📋', connected: false },
  { name: 'Google Drive', description: 'Document opslag & backup', icon: '📁', connected: true },
  { name: 'Exact Online', description: 'Data import/export', icon: '📊', connected: false },
]
</script>
