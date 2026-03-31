<template>
  <div class="space-y-6">
    <!-- Header -->
    <div>
      <h1 class="text-2xl font-bold text-slate-900">Goedemorgen, Jan!</h1>
      <p class="text-slate-500 mt-1">{{ currentDate }}</p>
    </div>

    <!-- Stat Cards -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      <StatCard
        title="Omzet deze maand"
        value="€ 12.430"
        change="+12,5%"
        color="primary"
        trend="up"
      />
      <StatCard
        title="Openstaande facturen"
        value="€ 3.250"
        change="3 facturen"
        color="amber"
        trend="neutral"
      />
      <StatCard
        title="BTW dit kwartaal"
        value="€ 2.611"
        change="Q1 2026"
        color="emerald"
        trend="neutral"
      />
      <StatCard
        title="Winst / Verlies"
        value="+ € 8.920"
        change="+8,3%"
        color="green"
        trend="up"
      />
    </div>

    <!-- Content Grid -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
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
                  <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-surface-100 text-slate-700">
                    {{ tx.category }}
                  </span>
                </td>
                <td class="px-6 py-3 text-sm text-right font-medium" :class="tx.amount > 0 ? 'text-emerald-600' : 'text-slate-900'">
                  {{ tx.amount > 0 ? '+' : '' }}€ {{ Math.abs(tx.amount).toLocaleString('nl-NL') }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- AI Insights -->
      <div class="bg-white rounded-xl border border-surface-200 shadow-sm">
        <div class="px-6 py-4 border-b border-surface-200">
          <div class="flex items-center gap-2">
            <div class="w-6 h-6 bg-primary-100 rounded-lg flex items-center justify-center">
              <svg class="w-4 h-4 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <h2 class="text-lg font-semibold text-slate-900">AI Inzichten</h2>
          </div>
        </div>
        <div class="p-6 space-y-4">
          <div v-for="insight in insights" :key="insight.title" class="flex gap-3">
            <div
              class="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5"
              :class="{
                'bg-red-100 text-red-600': insight.priority === 'high',
                'bg-amber-100 text-amber-600': insight.priority === 'medium',
                'bg-blue-100 text-blue-600': insight.priority === 'low',
              }"
            >
              <svg v-if="insight.type === 'deadline'" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <svg v-else-if="insight.type === 'alert'" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
              <svg v-else class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div>
              <h3 class="text-sm font-semibold text-slate-900">{{ insight.title }}</h3>
              <p class="text-xs text-slate-500 mt-0.5">{{ insight.description }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const currentDate = new Date().toLocaleDateString('nl-NL', {
  weekday: 'long',
  year: 'numeric',
  month: 'long',
  day: 'numeric',
})

const recentTransactions = [
  { id: 1, date: '28 mrt', description: 'Betaling van Bakkerij de Vries', category: 'Omzet', amount: 2450 },
  { id: 2, date: '27 mrt', description: 'Google Workspace', category: 'Software', amount: -12.99 },
  { id: 3, date: '26 mrt', description: 'NS Business Card', category: 'Transport', amount: -156.80 },
  { id: 4, date: '25 mrt', description: 'Factuur #2024-038 WebDesign BV', category: 'Omzet', amount: 3800 },
  { id: 5, date: '24 mrt', description: 'Albert Heijn kantoorsnacks', category: 'Kantoor', amount: -34.50 },
]

const insights = [
  {
    title: 'BTW deadline nadert',
    description: 'Je BTW aangifte Q1 2026 moet voor 30 april ingediend worden. Geschat bedrag: € 2.611.',
    type: 'deadline',
    priority: 'high',
  },
  {
    title: 'Onbekende transactie',
    description: 'Betaling van € 1.250 aan onbekende leverancier vereist review.',
    type: 'alert',
    priority: 'medium',
  },
  {
    title: 'Besparingskans',
    description: 'Softwarekosten +23% t.o.v. vorig kwartaal. Evalueer contracten.',
    type: 'tip',
    priority: 'low',
  },
]
</script>
