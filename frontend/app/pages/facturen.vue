<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold text-slate-900">Facturen</h1>
      <button class="bg-primary-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-primary-700 transition-colors flex items-center gap-2">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
        Nieuwe factuur
      </button>
    </div>

    <!-- Filter tabs -->
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

    <!-- Table -->
    <div class="bg-white rounded-xl border border-surface-200 shadow-sm overflow-hidden">
      <table class="w-full">
        <thead>
          <tr class="text-left text-xs font-medium text-slate-500 uppercase tracking-wider bg-surface-50">
            <th class="px-6 py-3">Nummer</th>
            <th class="px-6 py-3">Klant</th>
            <th class="px-6 py-3">Datum</th>
            <th class="px-6 py-3 text-right">Bedrag</th>
            <th class="px-6 py-3">Status</th>
            <th class="px-6 py-3">Acties</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-surface-100">
          <tr v-for="inv in filteredInvoices" :key="inv.number" class="hover:bg-surface-50">
            <td class="px-6 py-4 text-sm font-medium text-primary-600">{{ inv.number }}</td>
            <td class="px-6 py-4 text-sm text-slate-900">{{ inv.client }}</td>
            <td class="px-6 py-4 text-sm text-slate-600">{{ inv.date }}</td>
            <td class="px-6 py-4 text-sm text-right font-medium text-slate-900">€ {{ inv.amount.toLocaleString('nl-NL') }}</td>
            <td class="px-6 py-4">
              <span
                class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium"
                :class="{
                  'bg-emerald-100 text-emerald-700': inv.status === 'Betaald',
                  'bg-amber-100 text-amber-700': inv.status === 'Verzonden',
                  'bg-red-100 text-red-700': inv.status === 'Verlopen',
                }"
              >
                {{ inv.status }}
              </span>
            </td>
            <td class="px-6 py-4">
              <button class="text-slate-400 hover:text-slate-600">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z" />
                </svg>
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
const activeTab = ref('Alle')
const tabs = ['Alle', 'Verzonden', 'Betaald', 'Verlopen']

const invoices = [
  { number: 'INV-2026-042', client: 'Bakkerij de Vries BV', date: '28 mrt 2026', amount: 2450, status: 'Betaald' },
  { number: 'INV-2026-041', client: 'WebDesign Studio Amsterdam', date: '25 mrt 2026', amount: 3800, status: 'Verzonden' },
  { number: 'INV-2026-040', client: 'Groene Hart Catering', date: '20 mrt 2026', amount: 1275, status: 'Verzonden' },
  { number: 'INV-2026-039', client: 'TechStart Nederland BV', date: '15 mrt 2026', amount: 5600, status: 'Verlopen' },
  { number: 'INV-2026-038', client: 'Van den Berg Consultancy', date: '10 mrt 2026', amount: 890, status: 'Betaald' },
]

const filteredInvoices = computed(() => {
  if (activeTab.value === 'Alle') return invoices
  return invoices.filter((i) => i.status === activeTab.value)
})
</script>
