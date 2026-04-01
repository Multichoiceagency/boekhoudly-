<template>
  <div class="space-y-6">
    <h1 class="text-2xl font-bold text-slate-900">Banktransacties</h1>

    <!-- Bank account card -->
    <div class="bg-gradient-to-r from-primary-600 to-primary-800 rounded-xl p-6 text-white">
      <div class="flex items-center justify-between">
        <div>
          <p class="text-primary-200 text-sm">Bankrekening</p>
          <p class="text-2xl font-bold mt-1">{{ formatCurrency(bankBalance) }}</p>
          <p class="text-primary-200 text-sm mt-2">{{ transactions.length }} transacties</p>
        </div>
        <div class="text-right">
          <p class="text-primary-200 text-sm">Status</p>
          <p class="text-sm font-medium">{{ transactions.length > 0 ? 'Beschikbaar' : 'Geen data' }}</p>
        </div>
      </div>
    </div>

    <!-- Transactions -->
    <div class="bg-white rounded-xl border border-surface-200 shadow-sm overflow-hidden">
      <div class="px-6 py-4 border-b border-surface-200 flex items-center justify-between">
        <h2 class="text-lg font-semibold text-slate-900">Transacties</h2>
        <div class="flex gap-2">
          <input type="date" class="px-3 py-1.5 border border-surface-200 rounded-lg text-sm" />
          <input type="date" class="px-3 py-1.5 border border-surface-200 rounded-lg text-sm" />
        </div>
      </div>
      <table class="w-full">
        <thead>
          <tr class="text-left text-xs font-medium text-slate-500 uppercase tracking-wider bg-surface-50">
            <th class="px-6 py-3">Datum</th>
            <th class="px-6 py-3">Omschrijving</th>
            <th class="px-6 py-3 text-right">Bedrag</th>
            <th class="px-6 py-3">Categorie</th>
            <th class="px-6 py-3">Status</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-surface-100">
          <tr v-if="transactions.length === 0">
            <td colspan="5" class="px-6 py-12 text-center">
              <p class="text-sm text-slate-400">Geen banktransacties</p>
            </td>
          </tr>
          <tr v-for="tx in transactions" :key="tx.id" class="hover:bg-surface-50">
            <td class="px-6 py-3 text-sm text-slate-600">{{ tx.date }}</td>
            <td class="px-6 py-3 text-sm font-medium text-slate-900">{{ tx.description }}</td>
            <td class="px-6 py-3 text-sm text-right font-medium" :class="tx.amount > 0 ? 'text-emerald-600' : 'text-red-600'">
              {{ tx.amount > 0 ? '+' : '' }}€ {{ Math.abs(tx.amount).toLocaleString('nl-NL', { minimumFractionDigits: 2 }) }}
            </td>
            <td class="px-6 py-3 text-sm text-slate-600">{{ tx.category || '-' }}</td>
            <td class="px-6 py-3">
              <span v-if="tx.matched" class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-100 text-emerald-700">
                Gekoppeld
              </span>
              <button v-else class="text-xs text-primary-600 hover:text-primary-700 font-medium">
                Koppel transactie
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
const ws = useWorkspaceStore()

const transactions = computed(() => ws.bankTransactions)

const bankBalance = computed(() => {
  return ws.bankTransactions.reduce((sum, tx) => sum + tx.amount, 0)
})

function formatCurrency(value: number): string {
  return '€ ' + Math.abs(value).toLocaleString('nl-NL', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}
</script>
