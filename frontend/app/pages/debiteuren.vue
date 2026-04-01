<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold text-slate-900">Debiteuren</h1>
      <button @click="showModal = true" class="bg-primary-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-primary-700 transition-colors flex items-center gap-2">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
        Nieuwe debiteur
      </button>
    </div>

    <!-- Summary -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
      <div class="bg-white rounded-xl border border-surface-200 shadow-sm p-5">
        <p class="text-sm text-slate-500">Totaal openstaand</p>
        <p class="text-2xl font-bold text-red-600 mt-1">{{ formatCurrency(totalOutstanding) }}</p>
        <p class="text-xs text-slate-400 mt-1">{{ ws.outstandingInvoices.length }} openstaande facturen</p>
      </div>
      <div class="bg-white rounded-xl border border-surface-200 shadow-sm p-5">
        <p class="text-sm text-slate-500">Aantal debiteuren</p>
        <p class="text-2xl font-bold text-emerald-600 mt-1">{{ debtors.length }}</p>
        <p class="text-xs text-slate-400 mt-1">in administratie</p>
      </div>
      <div class="bg-white rounded-xl border border-surface-200 shadow-sm p-5">
        <p class="text-sm text-slate-500">Gemiddelde betalingstermijn</p>
        <p class="text-2xl font-bold text-slate-900 mt-1">{{ avgPaymentTerm }} dagen</p>
        <p class="text-xs text-slate-400 mt-1">over alle debiteuren</p>
      </div>
    </div>

    <!-- Debtors table -->
    <div class="bg-white rounded-xl border border-surface-200 shadow-sm overflow-hidden">
      <div class="px-6 py-4 border-b border-surface-200">
        <h2 class="text-lg font-semibold text-slate-900">Klanten</h2>
      </div>
      <table class="w-full">
        <thead>
          <tr class="text-left text-xs font-medium text-slate-500 uppercase tracking-wider bg-surface-50">
            <th class="px-6 py-3">Klant</th>
            <th class="px-6 py-3">KvK</th>
            <th class="px-6 py-3">Facturen</th>
            <th class="px-6 py-3 text-right">Openstaand</th>
            <th class="px-6 py-3">Betalingsgedrag</th>
            <th class="px-6 py-3">Acties</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-surface-100">
          <tr v-if="debtors.length === 0">
            <td colspan="6" class="px-6 py-12 text-center">
              <p class="text-sm text-slate-400">Geen debiteuren gevonden</p>
            </td>
          </tr>
          <tr v-for="d in debtors" :key="d.id" class="hover:bg-surface-50 cursor-pointer" @click="selectedDebtor = d">
            <td class="px-6 py-4">
              <p class="text-sm font-medium text-slate-900">{{ d.name }}</p>
              <p class="text-xs text-slate-500">{{ d.email }}</p>
            </td>
            <td class="px-6 py-4 text-sm text-slate-600">{{ d.kvk }}</td>
            <td class="px-6 py-4 text-sm text-slate-600">{{ d.invoiceCount || 0 }}</td>
            <td class="px-6 py-4 text-sm text-right font-medium text-emerald-600">
              Voldaan
            </td>
            <td class="px-6 py-4">
              <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-100 text-slate-700">
                -
              </span>
            </td>
            <td class="px-6 py-4">
              <button class="text-primary-600 hover:text-primary-700 text-sm font-medium">Bekijk</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Detail panel -->
    <div v-if="selectedDebtor" class="bg-white rounded-xl border border-surface-200 shadow-sm p-6">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-lg font-semibold text-slate-900">{{ selectedDebtor.name }}</h2>
        <button @click="selectedDebtor = null" class="text-slate-400 hover:text-slate-600">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
        </button>
      </div>
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
        <div><p class="text-slate-500">E-mail</p><p class="font-medium text-slate-900">{{ selectedDebtor.email }}</p></div>
        <div><p class="text-slate-500">KvK</p><p class="font-medium text-slate-900">{{ selectedDebtor.kvk }}</p></div>
        <div><p class="text-slate-500">BTW-nummer</p><p class="font-medium text-slate-900">{{ selectedDebtor.btw }}</p></div>
        <div><p class="text-slate-500">Betaaltermijn</p><p class="font-medium text-slate-900">{{ selectedDebtor.paymentTerm }} dagen</p></div>
      </div>
      <h3 class="text-sm font-semibold text-slate-700 mt-6 mb-3">Factuurhistorie</h3>
      <div class="space-y-2">
        <div v-if="debtorInvoices.length === 0" class="py-4 text-center">
          <p class="text-sm text-slate-400">Geen facturen voor deze debiteur</p>
        </div>
        <div v-for="inv in debtorInvoices" :key="inv.number" class="flex items-center justify-between py-2 px-3 bg-surface-50 rounded-lg">
          <div class="flex items-center gap-4">
            <span class="text-sm font-medium text-primary-600">{{ inv.number }}</span>
            <span class="text-sm text-slate-600">{{ inv.date }}</span>
          </div>
          <div class="flex items-center gap-4">
            <span class="text-sm font-medium text-slate-900">{{ formatCurrency(ws.invoiceTotal(inv)) }}</span>
            <span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium" :class="inv.status === 'betaald' ? 'bg-emerald-100 text-emerald-700' : inv.status === 'verlopen' ? 'bg-red-100 text-red-700' : 'bg-amber-100 text-amber-700'">
              {{ inv.status }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- Add modal -->
    <div v-if="showModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50" @click.self="showModal = false">
      <div class="bg-white rounded-xl shadow-xl w-full max-w-lg p-6">
        <h2 class="text-lg font-semibold text-slate-900 mb-4">Nieuwe debiteur</h2>
        <div class="grid grid-cols-2 gap-4">
          <div class="col-span-2"><label class="block text-sm font-medium text-slate-700 mb-1">Bedrijfsnaam</label><input type="text" class="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm focus:ring-2 focus:ring-primary-500" /></div>
          <div><label class="block text-sm font-medium text-slate-700 mb-1">KvK-nummer</label><input type="text" class="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm focus:ring-2 focus:ring-primary-500" /></div>
          <div><label class="block text-sm font-medium text-slate-700 mb-1">BTW-nummer</label><input type="text" class="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm focus:ring-2 focus:ring-primary-500" /></div>
          <div><label class="block text-sm font-medium text-slate-700 mb-1">E-mail</label><input type="email" class="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm focus:ring-2 focus:ring-primary-500" /></div>
          <div><label class="block text-sm font-medium text-slate-700 mb-1">Betaaltermijn (dagen)</label><input type="number" value="30" class="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm focus:ring-2 focus:ring-primary-500" /></div>
        </div>
        <div class="flex justify-end gap-3 mt-6">
          <button @click="showModal = false" class="px-4 py-2 text-sm font-medium text-slate-700 hover:text-slate-900">Annuleren</button>
          <button @click="showModal = false" class="bg-primary-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-primary-700">Opslaan</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const ws = useWorkspaceStore()
const showModal = ref(false)
const selectedDebtor = ref<any>(null)

const debtors = computed(() => ws.debtors)

const debtorInvoices = computed(() => {
  if (!selectedDebtor.value) return []
  return ws.invoices.filter(inv => inv.clientId === selectedDebtor.value.id)
})

const totalOutstanding = computed(() => ws.outstandingAmount)

const avgPaymentTerm = computed(() => {
  if (debtors.value.length === 0) return 0
  return Math.round(debtors.value.reduce((sum, d) => sum + d.paymentTerm, 0) / debtors.value.length)
})

function formatCurrency(value: number): string {
  return '€ ' + Math.abs(value).toLocaleString('nl-NL', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}
</script>
