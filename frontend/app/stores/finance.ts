import { defineStore } from 'pinia'

interface Transaction {
  id: string
  amount: number
  date: string
  description: string
  type: 'income' | 'expense'
  category: string
  status: string
  confidence_score: number | null
}

export const useFinanceStore = defineStore('finance', {
  state: () => ({
    transactions: [] as Transaction[],
    loading: false,
    summary: {
      total_income: 0,
      total_expenses: 0,
      net_profit: 0,
      pending_count: 0,
      processed_count: 0,
    },
  }),

  actions: {
    async fetchTransactions(filters?: Record<string, string>) {
      this.loading = true
      try {
        const api = useApi()
        const params = new URLSearchParams(filters || {})
        const data = await api.get<{ items: Transaction[]; total: number }>(
          `/transactions?${params.toString()}`
        )
        this.transactions = data.items
      } finally {
        this.loading = false
      }
    },

    async fetchSummary() {
      const api = useApi()
      this.summary = await api.get('/transactions/summary')
    },
  },
})
