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
        <p class="text-sm text-slate-500">Openstaande facturen</p>
        <p class="text-2xl font-bold text-red-600 mt-1">€ 1.847,99</p>
        <p class="text-xs text-slate-400 mt-1">5 onbetaalde facturen</p>
      </div>
      <div class="bg-white rounded-xl border border-surface-200 shadow-sm p-5">
        <p class="text-sm text-slate-500">Betaald deze maand</p>
        <p class="text-2xl font-bold text-emerald-600 mt-1">€ 3.420,50</p>
        <p class="text-xs text-slate-400 mt-1">12 betalingen verwerkt</p>
      </div>
      <div class="bg-white rounded-xl border border-surface-200 shadow-sm p-5">
        <p class="text-sm text-slate-500">BTW te vorderen</p>
        <p class="text-2xl font-bold text-blue-600 mt-1">€ 2.221,48</p>
        <p class="text-xs text-slate-400 mt-1">Q1 2026 voorbelasting</p>
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
          <tr v-for="c in creditors" :key="c.id" class="hover:bg-surface-50 cursor-pointer" @click="selectedCreditor = c">
            <td class="px-6 py-4">
              <p class="text-sm font-medium text-slate-900">{{ c.name }}</p>
              <p class="text-xs text-slate-500">{{ c.email }}</p>
            </td>
            <td class="px-6 py-4"><span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium" :class="catColor(c.category)">{{ c.category }}</span></td>
            <td class="px-6 py-4 text-sm text-slate-600">{{ c.invoiceCount }}</td>
            <td class="px-6 py-4 text-sm text-right font-medium" :class="c.outstanding > 0 ? 'text-red-600' : 'text-emerald-600'">
              {{ c.outstanding > 0 ? '€ ' + c.outstanding.toLocaleString('nl-NL', {minimumFractionDigits:2}) : 'Voldaan' }}
            </td>
            <td class="px-6 py-4 text-sm text-right font-medium text-slate-900">€ {{ c.totalYear.toLocaleString('nl-NL', {minimumFractionDigits:2}) }}</td>
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
        <div v-for="inv in selectedCreditor.invoices" :key="inv.number" class="flex items-center justify-between py-2 px-3 bg-surface-50 rounded-lg">
          <div class="flex items-center gap-4"><span class="text-sm font-medium text-slate-700">{{ inv.number }}</span><span class="text-sm text-slate-500">{{ inv.date }}</span></div>
          <div class="flex items-center gap-4">
            <span class="text-sm font-medium text-slate-900">€ {{ inv.amount.toLocaleString('nl-NL',{minimumFractionDigits:2}) }}</span>
            <span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium" :class="inv.paid ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700'">{{ inv.paid ? 'Betaald' : 'Open' }}</span>
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
const showModal = ref(false)
const selectedCreditor = ref<any>(null)

function catColor(c: string) {
  const m: Record<string,string> = { Software: 'bg-purple-100 text-purple-700', Transport: 'bg-blue-100 text-blue-700', Kantoor: 'bg-slate-100 text-slate-700', Marketing: 'bg-pink-100 text-pink-700', Telefoon: 'bg-cyan-100 text-cyan-700' }
  return m[c] || 'bg-slate-100 text-slate-700'
}

const creditors = [
  { id: 1, name: 'Google Ireland Ltd', email: 'billing@google.com', category: 'Software', iban: 'IE64IRCE92050112345678', paymentTerm: 30, invoiceCount: 12, outstanding: 12.99, totalYear: 155.88, invoices: [
    { number: 'GINV-2026-03', date: '01 mrt 2026', amount: 12.99, paid: false },
    { number: 'GINV-2026-02', date: '01 feb 2026', amount: 12.99, paid: true },
  ]},
  { id: 2, name: 'NS Groep NV', email: 'facturen@ns.nl', category: 'Transport', iban: 'NL91ABNA0417164300', paymentTerm: 14, invoiceCount: 3, outstanding: 156.80, totalYear: 470.40, invoices: [
    { number: 'NS-2026-Q1', date: '31 mrt 2026', amount: 156.80, paid: false },
    { number: 'NS-2025-Q4', date: '31 dec 2025', amount: 145.60, paid: true },
  ]},
  { id: 3, name: 'Bol.com BV', email: 'factuur@bol.com', category: 'Kantoor', iban: 'NL09INGB0664700610', paymentTerm: 14, invoiceCount: 2, outstanding: 349.00, totalYear: 698.00, invoices: [
    { number: 'BOL-8847201', date: '25 mrt 2026', amount: 349.00, paid: false },
  ]},
  { id: 4, name: 'Facebook Ireland Ltd', email: 'billing@fb.com', category: 'Marketing', iban: 'IE29AIBK93115212345678', paymentTerm: 30, invoiceCount: 6, outstanding: 250.00, totalYear: 1500.00, invoices: [
    { number: 'FB-2026-03', date: '31 mrt 2026', amount: 250.00, paid: false },
    { number: 'FB-2026-02', date: '28 feb 2026', amount: 250.00, paid: true },
  ]},
  { id: 5, name: 'KPN BV', email: 'factuur@kpn.com', category: 'Telefoon', iban: 'NL86INGB0002445588', paymentTerm: 14, invoiceCount: 3, outstanding: 0, totalYear: 135.00, invoices: [
    { number: 'KPN-2026-03', date: '20 mrt 2026', amount: 45.00, paid: true },
  ]},
]
</script>
