<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold text-slate-900">BTW Aangiftes</h1>
      <div class="flex gap-2">
        <button @click="generateAangifte" :disabled="generating" class="bg-primary-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-primary-700 transition-colors flex items-center gap-2 disabled:opacity-50">
          <svg v-if="!generating" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" /></svg>
          <svg v-else class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path></svg>
          {{ generating ? 'Genereren...' : 'Genereer aangifte' }}
        </button>
        <button @click="showSubmitModal = true" :disabled="!xmlGenerated" class="bg-emerald-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-emerald-700 transition-colors flex items-center gap-2 disabled:opacity-50">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" /></svg>
          Indienen via Digipoort
        </button>
      </div>
    </div>

    <!-- XML Generated notification -->
    <div v-if="xmlGenerated" class="bg-emerald-50 border border-emerald-200 rounded-xl p-4 flex items-center justify-between">
      <div class="flex items-center gap-3">
        <svg class="w-5 h-5 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" /></svg>
        <div>
          <p class="text-sm font-medium text-emerald-800">XML aangifte gegenereerd</p>
          <p class="text-xs text-emerald-600">btw-aangifte-q1-2026.xml | Gevalideerd tegen OB-schema</p>
        </div>
      </div>
      <button class="text-xs text-emerald-700 font-medium hover:text-emerald-800 border border-emerald-300 px-3 py-1 rounded-lg">Download XML</button>
    </div>

    <!-- Current quarter -->
    <div class="bg-white rounded-xl border border-surface-200 shadow-sm p-6">
      <h2 class="text-lg font-semibold text-slate-900 mb-4">Huidig kwartaal - Q1 2026</h2>
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div>
          <p class="text-sm text-slate-500">BTW ontvangen (omzet)</p>
          <p class="text-2xl font-bold text-slate-900 mt-1">€ 4.832,10</p>
          <p class="text-xs text-slate-400 mt-1">Op basis van 28 facturen</p>
        </div>
        <div>
          <p class="text-sm text-slate-500">BTW betaald (kosten)</p>
          <p class="text-2xl font-bold text-slate-900 mt-1">€ 2.221,48</p>
          <p class="text-xs text-slate-400 mt-1">Op basis van 45 transacties</p>
        </div>
        <div>
          <p class="text-sm text-slate-500">BTW af te dragen</p>
          <p class="text-2xl font-bold text-red-600 mt-1">€ 2.610,62</p>
          <p class="text-xs text-slate-400 mt-1">Deadline: 30 april 2026</p>
        </div>
      </div>

      <!-- Rubrieken breakdown -->
      <div class="mt-6 pt-4 border-t border-surface-200">
        <h3 class="text-sm font-semibold text-slate-700 mb-3">OB Rubrieken</h3>
        <div class="space-y-2 text-sm">
          <div class="flex justify-between py-1"><span class="text-slate-600">1a. Leveringen/diensten belast met hoog tarief</span><span class="font-medium">€ 18.688,10</span></div>
          <div class="flex justify-between py-1"><span class="text-slate-600">1a. Omzetbelasting 21%</span><span class="font-medium">€ 3.924,50</span></div>
          <div class="flex justify-between py-1"><span class="text-slate-600">1b. Leveringen/diensten belast met laag tarief</span><span class="font-medium">€ 9.513,33</span></div>
          <div class="flex justify-between py-1"><span class="text-slate-600">1b. Omzetbelasting 9%</span><span class="font-medium">€ 856,20</span></div>
          <div class="flex justify-between py-1"><span class="text-slate-600">1e. Leveringen/diensten 0%/verlegd</span><span class="font-medium">€ 51,40</span></div>
          <div class="flex justify-between py-1 border-t border-surface-200 pt-2"><span class="text-slate-600 font-medium">5a. Subtotaal</span><span class="font-bold">€ 4.832,10</span></div>
          <div class="flex justify-between py-1"><span class="text-slate-600">5b. Voorbelasting</span><span class="font-medium">€ 2.221,48</span></div>
          <div class="flex justify-between py-2 bg-red-50 rounded-lg px-3 mt-2"><span class="font-semibold text-red-700">5g. Te betalen</span><span class="font-bold text-red-700">€ 2.610,62</span></div>
        </div>
      </div>

      <div class="mt-4 grid grid-cols-3 gap-4">
        <div class="bg-surface-50 rounded-lg p-3">
          <p class="text-xs text-slate-500">21% tarief</p>
          <p class="text-lg font-bold text-slate-900">€ 3.924,50</p>
        </div>
        <div class="bg-surface-50 rounded-lg p-3">
          <p class="text-xs text-slate-500">9% tarief</p>
          <p class="text-lg font-bold text-slate-900">€ 856,20</p>
        </div>
        <div class="bg-surface-50 rounded-lg p-3">
          <p class="text-xs text-slate-500">0% / vrijgesteld</p>
          <p class="text-lg font-bold text-slate-900">€ 51,40</p>
        </div>
      </div>
    </div>

    <!-- Past filings -->
    <div class="bg-white rounded-xl border border-surface-200 shadow-sm overflow-hidden">
      <div class="px-6 py-4 border-b border-surface-200"><h2 class="text-lg font-semibold text-slate-900">Eerdere aangiftes</h2></div>
      <table class="w-full">
        <thead>
          <tr class="text-left text-xs font-medium text-slate-500 uppercase tracking-wider bg-surface-50">
            <th class="px-6 py-3">Periode</th>
            <th class="px-6 py-3 text-right">BTW ontvangen</th>
            <th class="px-6 py-3 text-right">BTW betaald</th>
            <th class="px-6 py-3 text-right">Saldo</th>
            <th class="px-6 py-3">Status</th>
            <th class="px-6 py-3">Acties</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-surface-100">
          <tr v-for="filing in pastFilings" :key="filing.period" class="hover:bg-surface-50">
            <td class="px-6 py-4 text-sm font-medium text-slate-900">{{ filing.period }}</td>
            <td class="px-6 py-4 text-sm text-right text-slate-600">€ {{ filing.collected.toLocaleString('nl-NL', { minimumFractionDigits: 2 }) }}</td>
            <td class="px-6 py-4 text-sm text-right text-slate-600">€ {{ filing.paid.toLocaleString('nl-NL', { minimumFractionDigits: 2 }) }}</td>
            <td class="px-6 py-4 text-sm text-right font-medium" :class="filing.balance > 0 ? 'text-red-600' : 'text-emerald-600'">
              {{ filing.balance > 0 ? '' : '+ ' }}€ {{ Math.abs(filing.balance).toLocaleString('nl-NL', { minimumFractionDigits: 2 }) }}
            </td>
            <td class="px-6 py-4">
              <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium" :class="{ 'bg-emerald-100 text-emerald-700': filing.status === 'Geaccepteerd', 'bg-blue-100 text-blue-700': filing.status === 'Ingediend', 'bg-amber-100 text-amber-700': filing.status === 'Concept' }">
                {{ filing.status }}
              </span>
            </td>
            <td class="px-6 py-4">
              <button class="text-primary-600 hover:text-primary-700 text-sm font-medium">Download</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Submit Modal -->
    <div v-if="showSubmitModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50" @click.self="showSubmitModal = false">
      <div class="bg-white rounded-xl shadow-xl w-full max-w-lg p-6">
        <h2 class="text-lg font-semibold text-slate-900 mb-4">BTW aangifte indienen via Digipoort</h2>
        <div class="bg-amber-50 border border-amber-200 rounded-lg p-4 mb-4">
          <p class="text-sm text-amber-800 font-medium">Let op: Dit dient de aangifte definitief in bij de Belastingdienst.</p>
          <p class="text-xs text-amber-600 mt-1">Periode: Q1 2026 | Bedrag: € 2.610,62</p>
        </div>
        <div class="space-y-3 text-sm">
          <div class="flex items-center gap-2"><svg class="w-4 h-4 text-emerald-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" /></svg><span>XML gevalideerd tegen OB-schema</span></div>
          <div class="flex items-center gap-2"><svg class="w-4 h-4 text-emerald-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" /></svg><span>Alle rubrieken correct ingevuld</span></div>
          <div class="flex items-center gap-2"><svg class="w-4 h-4 text-emerald-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" /></svg><span>BTW-nummer geverifieerd</span></div>
          <div class="flex items-center gap-2"><svg class="w-4 h-4 text-amber-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01" /></svg><span>PKIoverheid certificaat vereist</span></div>
        </div>
        <div class="flex justify-end gap-3 mt-6">
          <button @click="showSubmitModal = false" class="px-4 py-2 text-sm font-medium text-slate-700">Annuleren</button>
          <button @click="submitAangifte" class="bg-emerald-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-emerald-700">Bevestig & Indienen</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const generating = ref(false)
const xmlGenerated = ref(false)
const showSubmitModal = ref(false)

const pastFilings = [
  { period: 'Q4 2025', collected: 5120.00, paid: 2340.50, balance: 2779.50, status: 'Geaccepteerd' },
  { period: 'Q3 2025', collected: 4890.00, paid: 3210.00, balance: 1680.00, status: 'Geaccepteerd' },
  { period: 'Q2 2025', collected: 3650.00, paid: 4100.00, balance: -450.00, status: 'Geaccepteerd' },
  { period: 'Q1 2025', collected: 4200.00, paid: 2800.00, balance: 1400.00, status: 'Geaccepteerd' },
]

async function generateAangifte() {
  generating.value = true
  await new Promise((r) => setTimeout(r, 2000))
  generating.value = false
  xmlGenerated.value = true
}

function submitAangifte() {
  showSubmitModal.value = false
  alert('BTW aangifte ingediend! (Demo modus - geen echte indiening)')
}
</script>
