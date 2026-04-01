import { defineStore } from 'pinia'

export interface Branding {
  logo: string | null
  primaryColor: string
  companyName: string
  address: string
  postcode: string
  city: string
  kvk: string
  btw: string
  iban: string
  email: string
  phone: string
  website: string
}

export interface Invoice {
  id: string
  number: string
  client: string
  clientId: string
  date: string
  dueDate: string
  lines: { desc: string; qty: number; price: number; btwRate: number }[]
  status: 'concept' | 'verzonden' | 'betaald' | 'verlopen'
  paidDate?: string
}

export interface Expense {
  id: string
  date: string
  description: string
  category: string
  amount: number
  btwRate: number
  status: 'concept' | 'geboekt' | 'review'
  supplierId?: string
  receipt?: string
}

export interface Debtor {
  id: string
  name: string
  email: string
  kvk: string
  btw: string
  iban: string
  paymentTerm: number
  address: string
  city: string
}

export interface Creditor {
  id: string
  name: string
  email: string
  category: string
  iban: string
  paymentTerm: number
}

export interface BankTransaction {
  id: string
  date: string
  description: string
  amount: number
  category: string
  matched: boolean
  matchedInvoiceId?: string
  matchedExpenseId?: string
}

export interface Company {
  id: string
  name: string
  type: string
  kvk: string
  btw: string
  activiteiten: string
  parentId: string | null
  branding: Branding
  agents: string[]
}

export const useWorkspaceStore = defineStore('workspace', {
  state: () => ({
    activeCompanyId: '',
    companies: [] as Company[],
    invoices: [] as Invoice[],
    expenses: [] as Expense[],
    debtors: [] as Debtor[],
    creditors: [] as Creditor[],
    bankTransactions: [] as BankTransaction[],
    loaded: false,
    loading: false,
  }),

  getters: {
    activeCompany(state): Company {
      return state.companies.find(c => c.id === state.activeCompanyId) || state.companies[0] || {
        id: '', name: '', type: '', kvk: '', btw: '', activiteiten: '', parentId: null, agents: [],
        branding: { logo: null, primaryColor: '#059669', companyName: '', address: '', postcode: '', city: '', kvk: '', btw: '', iban: '', email: '', phone: '', website: '' },
      }
    },
    totalRevenue(state): number {
      return state.invoices.reduce((sum, inv) => sum + inv.lines.reduce((s, l) => s + l.qty * l.price, 0), 0)
    },
    totalExpenses(state): number {
      return state.expenses.reduce((sum, exp) => sum + exp.amount, 0)
    },
    netProfit(): number {
      return this.totalRevenue - this.totalExpenses
    },
    outstandingInvoices(state): Invoice[] {
      return state.invoices.filter(i => i.status === 'verzonden' || i.status === 'verlopen')
    },
    outstandingAmount(): number {
      return this.outstandingInvoices.reduce((sum, inv) => sum + inv.lines.reduce((s, l) => s + l.qty * l.price, 0), 0)
    },
    btwCollected(state): number {
      return state.invoices
        .filter(i => i.status === 'betaald' || i.status === 'verzonden' || i.status === 'verlopen')
        .reduce((sum, inv) => sum + inv.lines.reduce((s, l) => s + (l.qty * l.price * l.btwRate / 100), 0), 0)
    },
    btwPaid(state): number {
      return state.expenses
        .filter(e => e.status === 'geboekt')
        .reduce((sum, exp) => sum + (exp.amount * exp.btwRate / (100 + exp.btwRate)), 0)
    },
    btwDue(): number {
      return this.btwCollected - this.btwPaid
    },
    revenueByMonth(state): { month: string; income: number; expense: number }[] {
      const months: Record<string, { income: number; expense: number }> = {}
      state.invoices.forEach(inv => {
        const m = inv.date.substring(0, 7)
        if (!months[m]) months[m] = { income: 0, expense: 0 }
        months[m].income += inv.lines.reduce((s, l) => s + l.qty * l.price, 0)
      })
      state.expenses.forEach(exp => {
        const m = exp.date.substring(0, 7)
        if (!months[m]) months[m] = { income: 0, expense: 0 }
        months[m].expense += exp.amount
      })
      return Object.entries(months).sort().map(([month, data]) => ({ month, ...data }))
    },
    invoiceTotal: () => (inv: Invoice): number => {
      return inv.lines.reduce((s, l) => s + l.qty * l.price, 0)
    },
    invoiceTotalIncBtw: () => (inv: Invoice): number => {
      return inv.lines.reduce((s, l) => s + l.qty * l.price * (1 + l.btwRate / 100), 0)
    },
    nextInvoiceNumber(state): string {
      if (state.invoices.length === 0) return `INV-${new Date().getFullYear()}-001`
      const nums = state.invoices.map(i => parseInt(i.number.split('-').pop() || '0'))
      const year = new Date().getFullYear()
      return `INV-${year}-${String(Math.max(0, ...nums) + 1).padStart(3, '0')}`
    },
  },

  actions: {
    // ---- API helper ----
    _api() {
      return useApi()
    },

    // ---- Load all data from backend ----
    async loadAll() {
      if (this.loading) return
      this.loading = true
      try {
        const api = this._api()
        const [companies, invoices, expenses, debtors, creditors, bankTx] = await Promise.all([
          api.get<Company[]>('/workspace/companies').catch(() => []),
          api.get<Invoice[]>('/workspace/invoices').catch(() => []),
          api.get<Expense[]>('/workspace/expenses').catch(() => []),
          api.get<Debtor[]>('/workspace/debtors').catch(() => []),
          api.get<Creditor[]>('/workspace/creditors').catch(() => []),
          api.get<BankTransaction[]>('/workspace/bank-transactions').catch(() => []),
        ])
        this.companies = companies
        this.invoices = invoices
        this.expenses = expenses
        this.debtors = debtors
        this.creditors = creditors
        this.bankTransactions = bankTx
        if (companies.length > 0 && !this.activeCompanyId) {
          this.activeCompanyId = companies[0].id
        }
        this.loaded = true
      } catch (e) {
        console.error('Failed to load workspace data:', e)
      } finally {
        this.loading = false
      }
    },

    // ---- Companies ----
    switchCompany(id: string) {
      this.activeCompanyId = id
    },
    async addCompany(c: Partial<Company>) {
      const api = this._api()
      const created = await api.post<Company>('/workspace/companies', c)
      this.companies.push(created)
      if (!this.activeCompanyId) this.activeCompanyId = created.id
      return created
    },
    async updateBranding(companyId: string, branding: Partial<Branding>) {
      const api = this._api()
      const updated = await api.put<Company>(`/workspace/companies/${companyId}`, branding)
      const idx = this.companies.findIndex(c => c.id === companyId)
      if (idx >= 0) this.companies[idx] = updated
    },

    // ---- Invoices ----
    async addInvoice(inv: Partial<Invoice>) {
      const api = this._api()
      const created = await api.post<Invoice>('/workspace/invoices', inv)
      this.invoices.unshift(created)
      return created
    },
    async updateInvoice(id: string, data: Partial<Invoice>) {
      const api = this._api()
      const updated = await api.put<Invoice>(`/workspace/invoices/${id}`, data)
      const idx = this.invoices.findIndex(i => i.id === id)
      if (idx >= 0) this.invoices[idx] = updated
    },
    async deleteInvoice(id: string) {
      const api = this._api()
      await api.delete(`/workspace/invoices/${id}`)
      this.invoices = this.invoices.filter(i => i.id !== id)
    },

    // ---- Expenses ----
    async addExpense(exp: Partial<Expense>) {
      const api = this._api()
      const created = await api.post<Expense>('/workspace/expenses', exp)
      this.expenses.unshift(created)
      return created
    },
    async updateExpense(id: string, data: Partial<Expense>) {
      const api = this._api()
      const updated = await api.put<Expense>(`/workspace/expenses/${id}`, data)
      const idx = this.expenses.findIndex(e => e.id === id)
      if (idx >= 0) this.expenses[idx] = updated
    },
    async deleteExpense(id: string) {
      const api = this._api()
      await api.delete(`/workspace/expenses/${id}`)
      this.expenses = this.expenses.filter(e => e.id !== id)
    },

    // ---- Debtors ----
    async addDebtor(d: Partial<Debtor>) {
      const api = this._api()
      const created = await api.post<Debtor>('/workspace/debtors', d)
      this.debtors.push(created)
      return created
    },
    async updateDebtor(id: string, data: Partial<Debtor>) {
      const api = this._api()
      const updated = await api.put<Debtor>(`/workspace/debtors/${id}`, data)
      const idx = this.debtors.findIndex(d => d.id === id)
      if (idx >= 0) this.debtors[idx] = updated
    },
    async deleteDebtor(id: string) {
      const api = this._api()
      await api.delete(`/workspace/debtors/${id}`)
      this.debtors = this.debtors.filter(d => d.id !== id)
    },

    // ---- Creditors ----
    async addCreditor(c: Partial<Creditor>) {
      const api = this._api()
      const created = await api.post<Creditor>('/workspace/creditors', c)
      this.creditors.push(created)
      return created
    },
    async deleteCreditor(id: string) {
      const api = this._api()
      await api.delete(`/workspace/creditors/${id}`)
      this.creditors = this.creditors.filter(c => c.id !== id)
    },

    // ---- Bank Transactions ----
    async addBankTransaction(tx: Partial<BankTransaction>) {
      const api = this._api()
      const created = await api.post<BankTransaction>('/workspace/bank-transactions', tx)
      this.bankTransactions.unshift(created)
      return created
    },
    async matchTransaction(txId: string, type: 'invoice' | 'expense', targetId: string) {
      const api = this._api()
      const data: any = { matched: true }
      if (type === 'invoice') data.matchedInvoiceId = targetId
      else data.matchedExpenseId = targetId
      const updated = await api.put<BankTransaction>(`/workspace/bank-transactions/${txId}`, data)
      const idx = this.bankTransactions.findIndex(t => t.id === txId)
      if (idx >= 0) this.bankTransactions[idx] = updated
    },

    // ---- Bulk import (Perfex, CSV, etc.) ----
    async importBulkData(items: { type: string; data: any }[]) {
      for (const item of items) {
        try {
          if (item.type === 'invoice') await this.addInvoice(item.data)
          else if (item.type === 'expense') await this.addExpense(item.data)
          else if (item.type === 'debtor') await this.addDebtor(item.data)
          else if (item.type === 'creditor') await this.addCreditor(item.data)
          else if (item.type === 'bank') await this.addBankTransaction(item.data)
        } catch (e) {
          console.warn(`Import failed for ${item.type}:`, e)
        }
      }
    },
  },
})
