<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold text-slate-900">Uitgaven</h1>
      <button class="bg-primary-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-primary-700 transition-colors flex items-center gap-2">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
        Nieuwe uitgave
      </button>
    </div>

    <div class="bg-white rounded-xl border border-surface-200 shadow-sm overflow-hidden">
      <table class="w-full">
        <thead>
          <tr class="text-left text-xs font-medium text-slate-500 uppercase tracking-wider bg-surface-50">
            <th class="px-6 py-3">Datum</th>
            <th class="px-6 py-3">Omschrijving</th>
            <th class="px-6 py-3">Categorie</th>
            <th class="px-6 py-3 text-right">Bedrag</th>
            <th class="px-6 py-3 text-right">BTW</th>
            <th class="px-6 py-3">Status</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-surface-100">
          <tr v-for="exp in expenses" :key="exp.id" class="hover:bg-surface-50">
            <td class="px-6 py-4 text-sm text-slate-600">{{ exp.date }}</td>
            <td class="px-6 py-4 text-sm font-medium text-slate-900">{{ exp.description }}</td>
            <td class="px-6 py-4">
              <span
                class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium"
                :class="categoryColor(exp.category)"
              >
                {{ exp.category }}
              </span>
            </td>
            <td class="px-6 py-4 text-sm text-right font-medium text-slate-900">€ {{ exp.amount.toLocaleString('nl-NL', { minimumFractionDigits: 2 }) }}</td>
            <td class="px-6 py-4 text-sm text-right text-slate-600">{{ exp.btw }}%</td>
            <td class="px-6 py-4">
              <span
                class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium"
                :class="exp.status === 'Geboekt' ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700'"
              >
                {{ exp.status }}
              </span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
const expenses = [
  { id: 1, date: '28 mrt 2026', description: 'Google Workspace abonnement', category: 'Software', amount: 12.99, btw: 21, status: 'Geboekt' },
  { id: 2, date: '27 mrt 2026', description: 'NS Business Card - maart', category: 'Transport', amount: 156.80, btw: 9, status: 'Geboekt' },
  { id: 3, date: '25 mrt 2026', description: 'Bol.com bureaustoelen', category: 'Kantoor', amount: 349.00, btw: 21, status: 'Review' },
  { id: 4, date: '22 mrt 2026', description: 'Facebook Ads campagne', category: 'Marketing', amount: 250.00, btw: 21, status: 'Geboekt' },
  { id: 5, date: '20 mrt 2026', description: 'KPN zakelijk internet', category: 'Telefoon', amount: 45.00, btw: 21, status: 'Geboekt' },
]

function categoryColor(category: string): string {
  const colors: Record<string, string> = {
    Software: 'bg-purple-100 text-purple-700',
    Transport: 'bg-blue-100 text-blue-700',
    Kantoor: 'bg-slate-100 text-slate-700',
    Marketing: 'bg-pink-100 text-pink-700',
    Telefoon: 'bg-cyan-100 text-cyan-700',
  }
  return colors[category] || 'bg-slate-100 text-slate-700'
}
</script>
