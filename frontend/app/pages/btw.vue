<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold text-slate-900">BTW Aangiftes</h1>
      <button class="bg-primary-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-primary-700 transition-colors flex items-center gap-2">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
        </svg>
        Genereer aangifte
      </button>
    </div>

    <!-- Current quarter summary -->
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

      <div class="mt-6 pt-4 border-t border-surface-200">
        <h3 class="text-sm font-semibold text-slate-700 mb-3">Verdeling per tarief</h3>
        <div class="grid grid-cols-3 gap-4">
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
    </div>

    <!-- Past filings -->
    <div class="bg-white rounded-xl border border-surface-200 shadow-sm overflow-hidden">
      <div class="px-6 py-4 border-b border-surface-200">
        <h2 class="text-lg font-semibold text-slate-900">Eerdere aangiftes</h2>
      </div>
      <table class="w-full">
        <thead>
          <tr class="text-left text-xs font-medium text-slate-500 uppercase tracking-wider bg-surface-50">
            <th class="px-6 py-3">Periode</th>
            <th class="px-6 py-3 text-right">BTW ontvangen</th>
            <th class="px-6 py-3 text-right">BTW betaald</th>
            <th class="px-6 py-3 text-right">Saldo</th>
            <th class="px-6 py-3">Status</th>
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
              <span
                class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium"
                :class="{
                  'bg-emerald-100 text-emerald-700': filing.status === 'Geaccepteerd',
                  'bg-blue-100 text-blue-700': filing.status === 'Ingediend',
                  'bg-amber-100 text-amber-700': filing.status === 'Concept',
                }"
              >
                {{ filing.status }}
              </span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
const pastFilings = [
  { period: 'Q4 2025', collected: 5120.00, paid: 2340.50, balance: 2779.50, status: 'Geaccepteerd' },
  { period: 'Q3 2025', collected: 4890.00, paid: 3210.00, balance: 1680.00, status: 'Geaccepteerd' },
  { period: 'Q2 2025', collected: 3650.00, paid: 4100.00, balance: -450.00, status: 'Geaccepteerd' },
  { period: 'Q1 2025', collected: 4200.00, paid: 2800.00, balance: 1400.00, status: 'Geaccepteerd' },
]
</script>
