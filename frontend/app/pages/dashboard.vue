<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-[22px] font-bold text-gray-900">Overzicht</h1>
        <p class="text-[13px] text-gray-500 mt-0.5">Financieel overzicht van je bedrijf</p>
      </div>
      <div class="flex gap-2">
        <select class="px-3 py-2 bg-white border border-gray-200 rounded-xl text-[13px] text-gray-600 font-medium">
          <option>Deze maand</option><option>Dit kwartaal</option><option>Dit jaar</option>
        </select>
      </div>
    </div>

    <!-- Balance Cards -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-5">
      <!-- Main Balance -->
      <div class="bg-gradient-to-br from-emerald-600 to-emerald-800 rounded-2xl p-6 text-white relative overflow-hidden">
        <div class="absolute top-0 right-0 w-32 h-32 bg-white/5 rounded-full -translate-y-8 translate-x-8"></div>
        <div class="absolute bottom-0 left-0 w-24 h-24 bg-white/5 rounded-full translate-y-8 -translate-x-8"></div>
        <p class="text-[12px] text-emerald-200 font-medium">Bankrekening</p>
        <p class="text-[11px] text-emerald-300 mt-0.5">ING Zakelijke Rekening</p>
        <p class="text-[28px] font-bold mt-3">{{ fc(24650.83) }}</p>
        <div class="flex items-center gap-1.5 mt-2">
          <span class="text-[11px] bg-white/15 px-2 py-0.5 rounded-full">+15% dit kwartaal</span>
        </div>
        <div class="flex items-center justify-between mt-4 pt-3 border-t border-white/10">
          <NuxtLink to="/bank" class="text-[12px] text-emerald-200 hover:text-white font-medium flex items-center gap-1">
            Bekijk details <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 8l4 4m0 0l-4 4m4-4H3" /></svg>
          </NuxtLink>
        </div>
      </div>

      <!-- Revenue -->
      <div class="bg-white rounded-2xl border border-gray-100 p-6">
        <div class="flex items-center justify-between">
          <p class="text-[12px] text-gray-500 font-medium">Omzet dit kwartaal</p>
          <div class="w-8 h-8 bg-emerald-50 rounded-xl flex items-center justify-center"><svg class="w-4 h-4 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" /></svg></div>
        </div>
        <p class="text-[26px] font-bold text-gray-900 mt-2">{{ fc(ws.totalRevenue) }}</p>
        <div class="flex items-center gap-1.5 mt-2">
          <span class="text-[11px] text-emerald-600 font-semibold bg-emerald-50 px-2 py-0.5 rounded-full">+12,5%</span>
          <span class="text-[11px] text-gray-400">t.o.v. vorig kwartaal</span>
        </div>
        <NuxtLink to="/rapportage" class="text-[12px] text-gray-400 hover:text-emerald-600 font-medium flex items-center gap-1 mt-4 pt-3 border-t border-gray-50">
          Bekijk rapportage <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 8l4 4m0 0l-4 4m4-4H3" /></svg>
        </NuxtLink>
      </div>

      <!-- Openstaand -->
      <div class="bg-white rounded-2xl border border-gray-100 p-6">
        <div class="flex items-center justify-between">
          <p class="text-[12px] text-gray-500 font-medium">Openstaande facturen</p>
          <div class="w-8 h-8 bg-amber-50 rounded-xl flex items-center justify-center"><svg class="w-4 h-4 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" /></svg></div>
        </div>
        <p class="text-[26px] font-bold text-gray-900 mt-2">{{ fc(ws.outstandingAmount) }}</p>
        <div class="flex items-center gap-1.5 mt-2">
          <span class="text-[11px] text-amber-600 font-semibold bg-amber-50 px-2 py-0.5 rounded-full">{{ ws.outstandingInvoices.length }} facturen</span>
          <span class="text-[11px] text-gray-400">openstaand</span>
        </div>
        <NuxtLink to="/facturen" class="text-[12px] text-gray-400 hover:text-emerald-600 font-medium flex items-center gap-1 mt-4 pt-3 border-t border-gray-50">
          Bekijk facturen <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 8l4 4m0 0l-4 4m4-4H3" /></svg>
        </NuxtLink>
      </div>
    </div>

    <!-- Wallet + Cash Flow -->
    <div class="grid grid-cols-1 lg:grid-cols-5 gap-5">
      <!-- BTW & Wallet -->
      <div class="lg:col-span-2 bg-white rounded-2xl border border-gray-100 p-6">
        <div class="flex items-center justify-between mb-5">
          <h2 class="text-[15px] font-bold text-gray-900">Financieel Overzicht</h2>
        </div>
        <div class="space-y-4">
          <div class="flex items-center justify-between py-3 px-4 bg-emerald-50 rounded-xl">
            <div class="flex items-center gap-3">
              <div class="w-8 h-8 bg-emerald-600 rounded-lg flex items-center justify-center text-white text-[11px] font-bold">W</div>
              <div><p class="text-[13px] font-semibold text-gray-900">Winst Q1</p><p class="text-[11px] text-gray-500">Omzet - kosten</p></div>
            </div>
            <div class="text-right"><p class="text-[15px] font-bold text-emerald-700">{{ fc(ws.netProfit) }}</p><p class="text-[10px] text-emerald-600">+8,3%</p></div>
          </div>
          <div class="flex items-center justify-between py-3 px-4 bg-red-50 rounded-xl">
            <div class="flex items-center gap-3">
              <div class="w-8 h-8 bg-red-500 rounded-lg flex items-center justify-center text-white text-[11px] font-bold">B</div>
              <div><p class="text-[13px] font-semibold text-gray-900">BTW af te dragen</p><p class="text-[11px] text-gray-500">Deadline 30 april</p></div>
            </div>
            <div class="text-right"><p class="text-[15px] font-bold text-red-600">{{ fc(ws.btwDue) }}</p><p class="text-[10px] text-red-500">Q1 2026</p></div>
          </div>
          <div class="flex items-center justify-between py-3 px-4 bg-blue-50 rounded-xl">
            <div class="flex items-center gap-3">
              <div class="w-8 h-8 bg-blue-500 rounded-lg flex items-center justify-center text-white text-[11px] font-bold">K</div>
              <div><p class="text-[13px] font-semibold text-gray-900">Totaal kosten</p><p class="text-[11px] text-gray-500">{{ ws.expenses.length }} transacties</p></div>
            </div>
            <div class="text-right"><p class="text-[15px] font-bold text-gray-900">{{ fc(ws.totalExpenses) }}</p><p class="text-[10px] text-gray-500">deze maand</p></div>
          </div>
        </div>
      </div>

      <!-- Cash Flow Chart -->
      <div class="lg:col-span-3 bg-white rounded-2xl border border-gray-100 p-6">
        <div class="flex items-center justify-between mb-5">
          <div>
            <h2 class="text-[15px] font-bold text-gray-900">Cashflow</h2>
            <p class="text-[24px] font-bold text-gray-900 mt-1">{{ fc(24650.83) }}</p>
          </div>
          <div class="flex gap-1 bg-gray-100 p-1 rounded-xl">
            <button class="text-[11px] px-3 py-1 rounded-lg font-medium text-gray-500 hover:text-gray-900">Maand</button>
            <button class="text-[11px] px-3 py-1 rounded-lg font-medium bg-emerald-600 text-white">Kwartaal</button>
          </div>
        </div>
        <!-- Simple bar chart -->
        <div class="flex items-end gap-3 h-48 mt-4">
          <div v-for="month in chartData" :key="month.name" class="flex-1 flex flex-col items-center gap-1">
            <div class="w-full flex flex-col gap-0.5 items-center justify-end h-40">
              <div class="w-full max-w-[40px] bg-emerald-500 rounded-t-lg transition-all" :style="{ height: (month.income / maxVal * 100) + '%' }"></div>
              <div class="w-full max-w-[40px] bg-gray-200 rounded-b-lg transition-all" :style="{ height: (month.expense / maxVal * 100) + '%' }"></div>
            </div>
            <span class="text-[11px] text-gray-400 font-medium">{{ month.name }}</span>
          </div>
        </div>
        <div class="flex items-center gap-5 mt-4 pt-3 border-t border-gray-50">
          <span class="flex items-center gap-1.5 text-[11px] text-gray-500"><span class="w-2.5 h-2.5 bg-emerald-500 rounded-sm"></span> Inkomsten</span>
          <span class="flex items-center gap-1.5 text-[11px] text-gray-500"><span class="w-2.5 h-2.5 bg-gray-200 rounded-sm"></span> Uitgaven</span>
        </div>
      </div>
    </div>

    <!-- Recent Activities -->
    <div class="bg-white rounded-2xl border border-gray-100">
      <div class="px-6 py-4 flex items-center justify-between border-b border-gray-50">
        <h2 class="text-[15px] font-bold text-gray-900">Recente Activiteiten</h2>
        <div class="flex items-center gap-3">
          <div class="relative">
            <svg class="w-4 h-4 text-gray-400 absolute left-3 top-1/2 -translate-y-1/2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>
            <input type="text" placeholder="Zoek..." class="pl-9 pr-3 py-1.5 bg-gray-50 border border-gray-100 rounded-lg text-[12px] w-44 focus:ring-1 focus:ring-emerald-500 focus:outline-none" />
          </div>
          <button class="text-[12px] text-gray-500 border border-gray-200 px-3 py-1.5 rounded-lg hover:bg-gray-50 flex items-center gap-1.5">
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" /></svg>
            Filter
          </button>
        </div>
      </div>
      <table class="w-full">
        <thead>
          <tr class="text-left text-[11px] font-medium text-gray-400 uppercase tracking-wider">
            <th class="px-6 py-3 w-8"></th>
            <th class="px-6 py-3">Activiteit</th>
            <th class="px-6 py-3">Referentie</th>
            <th class="px-6 py-3">Datum</th>
            <th class="px-6 py-3 text-right">Bedrag</th>
            <th class="px-6 py-3">Status</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-50">
          <tr v-for="act in recentActivities" :key="act.id" class="hover:bg-gray-50/50 transition-colors">
            <td class="px-6 py-3"><div class="w-8 h-8 rounded-xl flex items-center justify-center" :class="act.iconBg"><span class="text-sm">{{ act.icon }}</span></div></td>
            <td class="px-6 py-3"><p class="text-[13px] font-medium text-gray-900">{{ act.description }}</p></td>
            <td class="px-6 py-3 text-[12px] text-gray-500 font-mono">{{ act.ref }}</td>
            <td class="px-6 py-3 text-[12px] text-gray-500">{{ act.date }}</td>
            <td class="px-6 py-3 text-[13px] text-right font-semibold" :class="act.amount > 0 ? 'text-emerald-600' : 'text-gray-900'">
              {{ act.amount > 0 ? '+' : '' }}{{ fc(act.amount) }}
            </td>
            <td class="px-6 py-3">
              <span class="inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-medium" :class="act.statusClass">{{ act.status }}</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
const ws = useWorkspaceStore()

const chartData = [
  { name: 'Jan', income: 11200, expense: 8800 },
  { name: 'Feb', income: 13800, expense: 10700 },
  { name: 'Mrt', income: 14500, expense: 10030 },
  { name: 'Apr', income: 8200, expense: 6400 },
]
const maxVal = Math.max(...chartData.flatMap(m => [m.income, m.expense]))

const recentActivities = [
  { id: 1, icon: '📄', iconBg: 'bg-emerald-50', description: 'Factuur verzonden', ref: 'INV-2026-042', date: '28 mrt 2026', amount: 2964.50, status: 'Betaald', statusClass: 'bg-emerald-50 text-emerald-700' },
  { id: 2, icon: '💳', iconBg: 'bg-red-50', description: 'Google Workspace', ref: 'EXP-0312', date: '27 mrt 2026', amount: -12.99, status: 'Geboekt', statusClass: 'bg-emerald-50 text-emerald-700' },
  { id: 3, icon: '🚂', iconBg: 'bg-blue-50', description: 'NS Business Card', ref: 'EXP-0311', date: '26 mrt 2026', amount: -156.80, status: 'Geboekt', statusClass: 'bg-emerald-50 text-emerald-700' },
  { id: 4, icon: '📄', iconBg: 'bg-emerald-50', description: 'Factuur WebDesign Studio', ref: 'INV-2026-041', date: '25 mrt 2026', amount: 4598, status: 'Verzonden', statusClass: 'bg-amber-50 text-amber-700' },
  { id: 5, icon: '🛒', iconBg: 'bg-purple-50', description: 'Bol.com bureaustoelen', ref: 'EXP-0310', date: '25 mrt 2026', amount: -349, status: 'Review', statusClass: 'bg-amber-50 text-amber-700' },
  { id: 6, icon: '📢', iconBg: 'bg-pink-50', description: 'Facebook Ads campagne', ref: 'EXP-0309', date: '22 mrt 2026', amount: -250, status: 'Geboekt', statusClass: 'bg-emerald-50 text-emerald-700' },
  { id: 7, icon: '⚠️', iconBg: 'bg-red-50', description: 'Factuur TechStart verlopen', ref: 'INV-2026-039', date: '15 mrt 2026', amount: 5600, status: 'Verlopen', statusClass: 'bg-red-50 text-red-700' },
]

function fc(v: number) { return '€ ' + Math.abs(v).toLocaleString('nl-NL', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }
</script>
