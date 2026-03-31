<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold text-slate-900">Urenregistratie</h1>
      <div class="flex items-center gap-3">
        <button class="p-2 text-slate-400 hover:text-slate-600">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
          </svg>
        </button>
        <span class="text-sm font-medium text-slate-700">Week 13, 2026</span>
        <button class="p-2 text-slate-400 hover:text-slate-600">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
          </svg>
        </button>
      </div>
    </div>

    <!-- Summary -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
      <div class="bg-white rounded-xl border border-surface-200 shadow-sm p-5">
        <p class="text-sm text-slate-500">Totaal deze week</p>
        <p class="text-2xl font-bold text-slate-900 mt-1">32,5 uur</p>
      </div>
      <div class="bg-white rounded-xl border border-surface-200 shadow-sm p-5">
        <p class="text-sm text-slate-500">Declarabel</p>
        <p class="text-2xl font-bold text-emerald-600 mt-1">28,0 uur</p>
      </div>
      <div class="bg-white rounded-xl border border-surface-200 shadow-sm p-5">
        <p class="text-sm text-slate-500">Niet-declarabel</p>
        <p class="text-2xl font-bold text-slate-600 mt-1">4,5 uur</p>
      </div>
    </div>

    <!-- Week view -->
    <div class="bg-white rounded-xl border border-surface-200 shadow-sm overflow-hidden">
      <table class="w-full">
        <thead>
          <tr class="text-left text-xs font-medium text-slate-500 uppercase tracking-wider bg-surface-50">
            <th class="px-6 py-3">Project</th>
            <th v-for="day in days" :key="day" class="px-4 py-3 text-center">{{ day }}</th>
            <th class="px-4 py-3 text-center">Totaal</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-surface-100">
          <tr v-for="row in timeEntries" :key="row.project" class="hover:bg-surface-50">
            <td class="px-6 py-3 text-sm font-medium text-slate-900">{{ row.project }}</td>
            <td v-for="(hours, i) in row.hours" :key="i" class="px-4 py-3 text-center text-sm text-slate-600">
              {{ hours || '-' }}
            </td>
            <td class="px-4 py-3 text-center text-sm font-semibold text-slate-900">
              {{ row.hours.reduce((a: number, b: number) => a + b, 0) }}
            </td>
          </tr>
        </tbody>
        <tfoot>
          <tr class="bg-surface-50 font-semibold">
            <td class="px-6 py-3 text-sm text-slate-900">Totaal</td>
            <td v-for="(_, i) in days" :key="i" class="px-4 py-3 text-center text-sm text-slate-900">
              {{ timeEntries.reduce((sum, row) => sum + row.hours[i], 0) || '-' }}
            </td>
            <td class="px-4 py-3 text-center text-sm text-slate-900">32,5</td>
          </tr>
        </tfoot>
      </table>
    </div>

    <!-- Add hours form -->
    <div class="bg-white rounded-xl border border-surface-200 shadow-sm p-6">
      <h2 class="text-lg font-semibold text-slate-900 mb-4">Uren toevoegen</h2>
      <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div>
          <label class="block text-sm font-medium text-slate-700 mb-1">Project</label>
          <select class="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-transparent">
            <option>Bakkerij de Vries - Website</option>
            <option>WebDesign Studio - App</option>
            <option>Intern - Administratie</option>
          </select>
        </div>
        <div>
          <label class="block text-sm font-medium text-slate-700 mb-1">Datum</label>
          <input type="date" class="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-transparent" />
        </div>
        <div>
          <label class="block text-sm font-medium text-slate-700 mb-1">Uren</label>
          <input type="number" step="0.5" placeholder="0" class="w-full px-3 py-2 border border-surface-200 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-transparent" />
        </div>
        <div class="flex items-end">
          <button class="w-full bg-primary-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-primary-700 transition-colors">
            Toevoegen
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const days = ['Ma', 'Di', 'Wo', 'Do', 'Vr', 'Za', 'Zo']

const timeEntries = [
  { project: 'Bakkerij de Vries - Website', hours: [8, 7, 6, 4, 0, 0, 0] },
  { project: 'WebDesign Studio - App', hours: [0, 0, 2, 4, 3, 0, 0] },
  { project: 'Intern - Administratie', hours: [0, 1, 0, 0, 1.5, 0, 0] },
]
</script>
