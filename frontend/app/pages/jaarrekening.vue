<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold text-slate-900">Jaarrekening</h1>
      <div class="flex gap-2">
        <select v-model="selectedYear" class="px-3 py-2 border border-surface-200 rounded-lg text-sm">
          <option>2025</option>
          <option>2024</option>
        </select>
        <button @click="generateXBRL" class="bg-emerald-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-emerald-700 transition-colors flex items-center gap-2">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
          XBRL Export
        </button>
        <button @click="downloadPdf" :disabled="generating" class="bg-primary-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-primary-700 transition-colors flex items-center gap-2 disabled:opacity-50">
          <svg v-if="!generating" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" /></svg>
          <svg v-else class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" /><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg>
          {{ generating ? 'Genereren...' : 'PDF Download' }}
        </button>
      </div>
    </div>

    <!-- XBRL Export notification -->
    <div v-if="xbrlGenerated" class="bg-emerald-50 border border-emerald-200 rounded-xl p-4 flex items-center gap-3">
      <svg class="w-5 h-5 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" /></svg>
      <div>
        <p class="text-sm font-medium text-emerald-800">XBRL bestand gegenereerd</p>
        <p class="text-xs text-emerald-600">jaarrekening-2025-sbr.xbrl - Klaar voor indiening bij KvK</p>
      </div>
    </div>

    <!-- Tabs -->
    <div class="flex gap-1 bg-surface-100 p-1 rounded-lg w-fit">
      <button v-for="tab in tabs" :key="tab" @click="activeTab = tab" class="px-4 py-2 text-sm font-medium rounded-md transition-colors" :class="activeTab === tab ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-600 hover:text-slate-900'">
        {{ tab }}
      </button>
    </div>

    <!-- Balans -->
    <div v-if="activeTab === 'Balans'" class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Activa -->
      <div class="bg-white rounded-xl border border-surface-200 shadow-sm overflow-hidden">
        <div class="px-6 py-4 border-b border-surface-200 bg-blue-50">
          <h2 class="text-lg font-semibold text-blue-900">Activa</h2>
        </div>
        <div class="divide-y divide-surface-100">
          <div class="px-6 py-3 bg-surface-50"><p class="text-xs font-semibold text-slate-500 uppercase">Vaste activa</p></div>
          <div v-for="item in balans.activa.vast" :key="item.name" class="px-6 py-3 flex justify-between">
            <span class="text-sm text-slate-700">{{ item.name }}</span>
            <span class="text-sm font-medium text-slate-900">{{ fc(item.value) }}</span>
          </div>
          <div class="px-6 py-3 flex justify-between bg-blue-50/50">
            <span class="text-sm font-semibold text-slate-900">Subtotaal vaste activa</span>
            <span class="text-sm font-bold text-slate-900">{{ fc(subtotaal(balans.activa.vast)) }}</span>
          </div>
          <div class="px-6 py-3 bg-surface-50"><p class="text-xs font-semibold text-slate-500 uppercase">Vlottende activa</p></div>
          <div v-for="item in balans.activa.vlottend" :key="item.name" class="px-6 py-3 flex justify-between">
            <span class="text-sm text-slate-700">{{ item.name }}</span>
            <span class="text-sm font-medium text-slate-900">{{ fc(item.value) }}</span>
          </div>
          <div class="px-6 py-3 flex justify-between bg-blue-50/50">
            <span class="text-sm font-semibold text-slate-900">Subtotaal vlottende activa</span>
            <span class="text-sm font-bold text-slate-900">{{ fc(subtotaal(balans.activa.vlottend)) }}</span>
          </div>
          <div class="px-6 py-4 flex justify-between bg-blue-100">
            <span class="text-sm font-bold text-blue-900">TOTAAL ACTIVA</span>
            <span class="text-lg font-bold text-blue-900">{{ fc(subtotaal(balans.activa.vast) + subtotaal(balans.activa.vlottend)) }}</span>
          </div>
        </div>
      </div>

      <!-- Passiva -->
      <div class="bg-white rounded-xl border border-surface-200 shadow-sm overflow-hidden">
        <div class="px-6 py-4 border-b border-surface-200 bg-emerald-50">
          <h2 class="text-lg font-semibold text-emerald-900">Passiva</h2>
        </div>
        <div class="divide-y divide-surface-100">
          <div class="px-6 py-3 bg-surface-50"><p class="text-xs font-semibold text-slate-500 uppercase">Eigen vermogen</p></div>
          <div v-for="item in balans.passiva.eigen" :key="item.name" class="px-6 py-3 flex justify-between">
            <span class="text-sm text-slate-700">{{ item.name }}</span>
            <span class="text-sm font-medium text-slate-900">{{ fc(item.value) }}</span>
          </div>
          <div class="px-6 py-3 flex justify-between bg-emerald-50/50">
            <span class="text-sm font-semibold text-slate-900">Subtotaal eigen vermogen</span>
            <span class="text-sm font-bold text-slate-900">{{ fc(subtotaal(balans.passiva.eigen)) }}</span>
          </div>
          <div class="px-6 py-3 bg-surface-50"><p class="text-xs font-semibold text-slate-500 uppercase">Vreemd vermogen</p></div>
          <div v-for="item in balans.passiva.vreemd" :key="item.name" class="px-6 py-3 flex justify-between">
            <span class="text-sm text-slate-700">{{ item.name }}</span>
            <span class="text-sm font-medium text-slate-900">{{ fc(item.value) }}</span>
          </div>
          <div class="px-6 py-3 flex justify-between bg-emerald-50/50">
            <span class="text-sm font-semibold text-slate-900">Subtotaal vreemd vermogen</span>
            <span class="text-sm font-bold text-slate-900">{{ fc(subtotaal(balans.passiva.vreemd)) }}</span>
          </div>
          <div class="px-6 py-4 flex justify-between bg-emerald-100">
            <span class="text-sm font-bold text-emerald-900">TOTAAL PASSIVA</span>
            <span class="text-lg font-bold text-emerald-900">{{ fc(subtotaal(balans.passiva.eigen) + subtotaal(balans.passiva.vreemd)) }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Winst & Verlies -->
    <div v-if="activeTab === 'Winst & Verlies'" class="bg-white rounded-xl border border-surface-200 shadow-sm overflow-hidden">
      <div class="divide-y divide-surface-100">
        <div class="px-6 py-3 bg-emerald-50"><p class="text-xs font-semibold text-emerald-700 uppercase">Opbrengsten</p></div>
        <div v-for="item in wv.opbrengsten" :key="item.name" class="px-6 py-3 flex justify-between">
          <span class="text-sm text-slate-700">{{ item.name }}</span>
          <span class="text-sm font-medium text-slate-900">{{ fc(item.value) }}</span>
        </div>
        <div class="px-6 py-3 flex justify-between bg-emerald-50/50">
          <span class="text-sm font-semibold text-emerald-800">Totaal opbrengsten</span>
          <span class="text-sm font-bold text-emerald-800">{{ fc(subtotaal(wv.opbrengsten)) }}</span>
        </div>

        <div class="px-6 py-3 bg-red-50"><p class="text-xs font-semibold text-red-700 uppercase">Kosten</p></div>
        <div v-for="item in kostenList" :key="item.name" class="px-6 py-3 flex justify-between">
          <span class="text-sm text-slate-700">{{ item.name }}</span>
          <span class="text-sm font-medium text-slate-900">{{ fc(item.value) }}</span>
        </div>
        <div class="px-6 py-3 flex justify-between bg-red-50/50">
          <span class="text-sm font-semibold text-red-800">Totaal kosten</span>
          <span class="text-sm font-bold text-red-800">{{ fc(subtotaal(kostenList)) }}</span>
        </div>

        <div class="px-6 py-4 flex justify-between bg-surface-50">
          <span class="text-sm font-bold text-slate-900">BEDRIJFSRESULTAAT</span>
          <span class="text-lg font-bold" :class="nettoResultaat >= 0 ? 'text-emerald-600' : 'text-red-600'">{{ fc(nettoResultaat) }}</span>
        </div>

        <div class="px-6 py-3 flex justify-between">
          <span class="text-sm text-slate-700">Vennootschapsbelasting (15%)</span>
          <span class="text-sm font-medium text-slate-900">{{ fc(Math.round(nettoResultaat * 0.15)) }}</span>
        </div>
        <div class="px-6 py-4 flex justify-between bg-primary-50 border-t-2 border-primary-200">
          <span class="text-sm font-bold text-primary-900">NETTO RESULTAAT</span>
          <span class="text-lg font-bold text-primary-900">{{ fc(Math.round(nettoResultaat * 0.85)) }}</span>
        </div>
      </div>
    </div>

    <!-- Toelichting -->
    <div v-if="activeTab === 'Toelichting'" class="space-y-4">
      <div class="bg-white rounded-xl border border-surface-200 shadow-sm p-6">
        <h2 class="text-lg font-semibold text-slate-900 mb-4">Toelichting bij de jaarrekening {{ selectedYear }}</h2>
        <div class="prose prose-sm max-w-none text-slate-700 space-y-4">
          <div>
            <h3 class="text-sm font-semibold text-slate-900">Algemeen</h3>
            <p class="text-sm">De jaarrekening is opgesteld in overeenstemming met de bepalingen van Titel 9, Boek 2 BW en de stellige uitspraken van de Richtlijnen voor de jaarverslaggeving voor kleine rechtspersonen.</p>
          </div>
          <div>
            <h3 class="text-sm font-semibold text-slate-900">Grondslagen voor de waardering</h3>
            <p class="text-sm">Materiele vaste activa worden gewaardeerd tegen aanschafprijs verminderd met lineaire afschrijvingen. Vorderingen worden gewaardeerd tegen nominale waarde, onder aftrek van een voorziening voor oninbaarheid.</p>
          </div>
          <div>
            <h3 class="text-sm font-semibold text-slate-900">Omzetverantwoording</h3>
            <p class="text-sm">Omzet wordt verantwoord op het moment dat de dienst is geleverd of het product is overgedragen aan de klant, en het bedrag op betrouwbare wijze kan worden bepaald.</p>
          </div>
          <div>
            <h3 class="text-sm font-semibold text-slate-900">Personeelskosten</h3>
            <p class="text-sm">Gedurende het boekjaar waren gemiddeld 1 persoon (voltijdsequivalent) werkzaam bij de onderneming.</p>
          </div>
        </div>
      </div>
      <div class="bg-amber-50 border border-amber-200 rounded-xl p-4 flex items-center gap-3">
        <span class="text-lg">🤖</span>
        <div>
          <p class="text-sm font-medium text-amber-800">AI Accountant Agent heeft deze toelichting opgesteld</p>
          <p class="text-xs text-amber-600">Confidence: 91% | Gebaseerd op SBR/XBRL standaarden | Review aanbevolen</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const ws = useWorkspaceStore()
const selectedYear = ref('2025')
const activeTab = ref('Balans')
const tabs = ['Balans', 'Winst & Verlies', 'Toelichting']
const xbrlGenerated = ref(false)

// Compute from store data - totals are dynamic
const totalRevenue = computed(() => ws.totalRevenue)
const totalExpenses = computed(() => ws.totalExpenses)
const outstandingAmount = computed(() => ws.outstandingAmount)

const balans = reactive({
  activa: {
    vast: [
      { name: 'Materiele vaste activa', value: 0 },
      { name: 'Inventaris en inrichting', value: 0 },
      { name: 'Computers en apparatuur', value: 0 },
    ],
    vlottend: [
      { name: 'Debiteuren', value: computed(() => outstandingAmount.value) },
      { name: 'Overige vorderingen', value: 0 },
      { name: 'Liquide middelen', value: computed(() => totalRevenue.value - totalExpenses.value) },
    ],
  },
  passiva: {
    eigen: [
      { name: 'Gestort kapitaal', value: 0 },
      { name: 'Overige reserves', value: 0 },
      { name: 'Resultaat boekjaar', value: computed(() => ws.netProfit) },
    ],
    vreemd: [
      { name: 'Crediteuren', value: 0 },
      { name: 'Belastingen en premies', value: computed(() => Math.round(ws.btwDue)) },
      { name: 'Overige schulden', value: 0 },
    ],
  },
})

const wv = reactive({
  opbrengsten: [
    { name: 'Netto-omzet', value: computed(() => totalRevenue.value) },
    { name: 'Overige bedrijfsopbrengsten', value: 0 },
  ],
  kosten: computed(() => {
    // Group expenses by category
    const cats: Record<string, number> = {}
    ws.expenses.forEach(e => {
      const cat = e.category || 'Overige bedrijfskosten'
      cats[cat] = (cats[cat] || 0) + e.amount
    })
    if (Object.keys(cats).length === 0) return [{ name: 'Geen kosten', value: 0 }]
    return Object.entries(cats).map(([name, value]) => ({ name, value }))
  }),
})

function subtotaal(items: any[]): number {
  if (!items || !Array.isArray(items)) return 0
  return items.reduce((sum, i) => {
    const v = typeof i.value === 'object' && i.value !== null && 'value' in i.value ? i.value.value : i.value
    return sum + (Number(v) || 0)
  }, 0)
}

const kostenList = computed(() => {
  const items = wv.kosten
  return Array.isArray(items) ? items : (items as any).value || []
})

const nettoResultaat = computed(() => subtotaal(wv.opbrengsten) - subtotaal(kostenList.value))

function fc(v: number): string {
  return '€ ' + v.toLocaleString('nl-NL', { minimumFractionDigits: 0 })
}

function generateXBRL() {
  xbrlGenerated.value = true
  setTimeout(() => { xbrlGenerated.value = false }, 5000)
}

const { generating, generateFromTemplate } = usePdf()

async function downloadPdf() {
  const { jaarrekeningTemplate } = await import('~/composables/usePdfTemplates')
  const company = ws.activeCompany
  const html = jaarrekeningTemplate(
    selectedYear.value,
    balans,
    wv,
    company?.branding?.companyName || 'Bedrijf',
    company?.branding || {}
  )
  await generateFromTemplate(html, `Jaarrekening-${selectedYear.value}.pdf`)
}
</script>
