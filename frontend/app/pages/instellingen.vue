<template>
  <div class="space-y-6">
    <h1 class="text-2xl font-bold text-slate-900">Instellingen</h1>

    <!-- Tabs -->
    <div class="flex gap-1 bg-surface-100 p-1 rounded-lg w-fit">
      <button
        v-for="tab in tabs"
        :key="tab"
        @click="activeTab = tab"
        class="px-4 py-2 text-sm font-medium rounded-md transition-colors"
        :class="activeTab === tab ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-600 hover:text-slate-900'"
      >
        {{ tab }}
      </button>
    </div>

    <!-- Bedrijf tab -->
    <div v-if="activeTab === 'Bedrijf'" class="bg-white rounded-xl border border-surface-200 shadow-sm p-6">
      <h2 class="text-lg font-semibold text-slate-900 mb-6">Bedrijfsgegevens</h2>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-2xl">
        <div>
          <label class="block text-sm font-medium text-slate-700 mb-1">Bedrijfsnaam</label>
          <input type="text" value="De Vries Digital BV" class="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-transparent" />
        </div>
        <div>
          <label class="block text-sm font-medium text-slate-700 mb-1">KvK-nummer</label>
          <input type="text" value="12345678" class="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-transparent" />
        </div>
        <div>
          <label class="block text-sm font-medium text-slate-700 mb-1">BTW-nummer</label>
          <input type="text" value="NL123456789B01" class="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-transparent" />
        </div>
        <div>
          <label class="block text-sm font-medium text-slate-700 mb-1">E-mailadres</label>
          <input type="email" value="info@devries-digital.nl" class="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-transparent" />
        </div>
        <div class="md:col-span-2">
          <label class="block text-sm font-medium text-slate-700 mb-1">Adres</label>
          <input type="text" value="Herengracht 123" class="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-transparent" />
        </div>
        <div>
          <label class="block text-sm font-medium text-slate-700 mb-1">Postcode</label>
          <input type="text" value="1015 AB" class="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-transparent" />
        </div>
        <div>
          <label class="block text-sm font-medium text-slate-700 mb-1">Plaats</label>
          <input type="text" value="Amsterdam" class="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-transparent" />
        </div>
      </div>
      <div class="mt-6 pt-4 border-t border-surface-200">
        <button class="bg-primary-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-primary-700 transition-colors">
          Opslaan
        </button>
      </div>
    </div>

    <!-- Gebruikers tab -->
    <div v-if="activeTab === 'Gebruikers'" class="bg-white rounded-xl border border-surface-200 shadow-sm p-6">
      <div class="flex items-center justify-between mb-6">
        <h2 class="text-lg font-semibold text-slate-900">Gebruikers</h2>
        <button class="bg-primary-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-primary-700 transition-colors">
          + Uitnodigen
        </button>
      </div>
      <div class="space-y-3">
        <div class="flex items-center justify-between py-3 px-4 bg-surface-50 rounded-lg">
          <div class="flex items-center gap-3">
            <div class="w-8 h-8 bg-primary-100 text-primary-600 rounded-full flex items-center justify-center text-sm font-semibold">JD</div>
            <div>
              <p class="text-sm font-medium text-slate-900">Jan de Vries</p>
              <p class="text-xs text-slate-500">jan@devries-digital.nl</p>
            </div>
          </div>
          <span class="text-xs font-medium text-primary-600 bg-primary-50 px-2 py-1 rounded">Eigenaar</span>
        </div>
      </div>
    </div>

    <!-- Integraties tab -->
    <div v-if="activeTab === 'Integraties'" class="bg-white rounded-xl border border-surface-200 shadow-sm p-6">
      <h2 class="text-lg font-semibold text-slate-900 mb-6">Integraties</h2>
      <div class="space-y-4">
        <div v-for="integration in integrations" :key="integration.name" class="flex items-center justify-between py-3 px-4 border border-surface-200 rounded-lg">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 bg-surface-100 rounded-lg flex items-center justify-center text-lg">{{ integration.icon }}</div>
            <div>
              <p class="text-sm font-medium text-slate-900">{{ integration.name }}</p>
              <p class="text-xs text-slate-500">{{ integration.description }}</p>
            </div>
          </div>
          <button
            class="px-3 py-1.5 rounded-lg text-sm font-medium transition-colors"
            :class="integration.connected ? 'bg-emerald-100 text-emerald-700' : 'bg-primary-600 text-white hover:bg-primary-700'"
          >
            {{ integration.connected ? 'Verbonden' : 'Verbinden' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Abonnement tab -->
    <div v-if="activeTab === 'Abonnement'" class="bg-white rounded-xl border border-surface-200 shadow-sm p-6">
      <h2 class="text-lg font-semibold text-slate-900 mb-6">Abonnement</h2>
      <div class="bg-primary-50 border border-primary-200 rounded-xl p-6">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-lg font-bold text-primary-900">FiscalFlow Pro</p>
            <p class="text-sm text-primary-600 mt-1">Onbeperkt documenten, AI classificatie, BTW aangiftes</p>
          </div>
          <div class="text-right">
            <p class="text-2xl font-bold text-primary-900">€ 49<span class="text-sm font-normal">/maand</span></p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const activeTab = ref('Bedrijf')
const tabs = ['Bedrijf', 'Gebruikers', 'Integraties', 'Abonnement']

const integrations = [
  { name: 'ING Bank', description: 'Automatische bankkoppeling', icon: '🏦', connected: true },
  { name: 'Mollie', description: 'Betalingen verwerken', icon: '💳', connected: false },
  { name: 'Belastingdienst', description: 'BTW aangifte indienen', icon: '🏛️', connected: false },
  { name: 'Google Drive', description: 'Document opslag', icon: '📁', connected: true },
]
</script>
