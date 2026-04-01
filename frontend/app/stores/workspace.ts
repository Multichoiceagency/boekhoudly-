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
    activeCompanyId: '2',
    companies: [
      {
        id: '1', name: 'De Vries Holding BV', type: 'BV (Holding)', kvk: '87654321', btw: 'NL987654321B01',
        activiteiten: 'Houdstermaatschappij', parentId: null, agents: ['accountant', 'advisor'],
        branding: { logo: null, primaryColor: '#4F46E5', companyName: 'De Vries Holding BV', address: 'Herengracht 123', postcode: '1015 AB', city: 'Amsterdam', kvk: '87654321', btw: 'NL987654321B01', iban: 'NL91 INGB 0001 2345 67', email: 'holding@devries.nl', phone: '020-1234567', website: 'www.devries-holding.nl' },
      },
      {
        id: '2', name: 'De Vries Digital BV', type: 'BV (Werk-BV)', kvk: '12345678', btw: 'NL123456789B01',
        activiteiten: 'Communicatie- en grafisch ontwerp', parentId: '1', agents: ['boekhouder', 'btw', 'audit', 'accountant', 'advisor'],
        branding: { logo: null, primaryColor: '#4F46E5', companyName: 'De Vries Digital BV', address: 'Herengracht 123', postcode: '1015 AB', city: 'Amsterdam', kvk: '12345678', btw: 'NL123456789B01', iban: 'NL91 INGB 0001 2345 67', email: 'info@devries-digital.nl', phone: '020-1234567', website: 'www.devries-digital.nl' },
      },
    ] as Company[],

    invoices: [
      { id: 'inv1', number: 'INV-2026-042', client: 'Bakkerij de Vries BV', clientId: 'deb1', date: '2026-03-28', dueDate: '2026-04-27', lines: [{ desc: 'Website redesign', qty: 1, price: 1800, btwRate: 21 }, { desc: 'SEO optimalisatie', qty: 1, price: 650, btwRate: 21 }], status: 'betaald', paidDate: '2026-03-30' },
      { id: 'inv2', number: 'INV-2026-041', client: 'WebDesign Studio Amsterdam', clientId: 'deb2', date: '2026-03-25', dueDate: '2026-04-08', lines: [{ desc: 'Mobile app development - fase 1', qty: 40, price: 95, btwRate: 21 }], status: 'verzonden' },
      { id: 'inv3', number: 'INV-2026-040', client: 'Groene Hart Catering', clientId: 'deb3', date: '2026-03-20', dueDate: '2026-04-19', lines: [{ desc: 'Webshop onderhoud maart', qty: 15, price: 85, btwRate: 21 }], status: 'verzonden' },
      { id: 'inv4', number: 'INV-2026-039', client: 'TechStart Nederland BV', clientId: 'deb4', date: '2026-03-15', dueDate: '2026-04-14', lines: [{ desc: 'Platform development sprint 4', qty: 56, price: 100, btwRate: 21 }], status: 'verlopen' },
      { id: 'inv5', number: 'INV-2026-038', client: 'Van den Berg Consultancy', clientId: 'deb5', date: '2026-03-10', dueDate: '2026-03-24', lines: [{ desc: 'Consulting sessie', qty: 2, price: 445, btwRate: 21 }], status: 'betaald', paidDate: '2026-03-22' },
    ] as Invoice[],

    expenses: [
      { id: 'exp1', date: '2026-03-28', description: 'Google Workspace abonnement', category: 'Software', amount: 12.99, btwRate: 21, status: 'geboekt', supplierId: 'cred1' },
      { id: 'exp2', date: '2026-03-27', description: 'NS Business Card - maart', category: 'Transport', amount: 156.80, btwRate: 9, status: 'geboekt', supplierId: 'cred2' },
      { id: 'exp3', date: '2026-03-25', description: 'Bol.com bureaustoelen', category: 'Kantoor', amount: 349.00, btwRate: 21, status: 'review', supplierId: 'cred3' },
      { id: 'exp4', date: '2026-03-22', description: 'Facebook Ads campagne', category: 'Marketing', amount: 250.00, btwRate: 21, status: 'geboekt', supplierId: 'cred4' },
      { id: 'exp5', date: '2026-03-20', description: 'KPN zakelijk internet', category: 'Telefoon', amount: 45.00, btwRate: 21, status: 'geboekt', supplierId: 'cred5' },
      { id: 'exp6', date: '2026-03-15', description: 'Adobe Creative Cloud', category: 'Software', amount: 59.99, btwRate: 21, status: 'geboekt' },
      { id: 'exp7', date: '2026-03-10', description: 'Printkosten drukwerk', category: 'Kantoor', amount: 234.50, btwRate: 21, status: 'geboekt' },
      { id: 'exp8', date: '2026-02-28', description: 'Google Workspace abonnement', category: 'Software', amount: 12.99, btwRate: 21, status: 'geboekt' },
      { id: 'exp9', date: '2026-02-15', description: 'LinkedIn Premium', category: 'Marketing', amount: 29.99, btwRate: 21, status: 'geboekt' },
      { id: 'exp10', date: '2026-01-20', description: 'Kantoorbenodigdheden', category: 'Kantoor', amount: 87.50, btwRate: 21, status: 'geboekt' },
    ] as Expense[],

    debtors: [
      { id: 'deb1', name: 'Bakkerij de Vries BV', email: 'admin@bakkerijdevries.nl', kvk: '12345678', btw: 'NL123456789B01', iban: 'NL91ABNA0417164300', paymentTerm: 30, address: 'Broodweg 12', city: 'Utrecht' },
      { id: 'deb2', name: 'WebDesign Studio Amsterdam', email: 'info@webdesignstudio.nl', kvk: '23456789', btw: 'NL234567890B01', iban: 'NL02RABO0123456789', paymentTerm: 14, address: 'Keizersgracht 456', city: 'Amsterdam' },
      { id: 'deb3', name: 'Groene Hart Catering', email: 'finance@groenehartcatering.nl', kvk: '34567890', btw: 'NL345678901B01', iban: 'NL39INGB0001234567', paymentTerm: 30, address: 'Koekjesweg 8', city: 'Gouda' },
      { id: 'deb4', name: 'TechStart Nederland BV', email: 'ap@techstart.nl', kvk: '45678901', btw: 'NL456789012B01', iban: 'NL80TRIO0786543210', paymentTerm: 30, address: 'Startuplaan 1', city: 'Eindhoven' },
      { id: 'deb5', name: 'Van den Berg Consultancy', email: 'info@vdbergconsultancy.nl', kvk: '56789012', btw: 'NL567890123B01', iban: 'NL12KNAB0987654321', paymentTerm: 14, address: 'Consultweg 22', city: 'Den Haag' },
    ] as Debtor[],

    creditors: [
      { id: 'cred1', name: 'Google Ireland Ltd', email: 'billing@google.com', category: 'Software', iban: 'IE64IRCE92050112345678', paymentTerm: 30 },
      { id: 'cred2', name: 'NS Groep NV', email: 'facturen@ns.nl', category: 'Transport', iban: 'NL91ABNA0417164300', paymentTerm: 14 },
      { id: 'cred3', name: 'Bol.com BV', email: 'factuur@bol.com', category: 'Kantoor', iban: 'NL09INGB0664700610', paymentTerm: 14 },
      { id: 'cred4', name: 'Facebook Ireland Ltd', email: 'billing@fb.com', category: 'Marketing', iban: 'IE29AIBK93115212345678', paymentTerm: 30 },
      { id: 'cred5', name: 'KPN BV', email: 'factuur@kpn.com', category: 'Telefoon', iban: 'NL86INGB0002445588', paymentTerm: 14 },
    ] as Creditor[],

    bankTransactions: [
      { id: 'bt1', date: '2026-03-31', description: 'Betaling Bakkerij de Vries BV', amount: 2964.50, category: 'Omzet', matched: true, matchedInvoiceId: 'inv1' },
      { id: 'bt2', date: '2026-03-30', description: 'Google Ireland Ltd', amount: -12.99, category: 'Software', matched: true, matchedExpenseId: 'exp1' },
      { id: 'bt3', date: '2026-03-29', description: 'NS Groep NV', amount: -156.80, category: 'Transport', matched: true, matchedExpenseId: 'exp2' },
      { id: 'bt4', date: '2026-03-28', description: 'Betaling WebDesign Studio', amount: 4598, category: 'Omzet', matched: false },
      { id: 'bt5', date: '2026-03-27', description: 'Albert Heijn 1032', amount: -34.50, category: '', matched: false },
      { id: 'bt6', date: '2026-03-26', description: 'Bol.com BV', amount: -349.00, category: 'Kantoor', matched: true, matchedExpenseId: 'exp3' },
      { id: 'bt7', date: '2026-03-25', description: 'Facebook Ireland', amount: -250.00, category: 'Marketing', matched: true, matchedExpenseId: 'exp4' },
      { id: 'bt8', date: '2026-03-24', description: 'KPN BV', amount: -45.00, category: 'Telefoon', matched: true, matchedExpenseId: 'exp5' },
      { id: 'bt9', date: '2026-03-23', description: 'Onbekende afschrijving', amount: -1250.00, category: '', matched: false },
      { id: 'bt10', date: '2026-03-22', description: 'TechStart Nederland BV', amount: 5600, category: 'Omzet', matched: false },
    ] as BankTransaction[],
  }),

  getters: {
    activeCompany(state): Company {
      return state.companies.find(c => c.id === state.activeCompanyId) || state.companies[0]
    },

    // Financial calculations from real data
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

    // BTW calculations
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

    // Revenue by category
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
      const nums = state.invoices.map(i => parseInt(i.number.split('-').pop() || '0'))
      return `INV-2026-${String(Math.max(...nums) + 1).padStart(3, '0')}`
    },
  },

  actions: {
    switchCompany(id: string) {
      this.activeCompanyId = id
    },
    addInvoice(inv: Invoice) {
      this.invoices.unshift(inv)
    },
    updateInvoice(id: string, data: Partial<Invoice>) {
      const idx = this.invoices.findIndex(i => i.id === id)
      if (idx >= 0) Object.assign(this.invoices[idx], data)
    },
    addExpense(exp: Expense) {
      this.expenses.unshift(exp)
    },
    updateExpense(id: string, data: Partial<Expense>) {
      const idx = this.expenses.findIndex(e => e.id === id)
      if (idx >= 0) Object.assign(this.expenses[idx], data)
    },
    addDebtor(d: Debtor) {
      this.debtors.push(d)
    },
    addCreditor(c: Creditor) {
      this.creditors.push(c)
    },
    addCompany(c: Company) {
      this.companies.push(c)
    },
    updateBranding(companyId: string, branding: Partial<Branding>) {
      const company = this.companies.find(c => c.id === companyId)
      if (company) Object.assign(company.branding, branding)
    },
    addBankTransaction(tx: BankTransaction) {
      this.bankTransactions.unshift(tx)
    },
    matchTransaction(txId: string, type: 'invoice' | 'expense', targetId: string) {
      const tx = this.bankTransactions.find(t => t.id === txId)
      if (tx) {
        tx.matched = true
        if (type === 'invoice') tx.matchedInvoiceId = targetId
        else tx.matchedExpenseId = targetId
      }
    },
    importBulkData(items: { type: string; data: any }[]) {
      items.forEach(item => {
        if (item.type === 'invoice') this.addInvoice(item.data)
        else if (item.type === 'expense') this.addExpense(item.data)
        else if (item.type === 'bank') this.addBankTransaction(item.data)
      })
    },
  },
})
