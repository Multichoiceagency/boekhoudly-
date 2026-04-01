<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-slate-900">Goedemorgen, Jan!</h1>
        <p class="text-slate-500 mt-1">{{ currentDate }}</p>
      </div>
      <div class="flex gap-2">
        <NuxtLink to="/ai-accountant" class="bg-primary-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-primary-700 transition-colors flex items-center gap-2">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
          AI Accountant
        </NuxtLink>
      </div>
    </div>

    <!-- Stat Cards -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      <StatCard title="Omzet deze maand" value="€ 12.430" change="+12,5%" color="primary" trend="up" />
      <StatCard title="Openstaande facturen" value="€ 10.675" change="3 facturen" color="amber" trend="neutral" />
      <StatCard title="BTW dit kwartaal" value="€ 2.611" change="Q1 2026" color="emerald" trend="neutral" />
      <StatCard title="Winst / Verlies" value="+ € 8.920" change="+8,3%" color="green" trend="up" />
    </div>

    <!-- Charts Row -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Cashflow Chart -->
      <div class="bg-white rounded-xl border border-surface-200 shadow-sm p-6">
        <h2 class="text-lg font-semibold text-slate-900 mb-4">Cashflow</h2>
        <div class="space-y-3">
          <div v-for="month in cashflowData" :key="month.name" class="flex items-center gap-3">
            <span class="text-xs text-slate-500 w-8">{{ month.name }}</span>
            <div class="flex-1 flex gap-1 h-6">
              <div class="bg-emerald-500 rounded-l h-full" :style="{ width: (month.income / maxCashflow * 100) + '%' }"></div>
              <div class="bg-red-400 rounded-r h-full" :style="{ width: (month.expense / maxCashflow * 100) + '%' }"></div>
            </div>
            <span class="text-xs font-medium w-16 text-right" :class="month.income - month.expense > 0 ? 'text-emerald-600' : 'text-red-600'">
              {{ month.income - month.expense > 0 ? '+' : '' }}€ {{ ((month.income - month.expense) / 1000).toFixed(1) }}k
            </span>
          </div>
        </div>
        <div class="flex items-center gap-4 mt-4 text-xs text-slate-500">
          <span class="flex items-center gap-1"><span class="w-3 h-3 bg-emerald-500 rounded"></span> Inkomsten</span>
          <span class="flex items-center gap-1"><span class="w-3 h-3 bg-red-400 rounded"></span> Uitgaven</span>
        </div>
      </div>

      <!-- Winst/Verlies -->
      <div class="bg-white rounded-xl border border-surface-200 shadow-sm p-6">
        <h2 class="text-lg font-semibold text-slate-900 mb-4">Winst & Verlies Q1 2026</h2>
        <div class="space-y-4">
          <div>
            <div class="flex justify-between text-sm mb-1"><span class="text-slate-600">Omzet</span><span class="font-medium text-slate-900">€ 38.450</span></div>
            <div class="w-full bg-surface-200 rounded-full h-3"><div class="bg-emerald-500 h-3 rounded-full" style="width: 100%"></div></div>
          </div>
          <div>
            <div class="flex justify-between text-sm mb-1"><span class="text-slate-600">Kosten</span><span class="font-medium text-slate-900">€ 29.530</span></div>
            <div class="w-full bg-surface-200 rounded-full h-3"><div class="bg-red-400 h-3 rounded-full" style="width: 76.8%"></div></div>
          </div>
          <div class="pt-3 border-t border-surface-200">
            <div class="flex justify-between"><span class="text-sm font-semibold text-slate-900">Brutowinst</span><span class="text-lg font-bold text-emerald-600">€ 8.920</span></div>
            <p class="text-xs text-slate-500 mt-1">Marge: 23,2% | +8,3% t.o.v. Q4 2025</p>
          </div>
          <div class="grid grid-cols-3 gap-2 pt-2">
            <div class="bg-surface-50 rounded-lg p-2 text-center">
              <p class="text-xs text-slate-500">Jan</p>
              <p class="text-sm font-bold text-emerald-600">€ 2.4k</p>
            </div>
            <div class="bg-surface-50 rounded-lg p-2 text-center">
              <p class="text-xs text-slate-500">Feb</p>
              <p class="text-sm font-bold text-emerald-600">€ 3.1k</p>
            </div>
            <div class="bg-surface-50 rounded-lg p-2 text-center">
              <p class="text-xs text-slate-500">Mrt</p>
              <p class="text-sm font-bold text-emerald-600">€ 3.4k</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- BTW + Agents Row -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- BTW Positie -->
      <div class="bg-white rounded-xl border border-surface-200 shadow-sm p-6">
        <h2 class="text-sm font-semibold text-slate-900 mb-3">BTW Positie Q1</h2>
        <div class="text-center py-4">
          <p class="text-3xl font-bold text-red-600">€ 2.610,62</p>
          <p class="text-xs text-slate-500 mt-1">Af te dragen</p>
        </div>
        <div class="space-y-2">
          <div class="flex justify-between text-sm"><span class="text-slate-600">BTW ontvangen</span><span class="font-medium">€ 4.832,10</span></div>
          <div class="flex justify-between text-sm"><span class="text-slate-600">BTW betaald</span><span class="font-medium">€ 2.221,48</span></div>
        </div>
        <div class="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
          <p class="text-xs font-medium text-red-700">Deadline: 30 april 2026 (29 dagen)</p>
        </div>
        <NuxtLink to="/btw" class="mt-3 block text-center text-sm font-medium text-primary-600 hover:text-primary-700">Bekijk aangifte →</NuxtLink>
      </div>

      <!-- Recent Transactions -->
      <div class="lg:col-span-2 bg-white rounded-xl border border-surface-200 shadow-sm">
        <div class="px-6 py-4 border-b border-surface-200 flex items-center justify-between">
          <h2 class="text-lg font-semibold text-slate-900">Recente transacties</h2>
          <NuxtLink to="/bank" class="text-sm text-primary-600 hover:text-primary-700 font-medium">Bekijk alle</NuxtLink>
        </div>
        <div class="overflow-x-auto">
          <table class="w-full">
            <thead>
              <tr class="text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                <th class="px-6 py-3">Datum</th>
                <th class="px-6 py-3">Omschrijving</th>
                <th class="px-6 py-3">Categorie</th>
                <th class="px-6 py-3 text-right">Bedrag</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-surface-100">
              <tr v-for="tx in recentTransactions" :key="tx.id" class="hover:bg-surface-50">
                <td class="px-6 py-3 text-sm text-slate-600">{{ tx.date }}</td>
                <td class="px-6 py-3 text-sm font-medium text-slate-900">{{ tx.description }}</td>
                <td class="px-6 py-3">
                  <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-surface-100 text-slate-700">{{ tx.category }}</span>
                </td>
                <td class="px-6 py-3 text-sm text-right font-medium" :class="tx.amount > 0 ? 'text-emerald-600' : 'text-slate-900'">
                  {{ tx.amount > 0 ? '+' : '' }}€ {{ Math.abs(tx.amount).toLocaleString('nl-NL') }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- AI Insights + Agents -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- AI Insights -->
      <div class="bg-white rounded-xl border border-surface-200 shadow-sm">
        <div class="px-6 py-4 border-b border-surface-200">
          <div class="flex items-center gap-2">
            <div class="w-6 h-6 bg-primary-100 rounded-lg flex items-center justify-center">
              <svg class="w-4 h-4 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
            </div>
            <h2 class="text-lg font-semibold text-slate-900">AI Inzichten</h2>
          </div>
        </div>
        <div class="p-6 space-y-4">
          <div v-for="insight in insights" :key="insight.title" class="flex gap-3">
            <div class="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5" :class="{ 'bg-red-100 text-red-600': insight.priority === 'high', 'bg-amber-100 text-amber-600': insight.priority === 'medium', 'bg-blue-100 text-blue-600': insight.priority === 'low' }">
              <span class="text-sm">{{ insight.icon }}</span>
            </div>
            <div>
              <h3 class="text-sm font-semibold text-slate-900">{{ insight.title }}</h3>
              <p class="text-xs text-slate-500 mt-0.5">{{ insight.description }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Active Agents -->
      <div class="lg:col-span-2 bg-white rounded-xl border border-surface-200 shadow-sm p-6">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-lg font-semibold text-slate-900">AI Agents Status</h2>
          <NuxtLink to="/ai-accountant" class="text-sm text-primary-600 hover:text-primary-700 font-medium">Open chat →</NuxtLink>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-5 gap-3">
          <div v-for="agent in agentStatus" :key="agent.name" class="bg-surface-50 rounded-lg p-3 text-center">
            <span class="text-2xl">{{ agent.icon }}</span>
            <p class="text-xs font-semibold text-slate-900 mt-1">{{ agent.name }}</p>
            <p class="text-[10px] text-slate-500">{{ agent.lastAction }}</p>
            <span class="inline-flex items-center gap-1 mt-2 text-[10px]">
              <span class="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
              Actief
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const currentDate = new Date().toLocaleDateString('nl-NL', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })

const recentTransactions = [
  { id: 1, date: '28 mrt', description: 'Betaling van Bakkerij de Vries', category: 'Omzet', amount: 2450 },
  { id: 2, date: '27 mrt', description: 'Google Workspace', category: 'Software', amount: -12.99 },
  { id: 3, date: '26 mrt', description: 'NS Business Card', category: 'Transport', amount: -156.80 },
  { id: 4, date: '25 mrt', description: 'Factuur #2024-038 WebDesign BV', category: 'Omzet', amount: 3800 },
  { id: 5, date: '24 mrt', description: 'Albert Heijn kantoorsnacks', category: 'Kantoor', amount: -34.50 },
]

const cashflowData = [
  { name: 'Jan', income: 11200, expense: 8800 },
  { name: 'Feb', income: 13800, expense: 10700 },
  { name: 'Mrt', income: 13450, expense: 10030 },
]
const maxCashflow = Math.max(...cashflowData.map((m) => Math.max(m.income, m.expense)))

const insights = [
  { title: 'BTW deadline nadert', description: 'Je BTW aangifte Q1 2026 moet voor 30 april. Geschat: € 2.611.', icon: '⏰', priority: 'high' },
  { title: 'Onbekende transactie', description: 'Betaling van € 1.250 aan onbekende leverancier.', icon: '⚠️', priority: 'medium' },
  { title: 'Besparingskans', description: 'Softwarekosten +23% t.o.v. vorig kwartaal.', icon: '💡', priority: 'low' },
]

const agentStatus = [
  { name: 'Boekhouder', icon: '📒', lastAction: '3 boekingen' },
  { name: 'BTW', icon: '🧾', lastAction: 'Aangifte klaar' },
  { name: 'Audit', icon: '🔍', lastAction: '1 fout gevonden' },
  { name: 'Accountant', icon: '📊', lastAction: 'Rapport klaar' },
  { name: 'Advisor', icon: '💡', lastAction: '2 tips' },
]
</script>
