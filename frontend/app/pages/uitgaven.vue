<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold text-slate-900">Uitgaven</h1>
      <button @click="showModal = true" class="bg-primary-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-primary-700 flex items-center gap-2">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" /></svg>
        Nieuwe uitgave
      </button>
    </div>

    <!-- Summary -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
      <div class="bg-white rounded-xl border border-surface-200 shadow-sm p-4">
        <p class="text-xs text-slate-500">Totaal uitgaven</p>
        <p class="text-xl font-bold text-slate-900">{{ fc(totalExpenses) }}</p>
      </div>
      <div class="bg-white rounded-xl border border-surface-200 shadow-sm p-4">
        <p class="text-xs text-slate-500">BTW te vorderen</p>
        <p class="text-xl font-bold text-blue-600">{{ fc(totalBtwVordering) }}</p>
      </div>
      <div class="bg-white rounded-xl border border-surface-200 shadow-sm p-4">
        <p class="text-xs text-slate-500">Geboekt</p>
        <p class="text-xl font-bold text-emerald-600">{{ ws.expenses.filter(e => e.status === 'geboekt').length }}</p>
      </div>
      <div class="bg-white rounded-xl border border-surface-200 shadow-sm p-4">
        <p class="text-xs text-slate-500">Review nodig</p>
        <p class="text-xl font-bold text-amber-600">{{ ws.expenses.filter(e => e.status === 'review').length }}</p>
      </div>
    </div>

    <!-- AI BTW Tips -->
    <div class="bg-gradient-to-r from-primary-50 to-blue-50 border border-primary-200 rounded-xl p-4">
      <div class="flex items-center gap-3 mb-3">
        <span class="text-lg">💡</span>
        <h3 class="text-sm font-semibold text-primary-900">AI BTW Bespaartips</h3>
      </div>
      <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
        <div class="bg-white/80 rounded-lg p-3">
          <p class="text-xs font-semibold text-slate-900">Nog {{ daysUntilEndQ }} dagen in dit kwartaal</p>
          <p class="text-[11px] text-slate-600">Maak geplande kosten nu om BTW voorbelasting te maximaliseren dit kwartaal.</p>
        </div>
        <div class="bg-white/80 rounded-lg p-3">
          <p class="text-xs font-semibold text-slate-900">Investeringsaftrek mogelijk</p>
          <p class="text-[11px] text-slate-600">Bij investering > € 2.801 krijg je tot 28% extra aftrek (KIA). Overweeg aankopen te bundelen.</p>
        </div>
        <div class="bg-white/80 rounded-lg p-3">
          <p class="text-xs font-semibold text-slate-900">Software kosten +23%</p>
          <p class="text-[11px] text-slate-600">3 overlappende tools gedetecteerd. Bespaar ~€ 45/maand door te consolideren.</p>
        </div>
      </div>
    </div>

    <!-- Table -->
    <div class="bg-white rounded-xl border border-surface-200 shadow-sm overflow-hidden">
      <table class="w-full">
        <thead>
          <tr class="text-left text-xs font-medium text-slate-500 uppercase tracking-wider bg-surface-50">
            <th class="px-6 py-3">Datum</th>
            <th class="px-6 py-3">Omschrijving</th>
            <th class="px-6 py-3">Leverancier</th>
            <th class="px-6 py-3">Categorie</th>
            <th class="px-6 py-3 text-right">Bedrag excl.</th>
            <th class="px-6 py-3 text-right">BTW</th>
            <th class="px-6 py-3">Status</th>
            <th class="px-6 py-3">Acties</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-surface-100">
          <tr v-for="exp in ws.expenses" :key="exp.id" class="hover:bg-surface-50">
            <td class="px-6 py-3 text-sm text-slate-600">{{ formatDate(exp.date) }}</td>
            <td class="px-6 py-3 text-sm font-medium text-slate-900">{{ exp.description }}</td>
            <td class="px-6 py-3 text-sm text-slate-600">{{ supplierName(exp.supplierId) }}</td>
            <td class="px-6 py-3"><span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium" :class="catColor(exp.category)">{{ exp.category }}</span></td>
            <td class="px-6 py-3 text-sm text-right font-medium text-slate-900">{{ fc(exp.amount / (1 + exp.btwRate / 100)) }}</td>
            <td class="px-6 py-3 text-sm text-right text-slate-600">{{ fc(exp.amount - exp.amount / (1 + exp.btwRate / 100)) }} ({{ exp.btwRate }}%)</td>
            <td class="px-6 py-3"><span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium" :class="exp.status === 'geboekt' ? 'bg-emerald-100 text-emerald-700' : exp.status === 'review' ? 'bg-amber-100 text-amber-700' : 'bg-slate-100 text-slate-700'">{{ exp.status === 'geboekt' ? 'Geboekt' : exp.status === 'review' ? 'Review' : 'Concept' }}</span></td>
            <td class="px-6 py-3">
              <div class="flex gap-1">
                <button v-if="exp.status === 'review'" @click="ws.updateExpense(exp.id, { status: 'geboekt' })" class="text-xs px-2 py-1 bg-emerald-100 text-emerald-700 rounded hover:bg-emerald-200">Goedkeuren</button>
                <button @click="editExpense(exp)" class="text-slate-400 hover:text-slate-600"><svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" /></svg></button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Add/Edit Modal -->
    <div v-if="showModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50" @click.self="showModal = false">
      <div class="bg-white rounded-xl shadow-xl w-full max-w-lg p-6">
        <h2 class="text-lg font-semibold text-slate-900 mb-4">{{ editingExpense ? 'Uitgave bewerken' : 'Nieuwe uitgave' }}</h2>
        <div class="grid grid-cols-2 gap-4">
          <div class="col-span-2"><label class="block text-sm font-medium text-slate-700 mb-1">Omschrijving</label><input v-model="form.description" type="text" class="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm focus:ring-2 focus:ring-primary-500" /></div>
          <div><label class="block text-sm font-medium text-slate-700 mb-1">Datum</label><input v-model="form.date" type="date" class="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm" /></div>
          <div><label class="block text-sm font-medium text-slate-700 mb-1">Bedrag (incl. BTW)</label><input v-model.number="form.amount" type="number" step="0.01" class="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm" /></div>
          <div><label class="block text-sm font-medium text-slate-700 mb-1">BTW tarief</label><select v-model.number="form.btwRate" class="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm"><option :value="21">21%</option><option :value="9">9%</option><option :value="0">0%</option></select></div>
          <div><label class="block text-sm font-medium text-slate-700 mb-1">Categorie</label><select v-model="form.category" class="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm"><option>Software</option><option>Transport</option><option>Kantoor</option><option>Marketing</option><option>Telefoon</option><option>Huisvesting</option><option>Verzekering</option><option>Overig</option></select></div>
          <div><label class="block text-sm font-medium text-slate-700 mb-1">Leverancier</label><select v-model="form.supplierId" class="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm"><option value="">Geen</option><option v-for="c in ws.creditors" :key="c.id" :value="c.id">{{ c.name }}</option></select></div>
          <div><label class="block text-sm font-medium text-slate-700 mb-1">Bon/factuur</label><input type="file" accept=".pdf,.jpg,.png" class="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm" /></div>
        </div>
        <div class="flex justify-end gap-3 mt-6">
          <button @click="showModal = false" class="px-4 py-2 text-sm font-medium text-slate-700">Annuleren</button>
          <button @click="saveExpense" class="bg-primary-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-primary-700">Opslaan</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const ws = useWorkspaceStore()
const showModal = ref(false)
const editingExpense = ref<string | null>(null)

const form = reactive({ description: '', date: new Date().toISOString().split('T')[0], amount: 0, btwRate: 21, category: 'Overig', supplierId: '' })

const totalExpenses = computed(() => ws.expenses.reduce((s, e) => s + e.amount, 0))
const totalBtwVordering = computed(() => ws.expenses.filter(e => e.status === 'geboekt').reduce((s, e) => s + (e.amount * e.btwRate / (100 + e.btwRate)), 0))
const daysUntilEndQ = computed(() => { const now = new Date(); const endQ = new Date(now.getFullYear(), Math.ceil((now.getMonth() + 1) / 3) * 3, 0); return Math.ceil((endQ.getTime() - now.getTime()) / 86400000) })

function supplierName(id?: string) { return id ? ws.creditors.find(c => c.id === id)?.name || '-' : '-' }
function catColor(c: string) { return { Software: 'bg-purple-100 text-purple-700', Transport: 'bg-blue-100 text-blue-700', Kantoor: 'bg-slate-100 text-slate-700', Marketing: 'bg-pink-100 text-pink-700', Telefoon: 'bg-cyan-100 text-cyan-700', Huisvesting: 'bg-amber-100 text-amber-700' }[c] || 'bg-slate-100 text-slate-700' }
function fc(v: number) { return '€ ' + v.toLocaleString('nl-NL', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }
function formatDate(d: string) { return new Date(d).toLocaleDateString('nl-NL', { day: 'numeric', month: 'short', year: 'numeric' }) }

function editExpense(exp: any) {
  editingExpense.value = exp.id
  Object.assign(form, { description: exp.description, date: exp.date, amount: exp.amount, btwRate: exp.btwRate, category: exp.category, supplierId: exp.supplierId || '' })
  showModal.value = true
}

function saveExpense() {
  if (editingExpense.value) {
    ws.updateExpense(editingExpense.value, { ...form })
  } else {
    ws.addExpense({ id: 'exp' + Date.now(), ...form, status: 'geboekt' })
  }
  showModal.value = false
  editingExpense.value = null
  Object.assign(form, { description: '', date: new Date().toISOString().split('T')[0], amount: 0, btwRate: 21, category: 'Overig', supplierId: '' })
}
</script>
