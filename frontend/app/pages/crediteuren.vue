<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold text-slate-900">Crediteuren</h1>
      <button @click="showModal = true" class="bg-primary-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-primary-700 transition-colors flex items-center gap-2">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" /></svg>
        Nieuwe crediteur
      </button>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
      <div class="bg-white rounded-xl border border-surface-200 shadow-sm p-5">
        <p class="text-sm text-slate-500">Aantal crediteuren</p>
        <p class="text-2xl font-bold text-red-600 mt-1">{{ creditors.length }}</p>
        <p class="text-xs text-slate-400 mt-1">in administratie</p>
      </div>
      <div class="bg-white rounded-xl border border-surface-200 shadow-sm p-5">
        <p class="text-sm text-slate-500">Totaal kosten</p>
        <p class="text-2xl font-bold text-emerald-600 mt-1">{{ formatCurrency(ws.totalExpenses) }}</p>
        <p class="text-xs text-slate-400 mt-1">{{ ws.expenses.length }} transacties</p>
      </div>
      <div class="bg-white rounded-xl border border-surface-200 shadow-sm p-5">
        <p class="text-sm text-slate-500">BTW te vorderen</p>
        <p class="text-2xl font-bold text-blue-600 mt-1">{{ formatCurrency(ws.btwPaid) }}</p>
        <p class="text-xs text-slate-400 mt-1">voorbelasting</p>
      </div>
    </div>

    <div class="bg-white rounded-xl border border-surface-200 shadow-sm overflow-hidden">
      <div class="px-6 py-4 border-b border-surface-200"><h2 class="text-lg font-semibold text-slate-900">Leveranciers</h2></div>
      <table class="w-full">
        <thead>
          <tr class="text-left text-xs font-medium text-slate-500 uppercase tracking-wider bg-surface-50">
            <th class="px-6 py-3">Leverancier</th>
            <th class="px-6 py-3">Categorie</th>
            <th class="px-6 py-3">Facturen</th>
            <th class="px-6 py-3 text-right">Openstaand</th>
            <th class="px-6 py-3 text-right">Totaal dit jaar</th>
            <th class="px-6 py-3">Acties</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-surface-100">
          <tr v-if="creditors.length === 0">
            <td colspan="6" class="px-6 py-12 text-center">
              <p class="text-sm text-slate-400">Geen crediteuren gevonden</p>
            </td>
          </tr>
          <tr v-for="c in creditors" :key="c.id" class="hover:bg-surface-50 cursor-pointer" @click="selectedCreditor = c">
            <td class="px-6 py-4">
              <p class="text-sm font-medium text-slate-900">{{ c.name }}</p>
              <p class="text-xs text-slate-500">{{ c.email }}</p>
            </td>
            <td class="px-6 py-4"><span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium" :class="catColor(c.category)">{{ c.category }}</span></td>
            <td class="px-6 py-4 text-sm text-slate-600">0</td>
            <td class="px-6 py-4 text-sm text-right font-medium text-emerald-600">
              Voldaan
            </td>
            <td class="px-6 py-4 text-sm text-right font-medium text-slate-900">{{ formatCurrency(0) }}</td>
            <td class="px-6 py-4"><button class="text-primary-600 hover:text-primary-700 text-sm font-medium">Bekijk</button></td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Detail -->
    <div v-if="selectedCreditor" class="bg-white rounded-xl border border-surface-200 shadow-sm p-6">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-lg font-semibold text-slate-900">{{ selectedCreditor.name }}</h2>
        <button @click="selectedCreditor = null" class="text-slate-400 hover:text-slate-600">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
        </button>
      </div>
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm mb-4">
        <div><p class="text-slate-500">Categorie</p><p class="font-medium">{{ selectedCreditor.category }}</p></div>
        <div><p class="text-slate-500">E-mail</p><p class="font-medium">{{ selectedCreditor.email }}</p></div>
        <div><p class="text-slate-500">IBAN</p><p class="font-medium">{{ selectedCreditor.iban }}</p></div>
        <div><p class="text-slate-500">Betaaltermijn</p><p class="font-medium">{{ selectedCreditor.paymentTerm }} dagen</p></div>
      </div>
      <h3 class="text-sm font-semibold text-slate-700 mb-3">Recente facturen</h3>
      <div class="space-y-2">
        <div v-if="creditorExpenses.length === 0" class="py-4 text-center">
          <p class="text-sm text-slate-400">Geen facturen voor deze crediteur</p>
        </div>
        <div v-for="exp in creditorExpenses" :key="exp.id" class="flex items-center justify-between py-2 px-3 bg-surface-50 rounded-lg">
          <div class="flex items-center gap-4"><span class="text-sm font-medium text-slate-700">{{ exp.id }}</span><span class="text-sm text-slate-500">{{ exp.date }}</span></div>
          <div class="flex items-center gap-4">
            <span class="text-sm font-medium text-slate-900">{{ formatCurrency(exp.amount) }}</span>
            <span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium" :class="exp.status === 'geboekt' ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700'">{{ exp.status === 'geboekt' ? 'Betaald' : 'Open' }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Modal -->
    <div v-if="showModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50" @click.self="showModal = false">
      <div class="bg-white rounded-xl shadow-xl w-full max-w-lg p-6">
        <h2 class="text-lg font-semibold text-slate-900 mb-4">Nieuwe crediteur</h2>
        <div class="grid grid-cols-2 gap-4">
          <div class="col-span-2"><label class="block text-sm font-medium text-slate-700 mb-1">Leverancier</label><input type="text" class="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm focus:ring-2 focus:ring-primary-500" /></div>
          <div><label class="block text-sm font-medium text-slate-700 mb-1">Categorie</label><select class="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm"><option>Software</option><option>Transport</option><option>Kantoor</option><option>Marketing</option><option>Telefoon</option></select></div>
          <div><label class="block text-sm font-medium text-slate-700 mb-1">E-mail</label><input type="email" class="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm focus:ring-2 focus:ring-primary-500" /></div>
          <div><label class="block text-sm font-medium text-slate-700 mb-1">IBAN</label><input type="text" class="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm focus:ring-2 focus:ring-primary-500" /></div>
          <div><label class="block text-sm font-medium text-slate-700 mb-1">Betaaltermijn</label><input type="number" value="30" class="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm focus:ring-2 focus:ring-primary-500" /></div>
        </div>
        <div class="flex justify-end gap-3 mt-6">
          <button @click="showModal = false" class="px-4 py-2 text-sm font-medium text-slate-700">Annuleren</button>
          <button @click="showModal = false" class="bg-primary-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-primary-700">Opslaan</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const ws = useWorkspaceStore()
const showModal = ref(false)
const selectedCreditor = ref<any>(null)

function catColor(c: string) {
  const m: Record<string,string> = { Software: 'bg-purple-100 text-purple-700', Transport: 'bg-blue-100 text-blue-700', Kantoor: 'bg-slate-100 text-slate-700', Marketing: 'bg-pink-100 text-pink-700', Telefoon: 'bg-cyan-100 text-cyan-700' }
  return m[c] || 'bg-slate-100 text-slate-700'
}

const creditors = computed(() => ws.creditors)

const creditorExpenses = computed(() => {
  if (!selectedCreditor.value) return []
  return ws.expenses.filter(exp => exp.supplierId === selectedCreditor.value.id)
})

function formatCurrency(value: number): string {
  return '€ ' + Math.abs(value).toLocaleString('nl-NL', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}
</script>
