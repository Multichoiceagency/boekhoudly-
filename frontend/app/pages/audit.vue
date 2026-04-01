<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold text-slate-900">Audit Rapport</h1>
      <div class="flex gap-2">
        <select v-model="selectedYear" class="px-3 py-2 border border-surface-200 rounded-lg text-sm">
          <option>2025</option>
          <option>2024</option>
        </select>
        <button @click="runAudit" class="bg-teal-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-teal-700 transition-colors flex items-center gap-2" :disabled="auditing">
          <svg v-if="!auditing" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" /></svg>
          <svg v-else class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" /><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg>
          {{ auditing ? 'Audit uitvoeren...' : 'Audit uitvoeren' }}
        </button>
        <button @click="printAudit" :disabled="generating" class="bg-primary-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-primary-700 transition-colors flex items-center gap-2 disabled:opacity-50">
          <svg v-if="!generating" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" /></svg>
          <svg v-else class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" /><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg>
          {{ generating ? 'Genereren...' : 'PDF Download' }}
        </button>
      </div>
    </div>

    <!-- Audit Score -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
      <div class="bg-white rounded-xl border border-surface-200 shadow-sm p-4">
        <p class="text-xs text-slate-500">Audit Score</p>
        <p class="text-2xl font-bold" :class="auditScore >= 80 ? 'text-emerald-600' : auditScore >= 60 ? 'text-amber-600' : 'text-red-600'">{{ auditScore }}%</p>
        <p class="text-xs mt-1" :class="auditScore >= 80 ? 'text-emerald-500' : auditScore >= 60 ? 'text-amber-500' : 'text-red-500'">{{ auditScore >= 80 ? 'Goed' : auditScore >= 60 ? 'Matig' : 'Onvoldoende' }}</p>
      </div>
      <div class="bg-white rounded-xl border border-surface-200 shadow-sm p-4">
        <p class="text-xs text-slate-500">Gecontroleerde boekingen</p>
        <p class="text-2xl font-bold text-slate-900">{{ auditResults.totalChecked }}</p>
        <p class="text-xs text-slate-400 mt-1">van {{ auditResults.totalTransactions }} totaal</p>
      </div>
      <div class="bg-white rounded-xl border border-surface-200 shadow-sm p-4">
        <p class="text-xs text-slate-500">Bevindingen</p>
        <p class="text-2xl font-bold text-amber-600">{{ auditResults.findings.length }}</p>
        <p class="text-xs text-slate-400 mt-1">{{ auditResults.findings.filter(f => f.severity === 'hoog').length }} hoog risico</p>
      </div>
      <div class="bg-white rounded-xl border border-surface-200 shadow-sm p-4">
        <p class="text-xs text-slate-500">Laatste audit</p>
        <p class="text-2xl font-bold text-slate-900">{{ lastAuditDate }}</p>
        <p class="text-xs text-slate-400 mt-1">{{ lastAuditTime }}</p>
      </div>
    </div>

    <!-- Tabs -->
    <div class="flex gap-1 bg-surface-100 p-1 rounded-lg w-fit">
      <button v-for="tab in tabs" :key="tab" @click="activeTab = tab" class="px-4 py-2 text-sm font-medium rounded-md transition-colors" :class="activeTab === tab ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-600 hover:text-slate-900'">
        {{ tab }}
      </button>
    </div>

    <!-- Overzicht Tab -->
    <div v-if="activeTab === 'Overzicht'" class="space-y-4">
      <!-- Audit Checks -->
      <div class="bg-white rounded-xl border border-surface-200 shadow-sm overflow-hidden">
        <div class="px-6 py-4 border-b border-surface-200">
          <h2 class="text-lg font-semibold text-slate-900">Controle Punten</h2>
        </div>
        <div class="divide-y divide-surface-100">
          <div v-for="check in auditChecks" :key="check.name" class="px-6 py-4 flex items-center justify-between">
            <div class="flex items-center gap-3">
              <div class="w-8 h-8 rounded-full flex items-center justify-center" :class="check.passed ? 'bg-emerald-100' : 'bg-red-100'">
                <svg v-if="check.passed" class="w-4 h-4 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" /></svg>
                <svg v-else class="w-4 h-4 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
              </div>
              <div>
                <p class="text-sm font-medium text-slate-900">{{ check.name }}</p>
                <p class="text-xs text-slate-500">{{ check.description }}</p>
              </div>
            </div>
            <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium" :class="check.passed ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-700'">
              {{ check.passed ? 'Voldoet' : 'Aandacht vereist' }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- Bevindingen Tab -->
    <div v-if="activeTab === 'Bevindingen'" class="space-y-4">
      <div class="bg-white rounded-xl border border-surface-200 shadow-sm overflow-hidden">
        <div class="px-6 py-4 border-b border-surface-200">
          <h2 class="text-lg font-semibold text-slate-900">Bevindingen ({{ auditResults.findings.length }})</h2>
        </div>
        <div class="divide-y divide-surface-100">
          <div v-for="(finding, i) in auditResults.findings" :key="i" class="px-6 py-4">
            <div class="flex items-start gap-3">
              <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium mt-0.5" :class="severityColor(finding.severity)">
                {{ finding.severity }}
              </span>
              <div class="flex-1">
                <p class="text-sm font-medium text-slate-900">{{ finding.title }}</p>
                <p class="text-sm text-slate-600 mt-1">{{ finding.description }}</p>
                <p class="text-xs text-slate-400 mt-2">Categorie: {{ finding.category }} | Referentie: {{ finding.reference }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Jaarrekening Tab -->
    <div v-if="activeTab === 'Jaarrekening'" class="space-y-4">
      <!-- Balans Verificatie -->
      <div class="bg-white rounded-xl border border-surface-200 shadow-sm overflow-hidden">
        <div class="px-6 py-4 border-b border-surface-200 bg-blue-50">
          <h2 class="text-lg font-semibold text-blue-900">Balans Verificatie</h2>
        </div>
        <div class="divide-y divide-surface-100">
          <div class="px-6 py-3 flex justify-between items-center">
            <span class="text-sm text-slate-700">Totaal Activa</span>
            <div class="flex items-center gap-3">
              <span class="text-sm font-medium text-slate-900">{{ fc(balansCheck.activa) }}</span>
              <svg class="w-4 h-4 text-emerald-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" /></svg>
            </div>
          </div>
          <div class="px-6 py-3 flex justify-between items-center">
            <span class="text-sm text-slate-700">Totaal Passiva</span>
            <div class="flex items-center gap-3">
              <span class="text-sm font-medium text-slate-900">{{ fc(balansCheck.passiva) }}</span>
              <svg class="w-4 h-4 text-emerald-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" /></svg>
            </div>
          </div>
          <div class="px-6 py-4 flex justify-between items-center" :class="balansCheck.activa === balansCheck.passiva ? 'bg-emerald-50' : 'bg-red-50'">
            <span class="text-sm font-bold" :class="balansCheck.activa === balansCheck.passiva ? 'text-emerald-900' : 'text-red-900'">
              Balans {{ balansCheck.activa === balansCheck.passiva ? 'klopt' : 'klopt niet' }}
            </span>
            <span class="text-sm font-bold" :class="balansCheck.activa === balansCheck.passiva ? 'text-emerald-900' : 'text-red-900'">
              Verschil: {{ fc(Math.abs(balansCheck.activa - balansCheck.passiva)) }}
            </span>
          </div>
        </div>
      </div>

      <!-- Winst & Verlies Verificatie -->
      <div class="bg-white rounded-xl border border-surface-200 shadow-sm overflow-hidden">
        <div class="px-6 py-4 border-b border-surface-200 bg-emerald-50">
          <h2 class="text-lg font-semibold text-emerald-900">Winst & Verlies Verificatie</h2>
        </div>
        <div class="divide-y divide-surface-100">
          <div class="px-6 py-3 flex justify-between">
            <span class="text-sm text-slate-700">Totaal Opbrengsten</span>
            <span class="text-sm font-medium text-emerald-700">{{ fc(wvCheck.opbrengsten) }}</span>
          </div>
          <div class="px-6 py-3 flex justify-between">
            <span class="text-sm text-slate-700">Totaal Kosten</span>
            <span class="text-sm font-medium text-red-700">{{ fc(wvCheck.kosten) }}</span>
          </div>
          <div class="px-6 py-3 flex justify-between bg-surface-50">
            <span class="text-sm font-bold text-slate-900">Bedrijfsresultaat</span>
            <span class="text-sm font-bold" :class="wvCheck.resultaat >= 0 ? 'text-emerald-600' : 'text-red-600'">{{ fc(wvCheck.resultaat) }}</span>
          </div>
          <div class="px-6 py-3 flex justify-between">
            <span class="text-sm text-slate-700">Vennootschapsbelasting (15%)</span>
            <span class="text-sm font-medium text-slate-900">{{ fc(Math.round(wvCheck.resultaat * 0.15)) }}</span>
          </div>
          <div class="px-6 py-4 flex justify-between bg-primary-50 border-t-2 border-primary-200">
            <span class="text-sm font-bold text-primary-900">Netto Resultaat</span>
            <span class="text-sm font-bold text-primary-900">{{ fc(Math.round(wvCheck.resultaat * 0.85)) }}</span>
          </div>
        </div>
      </div>

      <!-- BTW Controle -->
      <div class="bg-white rounded-xl border border-surface-200 shadow-sm overflow-hidden">
        <div class="px-6 py-4 border-b border-surface-200 bg-purple-50">
          <h2 class="text-lg font-semibold text-purple-900">BTW Controle</h2>
        </div>
        <div class="divide-y divide-surface-100">
          <div class="px-6 py-3 flex justify-between">
            <span class="text-sm text-slate-700">BTW Afgedragen</span>
            <span class="text-sm font-medium text-slate-900">{{ fc(btwCheck.afgedragen) }}</span>
          </div>
          <div class="px-6 py-3 flex justify-between">
            <span class="text-sm text-slate-700">BTW Teruggevorderd</span>
            <span class="text-sm font-medium text-slate-900">{{ fc(btwCheck.teruggevorderd) }}</span>
          </div>
          <div class="px-6 py-3 flex justify-between bg-purple-50/50">
            <span class="text-sm font-bold text-purple-900">Saldo</span>
            <span class="text-sm font-bold text-purple-900">{{ fc(btwCheck.afgedragen - btwCheck.teruggevorderd) }}</span>
          </div>
          <div class="px-6 py-3 flex justify-between items-center">
            <span class="text-sm text-slate-700">Alle BTW-aangiften ingediend</span>
            <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium" :class="btwCheck.alleIngediend ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-700'">
              {{ btwCheck.alleIngediend ? 'Ja' : 'Nee' }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- Audit Trail Tab -->
    <div v-if="activeTab === 'Audit Trail'" class="space-y-4">
      <div class="bg-white rounded-xl border border-surface-200 shadow-sm overflow-hidden">
        <div class="px-6 py-4 border-b border-surface-200">
          <h2 class="text-lg font-semibold text-slate-900">Audit Trail</h2>
        </div>
        <table class="w-full">
          <thead>
            <tr class="text-left text-xs font-medium text-slate-500 uppercase tracking-wider bg-surface-50">
              <th class="px-6 py-3">Datum</th>
              <th class="px-6 py-3">Actie</th>
              <th class="px-6 py-3">Gebruiker</th>
              <th class="px-6 py-3">Details</th>
              <th class="px-6 py-3">Status</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-surface-100">
            <tr v-for="(entry, i) in auditTrail" :key="i" class="hover:bg-surface-50">
              <td class="px-6 py-3 text-sm text-slate-600">{{ entry.date }}</td>
              <td class="px-6 py-3 text-sm font-medium text-slate-900">{{ entry.action }}</td>
              <td class="px-6 py-3 text-sm text-slate-600">{{ entry.user }}</td>
              <td class="px-6 py-3 text-sm text-slate-600">{{ entry.details }}</td>
              <td class="px-6 py-3">
                <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium" :class="entry.status === 'ok' ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700'">
                  {{ entry.status === 'ok' ? 'Akkoord' : 'Review' }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- AI Agent Notice -->
    <div class="bg-amber-50 border border-amber-200 rounded-xl p-4 flex items-center gap-3">
      <svg class="w-5 h-5 text-amber-600 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
      <div>
        <p class="text-sm font-medium text-amber-800">AI Audit Agent heeft deze controle uitgevoerd</p>
        <p class="text-xs text-amber-600">Confidence: 94% | Gebaseerd op RJ-standaarden en fiscale wetgeving | Accountantsreview aanbevolen</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const selectedYear = ref('2025')
const activeTab = ref('Overzicht')
const tabs = ['Overzicht', 'Bevindingen', 'Jaarrekening', 'Audit Trail']
const auditing = ref(false)

const lastAuditDate = ref('28 mrt 2026')
const lastAuditTime = ref('14:32')

const auditScore = computed(() => {
  const passed = auditChecks.filter(c => c.passed).length
  return Math.round((passed / auditChecks.length) * 100)
})

const auditResults = reactive({
  totalChecked: 847,
  totalTransactions: 892,
  findings: [
    { title: 'Ontbrekende factuur bij boeking', description: 'Boeking #B-2025-234 (€ 1.250) heeft geen onderliggende factuur. Onderbouwing toevoegen.', severity: 'hoog', category: 'Documentatie', reference: 'RJ 115.104' },
    { title: 'BTW-tarief afwijking', description: 'Boeking #B-2025-567 gebruikt 21% BTW op wat lijkt op een voedseldienst (normaal 9%).', severity: 'midden', category: 'BTW', reference: 'Wet OB art. 9' },
    { title: 'Dubbele boeking gedetecteerd', description: 'Boeking #B-2025-441 en #B-2025-442 lijken dezelfde uitgave te betreffen (Adobe Creative Cloud, december).', severity: 'hoog', category: 'Boekingen', reference: 'RJ 115.201' },
    { title: 'Afschrijvingstermijn controleren', description: 'Computer apparatuur wordt in 5 jaar afgeschreven, maar de verwachte levensduur is 3 jaar.', severity: 'laag', category: 'Vaste activa', reference: 'RJ 212.405' },
    { title: 'Openstaande factuur ouder dan 90 dagen', description: 'Factuur INV-2025-031 (TechStart Nederland BV) staat 94 dagen open. Voorziening dubieuze debiteuren overwegen.', severity: 'midden', category: 'Debiteuren', reference: 'RJ 222.301' },
    { title: 'Kasbestand niet gereconcilieerd', description: 'Het kasontvangstenbewijs voor maart ontbreekt. Afstemming met bankafschrift nodig.', severity: 'laag', category: 'Liquide middelen', reference: 'RJ 360.104' },
  ],
})

const auditChecks = reactive([
  { name: 'Balans is in evenwicht', description: 'Totaal activa = totaal passiva', passed: true },
  { name: 'Alle facturen onderbouwd', description: 'Elke boeking heeft een onderliggende factuur of bewijs', passed: false },
  { name: 'BTW-aangiften compleet', description: 'Alle kwartaalaangiften zijn tijdig ingediend', passed: true },
  { name: 'Geen dubbele boekingen', description: 'Controle op duplicaten in het grootboek', passed: false },
  { name: 'Afschrijvingen correct', description: 'Afschrijvingstermijnen conform RJ-richtlijnen', passed: true },
  { name: 'Debiteurenbeheer up-to-date', description: 'Geen onverantwoorde oninbare vorderingen', passed: true },
  { name: 'Crediteurensaldi gereconcilieerd', description: 'Openstaande schulden sluiten aan op facturen', passed: true },
  { name: 'Bankreconciliatie uitgevoerd', description: 'Banksaldi aansluiten op het grootboek', passed: true },
  { name: 'Jaarrekening compleet', description: 'Balans, W&V en toelichting zijn opgesteld', passed: true },
  { name: 'Continuiteit gewaarborgd', description: 'Geen signalen van discontinuiteit', passed: true },
])

const balansCheck = reactive({
  activa: 54700,
  passiva: 54700,
})

const wvCheck = reactive({
  opbrengsten: 145700,
  kosten: 129380,
  resultaat: 16320,
})

const btwCheck = reactive({
  afgedragen: 28476,
  teruggevorderd: 4850,
  alleIngediend: true,
})

const auditTrail = [
  { date: '28-03-2026 14:32', action: 'Audit uitgevoerd', user: 'AI Audit Agent', details: 'Volledige jaarcontrole 2025', status: 'ok' },
  { date: '28-03-2026 14:30', action: 'Jaarrekening gegenereerd', user: 'AI Accountant', details: 'Balans + W&V + Toelichting', status: 'ok' },
  { date: '25-03-2026 10:15', action: 'BTW Q4 ingediend', user: 'Admin', details: 'BTW-aangifte Q4 2025', status: 'ok' },
  { date: '20-03-2026 09:00', action: 'Bankreconciliatie', user: 'AI Boekhouder', details: '42 transacties gematcht', status: 'ok' },
  { date: '15-03-2026 16:45', action: 'Factuur aangepast', user: 'Admin', details: 'INV-2025-038 bedrag gecorrigeerd', status: 'review' },
  { date: '10-03-2026 11:20', action: 'Dubbele boeking gemeld', user: 'AI Audit Agent', details: 'B-2025-441 / B-2025-442', status: 'review' },
  { date: '01-03-2026 08:00', action: 'Maandafsluiting', user: 'AI Boekhouder', details: 'Februari 2026 afgesloten', status: 'ok' },
  { date: '28-02-2026 14:00', action: 'Voorziening aangemaakt', user: 'Admin', details: 'Dubieuze debiteuren € 1.250', status: 'ok' },
]

function severityColor(severity: string) {
  return {
    hoog: 'bg-red-100 text-red-700',
    midden: 'bg-amber-100 text-amber-700',
    laag: 'bg-blue-100 text-blue-700',
  }[severity] || 'bg-slate-100 text-slate-700'
}

const ws = useWorkspaceStore()
const { generating, generateFromTemplate } = usePdf()

function fc(v: number): string {
  return '\u20AC ' + v.toLocaleString('nl-NL', { minimumFractionDigits: 0 })
}

function runAudit() {
  auditing.value = true
  setTimeout(() => {
    auditing.value = false
    lastAuditDate.value = new Date().toLocaleDateString('nl-NL', { day: 'numeric', month: 'short', year: 'numeric' })
    lastAuditTime.value = new Date().toLocaleTimeString('nl-NL', { hour: '2-digit', minute: '2-digit' })
  }, 2000)
}

async function printAudit() {
  const { auditTemplate } = await import('~/composables/usePdfTemplates')
  const company = ws.activeCompany
  const html = auditTemplate(
    selectedYear.value,
    company?.branding?.companyName || 'Bedrijf',
    auditScore.value,
    auditChecks,
    auditResults.findings,
    balansCheck,
    wvCheck,
    btwCheck,
    company?.branding || {}
  )
  await generateFromTemplate(html, `Audit-Rapport-${selectedYear.value}.pdf`)
}
</script>
