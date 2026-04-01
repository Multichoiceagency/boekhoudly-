<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold text-slate-900">Facturen</h1>
      <button @click="showCreateModal = true" class="bg-primary-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-primary-700 transition-colors flex items-center gap-2">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" /></svg>
        Nieuwe factuur
      </button>
    </div>

    <!-- Summary cards -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
      <div class="bg-white rounded-xl border border-surface-200 shadow-sm p-4">
        <p class="text-xs text-slate-500">Totaal gefactureerd</p>
        <p class="text-xl font-bold text-slate-900">€ {{ totalAll.toLocaleString('nl-NL') }}</p>
      </div>
      <div class="bg-white rounded-xl border border-surface-200 shadow-sm p-4">
        <p class="text-xs text-slate-500">Betaald</p>
        <p class="text-xl font-bold text-emerald-600">€ {{ totalByStatus('Betaald').toLocaleString('nl-NL') }}</p>
      </div>
      <div class="bg-white rounded-xl border border-surface-200 shadow-sm p-4">
        <p class="text-xs text-slate-500">Openstaand</p>
        <p class="text-xl font-bold text-amber-600">€ {{ totalByStatus('Verzonden').toLocaleString('nl-NL') }}</p>
      </div>
      <div class="bg-white rounded-xl border border-surface-200 shadow-sm p-4">
        <p class="text-xs text-slate-500">Verlopen</p>
        <p class="text-xl font-bold text-red-600">€ {{ totalByStatus('Verlopen').toLocaleString('nl-NL') }}</p>
      </div>
    </div>

    <!-- Filter tabs -->
    <div class="flex gap-1 bg-surface-100 p-1 rounded-lg w-fit">
      <button v-for="tab in tabs" :key="tab" @click="activeTab = tab" class="px-4 py-2 text-sm font-medium rounded-md transition-colors" :class="activeTab === tab ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-600 hover:text-slate-900'">
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
            <th class="px-6 py-3 text-right">Bedrag excl.</th>
            <th class="px-6 py-3 text-right">BTW</th>
            <th class="px-6 py-3 text-right">Totaal</th>
            <th class="px-6 py-3">Status</th>
            <th class="px-6 py-3">Acties</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-surface-100">
          <tr v-for="inv in filteredInvoices" :key="inv.number" class="hover:bg-surface-50 cursor-pointer" @click="selectedInvoice = inv">
            <td class="px-6 py-4 text-sm font-medium text-primary-600">{{ inv.number }}</td>
            <td class="px-6 py-4 text-sm text-slate-900">{{ inv.client }}</td>
            <td class="px-6 py-4 text-sm text-slate-600">{{ inv.date }}</td>
            <td class="px-6 py-4 text-sm text-right text-slate-900">€ {{ inv.amount.toLocaleString('nl-NL') }}</td>
            <td class="px-6 py-4 text-sm text-right text-slate-600">€ {{ Math.round(inv.amount * 0.21).toLocaleString('nl-NL') }}</td>
            <td class="px-6 py-4 text-sm text-right font-medium text-slate-900">€ {{ Math.round(inv.amount * 1.21).toLocaleString('nl-NL') }}</td>
            <td class="px-6 py-4">
              <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium" :class="statusColor(inv.status)">{{ inv.status }}</span>
            </td>
            <td class="px-6 py-4">
              <div class="flex gap-2">
                <button @click.stop="selectedInvoice = inv" class="text-slate-400 hover:text-primary-600" title="Bekijk">
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" /></svg>
                </button>
                <button @click.stop class="text-slate-400 hover:text-slate-600" title="Download PDF">
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
                </button>
                <button v-if="inv.status === 'Verlopen'" @click.stop class="text-slate-400 hover:text-amber-600" title="Herinnering sturen">
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" /></svg>
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Invoice Detail -->
    <div v-if="selectedInvoice" class="bg-white rounded-xl border border-surface-200 shadow-sm p-6">
      <div class="flex items-center justify-between mb-6">
        <div>
          <h2 class="text-lg font-semibold text-slate-900">{{ selectedInvoice.number }}</h2>
          <p class="text-sm text-slate-500">{{ selectedInvoice.client }}</p>
        </div>
        <button @click="selectedInvoice = null" class="text-slate-400 hover:text-slate-600">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
        </button>
      </div>
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm mb-6">
        <div><p class="text-slate-500">Factuurdatum</p><p class="font-medium">{{ selectedInvoice.date }}</p></div>
        <div><p class="text-slate-500">Vervaldatum</p><p class="font-medium">{{ selectedInvoice.dueDate }}</p></div>
        <div><p class="text-slate-500">Status</p><span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium" :class="statusColor(selectedInvoice.status)">{{ selectedInvoice.status }}</span></div>
        <div><p class="text-slate-500">Betaalmethode</p><p class="font-medium">Bankoverschrijving</p></div>
      </div>
      <h3 class="text-sm font-semibold text-slate-700 mb-3">Regels</h3>
      <table class="w-full text-sm mb-4">
        <thead><tr class="text-left text-xs text-slate-500 uppercase"><th class="py-2">Omschrijving</th><th class="py-2 text-right">Aantal</th><th class="py-2 text-right">Prijs</th><th class="py-2 text-right">BTW</th><th class="py-2 text-right">Totaal</th></tr></thead>
        <tbody class="divide-y divide-surface-100">
          <tr v-for="(line, i) in selectedInvoice.lines" :key="i">
            <td class="py-2 text-slate-700">{{ line.desc }}</td>
            <td class="py-2 text-right text-slate-600">{{ line.qty }}</td>
            <td class="py-2 text-right text-slate-600">€ {{ line.price.toLocaleString('nl-NL') }}</td>
            <td class="py-2 text-right text-slate-600">21%</td>
            <td class="py-2 text-right font-medium text-slate-900">€ {{ (line.qty * line.price).toLocaleString('nl-NL') }}</td>
          </tr>
        </tbody>
      </table>
      <div class="border-t border-surface-200 pt-3 space-y-1 text-sm text-right">
        <div class="flex justify-end gap-8"><span class="text-slate-500">Subtotaal:</span><span class="font-medium">€ {{ selectedInvoice.amount.toLocaleString('nl-NL') }}</span></div>
        <div class="flex justify-end gap-8"><span class="text-slate-500">BTW 21%:</span><span class="font-medium">€ {{ Math.round(selectedInvoice.amount * 0.21).toLocaleString('nl-NL') }}</span></div>
        <div class="flex justify-end gap-8 text-base"><span class="font-semibold">Totaal:</span><span class="font-bold text-primary-600">€ {{ Math.round(selectedInvoice.amount * 1.21).toLocaleString('nl-NL') }}</span></div>
      </div>
    </div>

    <!-- Create Modal -->
    <div v-if="showCreateModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50" @click.self="showCreateModal = false">
      <div class="bg-white rounded-xl shadow-xl w-full max-w-2xl p-6 max-h-[90vh] overflow-y-auto">
        <h2 class="text-lg font-semibold text-slate-900 mb-4">Nieuwe factuur aanmaken</h2>
        <div class="grid grid-cols-2 gap-4 mb-6">
          <div><label class="block text-sm font-medium text-slate-700 mb-1">Klant</label><select class="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm"><option>Bakkerij de Vries BV</option><option>WebDesign Studio Amsterdam</option><option>Groene Hart Catering</option><option>TechStart Nederland BV</option></select></div>
          <div><label class="block text-sm font-medium text-slate-700 mb-1">Factuurdatum</label><input type="date" class="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm" /></div>
          <div><label class="block text-sm font-medium text-slate-700 mb-1">Vervaldatum</label><input type="date" class="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm" /></div>
          <div><label class="block text-sm font-medium text-slate-700 mb-1">Referentie</label><input type="text" placeholder="PO-nummer / referentie" class="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm" /></div>
        </div>
        <h3 class="text-sm font-semibold text-slate-700 mb-2">Factuurregels</h3>
        <div class="space-y-2 mb-4">
          <div v-for="(line, i) in newInvoiceLines" :key="i" class="grid grid-cols-12 gap-2 items-end">
            <div class="col-span-5"><input v-model="line.desc" type="text" placeholder="Omschrijving" class="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm" /></div>
            <div class="col-span-2"><input v-model.number="line.qty" type="number" placeholder="Aantal" class="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm" /></div>
            <div class="col-span-2"><input v-model.number="line.price" type="number" placeholder="Prijs" class="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm" /></div>
            <div class="col-span-2 text-sm font-medium text-right text-slate-900 py-2">€ {{ (line.qty * line.price).toLocaleString('nl-NL') }}</div>
            <div class="col-span-1"><button @click="newInvoiceLines.splice(i, 1)" class="text-red-400 hover:text-red-600 p-2"><svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg></button></div>
          </div>
        </div>
        <button @click="newInvoiceLines.push({desc:'',qty:1,price:0})" class="text-sm text-primary-600 hover:text-primary-700 font-medium">+ Regel toevoegen</button>
        <div class="flex justify-end gap-3 mt-6 pt-4 border-t border-surface-200">
          <button @click="showCreateModal = false" class="px-4 py-2 text-sm font-medium text-slate-700">Annuleren</button>
          <button @click="showCreateModal = false" class="bg-slate-200 text-slate-700 px-4 py-2 rounded-lg text-sm font-medium hover:bg-slate-300">Concept opslaan</button>
          <button @click="showCreateModal = false" class="bg-primary-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-primary-700">Verstuur factuur</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const activeTab = ref('Alle')
const tabs = ['Alle', 'Verzonden', 'Betaald', 'Verlopen']
const showCreateModal = ref(false)
const selectedInvoice = ref<any>(null)
const newInvoiceLines = ref([{ desc: '', qty: 1, price: 0 }])

const invoices = [
  { number: 'INV-2026-042', client: 'Bakkerij de Vries BV', date: '28 mrt 2026', dueDate: '27 apr 2026', amount: 2450, status: 'Betaald', lines: [{ desc: 'Website redesign', qty: 1, price: 1800 }, { desc: 'SEO optimalisatie', qty: 1, price: 650 }] },
  { number: 'INV-2026-041', client: 'WebDesign Studio Amsterdam', date: '25 mrt 2026', dueDate: '8 apr 2026', amount: 3800, status: 'Verzonden', lines: [{ desc: 'Mobile app development - fase 1', qty: 40, price: 95 }] },
  { number: 'INV-2026-040', client: 'Groene Hart Catering', date: '20 mrt 2026', dueDate: '19 apr 2026', amount: 1275, status: 'Verzonden', lines: [{ desc: 'Webshop onderhoud maart', qty: 15, price: 85 }] },
  { number: 'INV-2026-039', client: 'TechStart Nederland BV', date: '15 mrt 2026', dueDate: '14 apr 2026', amount: 5600, status: 'Verlopen', lines: [{ desc: 'Platform development sprint 4', qty: 56, price: 100 }] },
  { number: 'INV-2026-038', client: 'Van den Berg Consultancy', date: '10 mrt 2026', dueDate: '24 mrt 2026', amount: 890, status: 'Betaald', lines: [{ desc: 'Consulting sessie', qty: 2, price: 445 }] },
]

const filteredInvoices = computed(() => {
  if (activeTab.value === 'Alle') return invoices
  return invoices.filter((i) => i.status === activeTab.value)
})

const totalAll = computed(() => invoices.reduce((s, i) => s + i.amount, 0))
function totalByStatus(status: string) { return invoices.filter((i) => i.status === status).reduce((s, i) => s + i.amount, 0) }

function statusColor(status: string) {
  return { 'bg-emerald-100 text-emerald-700': status === 'Betaald', 'bg-amber-100 text-amber-700': status === 'Verzonden', 'bg-red-100 text-red-700': status === 'Verlopen' }[status] || ''
}
</script>
