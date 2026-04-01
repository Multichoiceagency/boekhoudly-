<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold text-slate-900">Rapportages</h1>
      <div class="flex gap-2">
        <select v-model="selectedYear" class="px-3 py-2 border border-surface-200 rounded-lg text-sm focus:ring-2 focus:ring-primary-500">
          <option>2026</option>
          <option>2025</option>
        </select>
        <select v-model="selectedPeriod" class="px-3 py-2 border border-surface-200 rounded-lg text-sm focus:ring-2 focus:ring-primary-500">
          <option>Q1 (jan-mrt)</option>
          <option>Q2 (apr-jun)</option>
          <option>Q3 (jul-sep)</option>
          <option>Q4 (okt-dec)</option>
          <option>Heel jaar</option>
        </select>
      </div>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <NuxtLink v-for="report in reports" :key="report.title" :to="report.route" class="bg-white rounded-xl border border-surface-200 shadow-sm p-6 hover:shadow-md transition-shadow block">
        <div class="w-12 h-12 rounded-xl flex items-center justify-center mb-4" :class="report.bgColor">
          <span v-html="report.icon" class="w-6 h-6" :class="report.iconColor"></span>
        </div>
        <h2 class="text-lg font-semibold text-slate-900">{{ report.title }}</h2>
        <p class="text-sm text-slate-500 mt-1">{{ report.description }}</p>
        <span class="mt-4 text-sm font-medium text-primary-600 hover:text-primary-700 flex items-center gap-1">
          Bekijk rapport
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
          </svg>
        </span>
      </NuxtLink>
    </div>
  </div>
</template>

<script setup lang="ts">
const selectedYear = ref('2026')
const selectedPeriod = ref('Q1 (jan-mrt)')

const reports = [
  {
    title: 'Winst & Verlies',
    description: 'Overzicht van inkomsten en uitgaven over de geselecteerde periode.',
    icon: '<svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" /></svg>',
    bgColor: 'bg-emerald-100',
    iconColor: 'text-emerald-600',
    route: '/jaarrekening',
  },
  {
    title: 'Balans',
    description: 'Overzicht van bezittingen, schulden en eigen vermogen.',
    icon: '<svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 6l3 1m0 0l-3 9a5.002 5.002 0 006.001 0M6 7l3 9M6 7l6-2m6 2l3-1m-3 1l-3 9a5.002 5.002 0 006.001 0M18 7l3 9m-3-9l-6-2m0-2v2m0 16V5m0 16H9m3 0h3" /></svg>',
    bgColor: 'bg-blue-100',
    iconColor: 'text-blue-600',
    route: '/jaarrekening',
  },
  {
    title: 'BTW Overzicht',
    description: 'Samenvatting van BTW over inkomsten en uitgaven.',
    icon: '<svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 14l6-6m-5.5.5h.01m4.99 5h.01M19 21l-7-5-7 5V5a2 2 0 012-2h10a2 2 0 012 2v16z" /></svg>',
    bgColor: 'bg-purple-100',
    iconColor: 'text-purple-600',
    route: '/btw',
  },
  {
    title: 'Cashflow',
    description: 'Inzicht in inkomende en uitgaande geldstromen.',
    icon: '<svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>',
    bgColor: 'bg-amber-100',
    iconColor: 'text-amber-600',
    route: '/jaarrekening',
  },
  {
    title: 'Jaarrekening',
    description: 'Volledige jaarrekening met balans, winst & verlies en toelichting.',
    icon: '<svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>',
    bgColor: 'bg-indigo-100',
    iconColor: 'text-indigo-600',
    route: '/jaarrekening',
  },
  {
    title: 'Audit Rapport',
    description: 'Controle en verificatie van de boekhouding met audit trail.',
    icon: '<svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" /></svg>',
    bgColor: 'bg-teal-100',
    iconColor: 'text-teal-600',
    route: '/audit',
  },
  {
    title: 'Jaaroverzicht',
    description: 'Compleet financieel overzicht voor belastingaangifte.',
    icon: '<svg fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>',
    bgColor: 'bg-red-100',
    iconColor: 'text-red-600',
    route: '/aangifte-ib',
  },
]
</script>
