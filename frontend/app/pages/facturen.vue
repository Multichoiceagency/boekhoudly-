<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold text-slate-900">Facturen</h1>
      <div class="flex gap-2">
        <button @click="showOfferteModal = true" class="border border-surface-300 text-slate-700 px-4 py-2 rounded-lg text-sm font-medium hover:bg-surface-50 flex items-center gap-2">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" /></svg>
          Nieuwe offerte
        </button>
        <button @click="openCreateModal" class="bg-primary-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-primary-700 flex items-center gap-2">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" /></svg>
          Nieuwe factuur
        </button>
      </div>
    </div>

    <!-- Summary -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
      <div class="bg-white rounded-xl border border-surface-200 shadow-sm p-4">
        <p class="text-xs text-slate-500">Totaal gefactureerd</p>
        <p class="text-xl font-bold text-slate-900">{{ fc(totalAll) }}</p>
      </div>
      <div class="bg-white rounded-xl border border-surface-200 shadow-sm p-4">
        <p class="text-xs text-slate-500">Betaald</p>
        <p class="text-xl font-bold text-emerald-600">{{ fc(totalByStatus('betaald')) }}</p>
      </div>
      <div class="bg-white rounded-xl border border-surface-200 shadow-sm p-4">
        <p class="text-xs text-slate-500">Openstaand</p>
        <p class="text-xl font-bold text-amber-600">{{ fc(totalByStatus('verzonden')) }}</p>
      </div>
      <div class="bg-white rounded-xl border border-surface-200 shadow-sm p-4">
        <p class="text-xs text-slate-500">Verlopen</p>
        <p class="text-xl font-bold text-red-600">{{ fc(totalByStatus('verlopen')) }}</p>
      </div>
    </div>

    <!-- Tabs -->
    <div class="flex gap-1 bg-surface-100 p-1 rounded-lg w-fit">
      <button v-for="tab in tabs" :key="tab.key" @click="activeTab = tab.key" class="px-4 py-2 text-sm font-medium rounded-md transition-colors" :class="activeTab === tab.key ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-600 hover:text-slate-900'">
        {{ tab.label }} ({{ tab.key === 'alle' ? ws.invoices.length : ws.invoices.filter(i => i.status === tab.key).length }})
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
            <th class="px-6 py-3 text-right">Subtotaal</th>
            <th class="px-6 py-3 text-right">BTW</th>
            <th class="px-6 py-3 text-right">Totaal</th>
            <th class="px-6 py-3">Status</th>
            <th class="px-6 py-3">Acties</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-surface-100">
          <tr v-for="inv in filteredInvoices" :key="inv.id" class="hover:bg-surface-50 cursor-pointer" @click="selectedInvoice = inv">
            <td class="px-6 py-4 text-sm font-medium text-primary-600">{{ inv.number }}</td>
            <td class="px-6 py-4 text-sm text-slate-900">{{ inv.client }}</td>
            <td class="px-6 py-4 text-sm text-slate-600">{{ formatDate(inv.date) }}</td>
            <td class="px-6 py-4 text-sm text-right text-slate-900">{{ fc(ws.invoiceTotal(inv)) }}</td>
            <td class="px-6 py-4 text-sm text-right text-slate-600">{{ fc(ws.invoiceTotalIncBtw(inv) - ws.invoiceTotal(inv)) }}</td>
            <td class="px-6 py-4 text-sm text-right font-medium text-slate-900">{{ fc(ws.invoiceTotalIncBtw(inv)) }}</td>
            <td class="px-6 py-4"><span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium" :class="statusColor(inv.status)">{{ statusLabel(inv.status) }}</span></td>
            <td class="px-6 py-4">
              <div class="flex gap-2">
                <button @click.stop="selectedInvoice = inv" class="text-slate-400 hover:text-primary-600" title="Bekijk"><svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" /></svg></button>
                <button @click.stop="duplicateInvoice(inv)" class="text-slate-400 hover:text-slate-600" title="Dupliceer"><svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg></button>
                <button v-if="inv.status === 'verzonden'" @click.stop="markPaid(inv)" class="text-slate-400 hover:text-emerald-600" title="Markeer betaald"><svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg></button>
                <button v-if="inv.status === 'verlopen'" @click.stop="sendReminder(inv)" class="text-slate-400 hover:text-amber-600" title="Herinnering"><svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" /></svg></button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Detail panel (PDF-like preview with branding) -->
    <div v-if="selectedInvoice" class="bg-white rounded-xl border border-surface-200 shadow-sm overflow-hidden">
      <div class="px-6 py-4 border-b border-surface-200 flex items-center justify-between">
        <h2 class="text-lg font-semibold text-slate-900">{{ selectedInvoice.number }}</h2>
        <div class="flex gap-2">
          <button @click="printInvoice" class="border border-surface-300 text-slate-700 px-3 py-1.5 rounded-lg text-xs font-medium hover:bg-surface-50">PDF Download</button>
          <button @click="selectedInvoice = null" class="text-slate-400 hover:text-slate-600"><svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg></button>
        </div>
      </div>
      <!-- Factuur preview met bedrijfsbranding -->
      <div class="p-8" :style="{ borderTop: '4px solid ' + branding.primaryColor }">
        <div class="flex justify-between mb-8">
          <div>
            <div v-if="branding.logo" class="w-32 h-12 bg-surface-100 rounded flex items-center justify-center mb-2"><img :src="branding.logo" class="max-h-full" /></div>
            <p class="text-lg font-bold" :style="{ color: branding.primaryColor }">{{ branding.companyName }}</p>
            <p class="text-xs text-slate-500">{{ branding.address }}</p>
            <p class="text-xs text-slate-500">{{ branding.postcode }} {{ branding.city }}</p>
            <p class="text-xs text-slate-500">KvK: {{ branding.kvk }} | BTW: {{ branding.btw }}</p>
          </div>
          <div class="text-right">
            <h3 class="text-2xl font-bold text-slate-900">FACTUUR</h3>
            <p class="text-sm text-slate-600 mt-2">{{ selectedInvoice.number }}</p>
            <p class="text-sm text-slate-600">Datum: {{ formatDate(selectedInvoice.date) }}</p>
            <p class="text-sm text-slate-600">Vervaldatum: {{ formatDate(selectedInvoice.dueDate) }}</p>
          </div>
        </div>
        <div class="mb-6 p-4 bg-surface-50 rounded-lg">
          <p class="text-xs text-slate-500 uppercase font-medium">Factuur aan</p>
          <p class="text-sm font-semibold text-slate-900 mt-1">{{ selectedInvoice.client }}</p>
          <p v-if="clientDebtor" class="text-xs text-slate-500">{{ clientDebtor.address }}, {{ clientDebtor.city }}</p>
          <p v-if="clientDebtor" class="text-xs text-slate-500">KvK: {{ clientDebtor.kvk }}</p>
        </div>
        <table class="w-full text-sm mb-6">
          <thead><tr class="border-b-2" :style="{ borderColor: branding.primaryColor }"><th class="py-2 text-left">Omschrijving</th><th class="py-2 text-right">Aantal</th><th class="py-2 text-right">Prijs</th><th class="py-2 text-right">BTW</th><th class="py-2 text-right">Totaal</th></tr></thead>
          <tbody>
            <tr v-for="(line, i) in selectedInvoice.lines" :key="i" class="border-b border-surface-100">
              <td class="py-2 text-slate-700">{{ line.desc }}</td>
              <td class="py-2 text-right text-slate-600">{{ line.qty }}</td>
              <td class="py-2 text-right text-slate-600">{{ fc(line.price) }}</td>
              <td class="py-2 text-right text-slate-600">{{ line.btwRate }}%</td>
              <td class="py-2 text-right font-medium text-slate-900">{{ fc(line.qty * line.price) }}</td>
            </tr>
          </tbody>
        </table>
        <div class="flex justify-end">
          <div class="w-64 space-y-1 text-sm">
            <div class="flex justify-between"><span class="text-slate-500">Subtotaal</span><span class="font-medium">{{ fc(ws.invoiceTotal(selectedInvoice)) }}</span></div>
            <div class="flex justify-between"><span class="text-slate-500">BTW</span><span class="font-medium">{{ fc(ws.invoiceTotalIncBtw(selectedInvoice) - ws.invoiceTotal(selectedInvoice)) }}</span></div>
            <div class="flex justify-between pt-2 border-t-2 text-base" :style="{ borderColor: branding.primaryColor }">
              <span class="font-bold">Totaal</span>
              <span class="font-bold" :style="{ color: branding.primaryColor }">{{ fc(ws.invoiceTotalIncBtw(selectedInvoice)) }}</span>
            </div>
          </div>
        </div>
        <div class="mt-8 pt-4 border-t border-surface-200 text-xs text-slate-400">
          <p>Betaling binnen {{ clientDebtor?.paymentTerm || 30 }} dagen op {{ branding.iban }} t.n.v. {{ branding.companyName }}</p>
          <p>{{ branding.email }} | {{ branding.phone }} | {{ branding.website }}</p>
        </div>
      </div>
    </div>

    <!-- Create Invoice Modal -->
    <div v-if="showCreateModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50" @click.self="showCreateModal = false">
      <div class="bg-white rounded-xl shadow-xl w-full max-w-2xl p-6 max-h-[90vh] overflow-y-auto">
        <h2 class="text-lg font-semibold text-slate-900 mb-4">{{ editMode ? 'Factuur bewerken' : 'Nieuwe factuur' }}</h2>
        <div class="grid grid-cols-2 gap-4 mb-6">
          <div>
            <label class="block text-sm font-medium text-slate-700 mb-1">Klant</label>
            <select v-model="newInvoice.clientId" @change="onClientChange" class="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm">
              <option value="">Selecteer klant...</option>
              <option v-for="d in ws.debtors" :key="d.id" :value="d.id">{{ d.name }}</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-slate-700 mb-1">Factuurnummer</label>
            <input type="text" v-model="newInvoice.number" class="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm" />
          </div>
          <div>
            <label class="block text-sm font-medium text-slate-700 mb-1">Factuurdatum</label>
            <input type="date" v-model="newInvoice.date" class="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm" />
          </div>
          <div>
            <label class="block text-sm font-medium text-slate-700 mb-1">Vervaldatum</label>
            <input type="date" v-model="newInvoice.dueDate" class="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm" />
          </div>
        </div>

        <h3 class="text-sm font-semibold text-slate-700 mb-2">Factuurregels</h3>
        <div class="space-y-2 mb-4">
          <div v-for="(line, i) in newInvoice.lines" :key="i" class="grid grid-cols-12 gap-2 items-end">
            <div class="col-span-4"><input v-model="line.desc" type="text" placeholder="Omschrijving" class="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm" /></div>
            <div class="col-span-2"><input v-model.number="line.qty" type="number" min="1" placeholder="Aantal" class="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm" /></div>
            <div class="col-span-2"><input v-model.number="line.price" type="number" step="0.01" placeholder="Prijs" class="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm" /></div>
            <div class="col-span-2">
              <select v-model.number="line.btwRate" class="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm">
                <option :value="21">21%</option><option :value="9">9%</option><option :value="0">0%</option>
              </select>
            </div>
            <div class="col-span-1 text-sm font-medium text-right py-2">{{ fc(line.qty * line.price) }}</div>
            <div class="col-span-1"><button @click="newInvoice.lines.splice(i, 1)" class="text-red-400 hover:text-red-600 p-2"><svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg></button></div>
          </div>
        </div>
        <button @click="newInvoice.lines.push({ desc: '', qty: 1, price: 0, btwRate: 21 })" class="text-sm text-primary-600 hover:text-primary-700 font-medium mb-4">+ Regel toevoegen</button>

        <!-- Totals -->
        <div class="flex justify-end mb-6">
          <div class="w-64 space-y-1 text-sm border-t border-surface-200 pt-2">
            <div class="flex justify-between"><span class="text-slate-500">Subtotaal</span><span class="font-medium">{{ fc(newInvoiceSubtotal) }}</span></div>
            <div class="flex justify-between"><span class="text-slate-500">BTW</span><span class="font-medium">{{ fc(newInvoiceBtw) }}</span></div>
            <div class="flex justify-between font-bold text-base"><span>Totaal</span><span class="text-primary-600">{{ fc(newInvoiceSubtotal + newInvoiceBtw) }}</span></div>
          </div>
        </div>

        <div class="flex justify-end gap-3 pt-4 border-t border-surface-200">
          <button @click="showCreateModal = false" class="px-4 py-2 text-sm font-medium text-slate-700">Annuleren</button>
          <button @click="saveInvoice('concept')" class="bg-slate-200 text-slate-700 px-4 py-2 rounded-lg text-sm font-medium hover:bg-slate-300">Concept opslaan</button>
          <button @click="saveInvoice('verzonden')" class="bg-primary-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-primary-700">Verstuur factuur</button>
        </div>
      </div>
    </div>

    <!-- Offerte Modal (simplified) -->
    <div v-if="showOfferteModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50" @click.self="showOfferteModal = false">
      <div class="bg-white rounded-xl shadow-xl w-full max-w-2xl p-6">
        <h2 class="text-lg font-semibold text-slate-900 mb-4">Nieuwe offerte</h2>
        <p class="text-sm text-slate-600 mb-4">Maak een offerte aan die later omgezet kan worden naar een factuur.</p>
        <div class="grid grid-cols-2 gap-4 mb-4">
          <div><label class="block text-sm font-medium text-slate-700 mb-1">Klant</label><select class="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm"><option value="">Selecteer...</option><option v-for="d in ws.debtors" :key="d.id" :value="d.id">{{ d.name }}</option></select></div>
          <div><label class="block text-sm font-medium text-slate-700 mb-1">Geldig tot</label><input type="date" class="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm" /></div>
          <div class="col-span-2"><label class="block text-sm font-medium text-slate-700 mb-1">Omschrijving</label><textarea rows="3" class="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm" placeholder="Offerte omschrijving..."></textarea></div>
        </div>
        <div class="flex justify-end gap-3"><button @click="showOfferteModal = false" class="px-4 py-2 text-sm text-slate-700">Annuleren</button><button @click="showOfferteModal = false" class="bg-primary-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-primary-700">Offerte aanmaken</button></div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const ws = useWorkspaceStore()

const activeTab = ref('alle')
const tabs = [{ key: 'alle', label: 'Alle' }, { key: 'verzonden', label: 'Verzonden' }, { key: 'betaald', label: 'Betaald' }, { key: 'verlopen', label: 'Verlopen' }]
const showCreateModal = ref(false)
const showOfferteModal = ref(false)
const selectedInvoice = ref<any>(null)
const editMode = ref(false)

const newInvoice = reactive({
  clientId: '',
  client: '',
  number: '',
  date: new Date().toISOString().split('T')[0],
  dueDate: '',
  lines: [{ desc: '', qty: 1, price: 0, btwRate: 21 }] as { desc: string; qty: number; price: number; btwRate: number }[],
})

const branding = computed(() => ws.activeCompany.branding)

const clientDebtor = computed(() => {
  if (!selectedInvoice.value) return null
  return ws.debtors.find(d => d.id === selectedInvoice.value.clientId)
})

const filteredInvoices = computed(() => {
  if (activeTab.value === 'alle') return ws.invoices
  return ws.invoices.filter(i => i.status === activeTab.value)
})

const totalAll = computed(() => ws.invoices.reduce((s, i) => s + ws.invoiceTotal(i), 0))
function totalByStatus(status: string) { return ws.invoices.filter(i => i.status === status).reduce((s, i) => s + ws.invoiceTotal(i), 0) }

const newInvoiceSubtotal = computed(() => newInvoice.lines.reduce((s, l) => s + l.qty * l.price, 0))
const newInvoiceBtw = computed(() => newInvoice.lines.reduce((s, l) => s + l.qty * l.price * l.btwRate / 100, 0))

function openCreateModal() {
  editMode.value = false
  newInvoice.clientId = ''
  newInvoice.client = ''
  newInvoice.number = ws.nextInvoiceNumber
  newInvoice.date = new Date().toISOString().split('T')[0]
  newInvoice.dueDate = ''
  newInvoice.lines = [{ desc: '', qty: 1, price: 0, btwRate: 21 }]
  showCreateModal.value = true
}

function onClientChange() {
  const debtor = ws.debtors.find(d => d.id === newInvoice.clientId)
  if (debtor) {
    newInvoice.client = debtor.name
    const due = new Date()
    due.setDate(due.getDate() + debtor.paymentTerm)
    newInvoice.dueDate = due.toISOString().split('T')[0]
  }
}

function saveInvoice(status: 'concept' | 'verzonden') {
  ws.addInvoice({
    id: 'inv' + Date.now(),
    number: newInvoice.number,
    client: newInvoice.client,
    clientId: newInvoice.clientId,
    date: newInvoice.date,
    dueDate: newInvoice.dueDate,
    lines: [...newInvoice.lines],
    status,
  })
  showCreateModal.value = false
}

function markPaid(inv: any) {
  ws.updateInvoice(inv.id, { status: 'betaald', paidDate: new Date().toISOString().split('T')[0] })
}

function sendReminder(inv: any) {
  alert(`Herinnering verstuurd voor ${inv.number} aan ${inv.client}`)
}

function duplicateInvoice(inv: any) {
  newInvoice.clientId = inv.clientId
  newInvoice.client = inv.client
  newInvoice.number = ws.nextInvoiceNumber
  newInvoice.date = new Date().toISOString().split('T')[0]
  newInvoice.lines = inv.lines.map((l: any) => ({ ...l }))
  onClientChange()
  editMode.value = false
  showCreateModal.value = true
}

function printInvoice() { window.print() }

function fc(v: number) { return '€ ' + v.toLocaleString('nl-NL', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }
function formatDate(d: string) { return new Date(d).toLocaleDateString('nl-NL', { day: 'numeric', month: 'short', year: 'numeric' }) }
function statusColor(s: string) { return { betaald: 'bg-emerald-100 text-emerald-700', verzonden: 'bg-amber-100 text-amber-700', verlopen: 'bg-red-100 text-red-700', concept: 'bg-slate-100 text-slate-700' }[s] || '' }
function statusLabel(s: string) { return { betaald: 'Betaald', verzonden: 'Verzonden', verlopen: 'Verlopen', concept: 'Concept' }[s] || s }
</script>
