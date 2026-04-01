<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold text-slate-900">Grootboek</h1>
      <div class="flex gap-2">
        <select v-model="selectedYear" class="px-3 py-2 border border-surface-200 rounded-lg text-sm">
          <option>2026</option>
          <option>2025</option>
        </select>
        <select v-model="selectedCategory" class="px-3 py-2 border border-surface-200 rounded-lg text-sm">
          <option value="">Alle categorieeen</option>
          <option v-for="cat in categories" :key="cat">{{ cat }}</option>
        </select>
        <button class="bg-primary-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-primary-700 transition-colors flex items-center gap-2">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          Exporteer
        </button>
      </div>
    </div>

    <!-- Summary cards -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
      <div class="bg-white rounded-xl border border-surface-200 shadow-sm p-5">
        <p class="text-sm text-slate-500">Totaal debet</p>
        <p class="text-2xl font-bold text-slate-900 mt-1">{{ formatCurrency(totals.debit) }}</p>
      </div>
      <div class="bg-white rounded-xl border border-surface-200 shadow-sm p-5">
        <p class="text-sm text-slate-500">Totaal credit</p>
        <p class="text-2xl font-bold text-slate-900 mt-1">{{ formatCurrency(totals.credit) }}</p>
      </div>
      <div class="bg-white rounded-xl border border-surface-200 shadow-sm p-5">
        <p class="text-sm text-slate-500">Saldo</p>
        <p class="text-2xl font-bold mt-1" :class="totals.debit - totals.credit >= 0 ? 'text-emerald-600' : 'text-red-600'">
          {{ formatCurrency(Math.abs(totals.debit - totals.credit)) }}
        </p>
      </div>
      <div class="bg-white rounded-xl border border-surface-200 shadow-sm p-5">
        <p class="text-sm text-slate-500">Boekingen</p>
        <p class="text-2xl font-bold text-slate-900 mt-1">{{ filteredEntries.length }}</p>
      </div>
    </div>

    <!-- Ledger table -->
    <div class="bg-white rounded-xl border border-surface-200 shadow-sm overflow-hidden">
      <div class="px-6 py-4 border-b border-surface-200 flex items-center justify-between">
        <h2 class="text-lg font-semibold text-slate-900">Grootboekregels</h2>
        <div class="relative">
          <svg class="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <input v-model="searchQuery" type="text" placeholder="Zoek in grootboek..." class="pl-9 pr-4 py-2 border border-surface-200 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 w-64" />
        </div>
      </div>
      <table class="w-full">
        <thead>
          <tr class="text-left text-xs font-medium text-slate-500 uppercase tracking-wider bg-surface-50">
            <th class="px-6 py-3">Datum</th>
            <th class="px-6 py-3">Rekening</th>
            <th class="px-6 py-3">Omschrijving</th>
            <th class="px-6 py-3">Categorie</th>
            <th class="px-6 py-3 text-right">Debet</th>
            <th class="px-6 py-3 text-right">Credit</th>
            <th class="px-6 py-3">Bron</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-surface-100">
          <tr v-for="entry in filteredEntries" :key="entry.id" class="hover:bg-surface-50">
            <td class="px-6 py-3 text-sm text-slate-600">{{ entry.date }}</td>
            <td class="px-6 py-3 text-sm font-medium text-slate-900">{{ entry.account }}</td>
            <td class="px-6 py-3 text-sm text-slate-700">{{ entry.description }}</td>
            <td class="px-6 py-3">
              <span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-surface-100 text-slate-700">
                {{ entry.category }}
              </span>
            </td>
            <td class="px-6 py-3 text-sm text-right font-medium text-slate-900">{{ entry.debit ? formatCurrency(entry.debit) : '' }}</td>
            <td class="px-6 py-3 text-sm text-right font-medium text-slate-900">{{ entry.credit ? formatCurrency(entry.credit) : '' }}</td>
            <td class="px-6 py-3">
              <span class="text-xs px-2 py-0.5 rounded-full" :class="entry.source === 'AI' ? 'bg-primary-100 text-primary-700' : 'bg-surface-100 text-slate-600'">
                {{ entry.source }}
              </span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
const selectedYear = ref('2026')
const selectedCategory = ref('')
const searchQuery = ref('')
const categories = ['Omzet', 'Kosten', 'BTW', 'Bank', 'Afschrijving']

const entries = ref([
  { id: 1, date: '31-03-2026', account: '8000 - Omzet', description: 'Factuur INV-2026-042 Bakkerij de Vries', category: 'Omzet', debit: 0, credit: 2450, source: 'AI' },
  { id: 2, date: '31-03-2026', account: '1300 - Debiteuren', description: 'Factuur INV-2026-042 Bakkerij de Vries', category: 'Omzet', debit: 2964.50, credit: 0, source: 'AI' },
  { id: 3, date: '31-03-2026', account: '1520 - BTW af te dragen', description: 'BTW 21% over INV-2026-042', category: 'BTW', debit: 0, credit: 514.50, source: 'AI' },
  { id: 4, date: '30-03-2026', account: '4200 - Kantoorkosten', description: 'Google Workspace abonnement', category: 'Kosten', debit: 10.74, credit: 0, source: 'AI' },
  { id: 5, date: '30-03-2026', account: '1510 - BTW voorbelasting', description: 'BTW 21% Google Workspace', category: 'BTW', debit: 2.25, credit: 0, source: 'AI' },
  { id: 6, date: '30-03-2026', account: '1100 - Bank', description: 'Betaling Google Ireland Ltd', category: 'Bank', debit: 0, credit: 12.99, source: 'Bank' },
  { id: 7, date: '29-03-2026', account: '4300 - Vervoerskosten', description: 'NS Business Card maart', category: 'Kosten', debit: 143.85, credit: 0, source: 'AI' },
  { id: 8, date: '29-03-2026', account: '1510 - BTW voorbelasting', description: 'BTW 9% NS transport', category: 'BTW', debit: 12.95, credit: 0, source: 'AI' },
  { id: 9, date: '28-03-2026', account: '8000 - Omzet', description: 'Factuur INV-2026-041 WebDesign Studio', category: 'Omzet', debit: 0, credit: 3800, source: 'AI' },
  { id: 10, date: '28-03-2026', account: '1300 - Debiteuren', description: 'Factuur INV-2026-041 WebDesign Studio', category: 'Omzet', debit: 4598, credit: 0, source: 'AI' },
  { id: 11, date: '28-03-2026', account: '1520 - BTW af te dragen', description: 'BTW 21% over INV-2026-041', category: 'BTW', debit: 0, credit: 798, source: 'AI' },
  { id: 12, date: '25-03-2026', account: '4100 - Inventaris', description: 'Bol.com bureaustoelen', category: 'Kosten', debit: 288.43, credit: 0, source: 'Handmatig' },
  { id: 13, date: '22-03-2026', account: '4600 - Marketingkosten', description: 'Facebook Ads campagne', category: 'Kosten', debit: 206.61, credit: 0, source: 'AI' },
  { id: 14, date: '20-03-2026', account: '4400 - Communicatiekosten', description: 'KPN zakelijk internet', category: 'Kosten', debit: 37.19, credit: 0, source: 'AI' },
  { id: 15, date: '15-03-2026', account: '6100 - Afschrijving inventaris', description: 'Afschrijving Q1 2026 kantoorinventaris', category: 'Afschrijving', debit: 625, credit: 0, source: 'AI' },
])

const filteredEntries = computed(() => {
  let result = entries.value
  if (selectedCategory.value) {
    result = result.filter((e) => e.category === selectedCategory.value)
  }
  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase()
    result = result.filter((e) => e.description.toLowerCase().includes(q) || e.account.toLowerCase().includes(q))
  }
  return result
})

const totals = computed(() => ({
  debit: filteredEntries.value.reduce((sum, e) => sum + e.debit, 0),
  credit: filteredEntries.value.reduce((sum, e) => sum + e.credit, 0),
}))

function formatCurrency(value: number): string {
  return '€ ' + value.toLocaleString('nl-NL', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}
</script>
