import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add token to requests if available
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Handle 401 errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default api

// API functions
export const authApi = {
  login: (email: string, password: string) => {
    const formData = new FormData()
    formData.append('username', email)
    formData.append('password', password)
    return api.post('/auth/login', formData)
  },
  me: () => api.get('/auth/me'),
  register: (data: any) => api.post('/auth/register', data),
  updateProfile: (data: any) => api.put('/auth/me', data),
  changePassword: (currentPassword: string, newPassword: string) =>
    api.post('/auth/me/change-password', {
      current_password: currentPassword,
      new_password: newPassword,
    }),
}

export const companyApi = {
  get: () => api.get('/company'),
  update: (data: any) => api.put('/company', data),
  uploadLogo: (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post('/company/logo', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
}

export const clientsApi = {
  list: (params?: any) => api.get('/clients', { params }),
  get: (id: number) => api.get(`/clients/${id}`),
  create: (data: any) => api.post('/clients', data),
  update: (id: number, data: any) => api.put(`/clients/${id}`, data),
  delete: (id: number) => api.delete(`/clients/${id}`),
}

export const suppliersApi = {
  list: (params?: any) => api.get('/suppliers', { params }),
  get: (id: number) => api.get(`/suppliers/${id}`),
  create: (data: any) => api.post('/suppliers', data),
  update: (id: number, data: any) => api.put(`/suppliers/${id}`, data),
  delete: (id: number) => api.delete(`/suppliers/${id}`),
}

export const articlesApi = {
  list: (params?: any) => api.get('/articles', { params }),
  get: (id: number) => api.get(`/articles/${id}`),
  create: (data: any) => api.post('/articles', data),
  update: (id: number, data: any) => api.put(`/articles/${id}`, data),
  delete: (id: number) => api.delete(`/articles/${id}`),
}

export const invoicesApi = {
  list: (params?: any) => api.get('/invoices', { params }),
  get: (id: number) => api.get(`/invoices/${id}`),
  create: (data: any) => api.post('/invoices', data),
  update: (id: number, data: any) => api.put(`/invoices/${id}`, data),
  delete: (id: number) => api.delete(`/invoices/${id}`),
  generatePdf: (id: number) => api.post(`/invoices/${id}/generate-pdf`),
  downloadPdf: (id: number) => api.get(`/invoices/${id}/download-pdf`, { responseType: 'blob' }),
  send: (id: number, params?: any) => api.post(`/invoices/${id}/send`, null, { params }),
  markPaid: (id: number, data?: any) => api.post(`/invoices/${id}/mark-paid`, null, { params: data }),
}

export const expensesApi = {
  list: (params?: any) => api.get('/expenses', { params }),
  get: (id: number) => api.get(`/expenses/${id}`),
  create: (data: any) => api.post('/expenses', data),
  update: (id: number, data: any) => api.put(`/expenses/${id}`, data),
  delete: (id: number) => api.delete(`/expenses/${id}`),
  uploadReceipt: (id: number, file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post(`/expenses/${id}/receipt`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  types: {
    list: (params?: any) => api.get('/expenses/types', { params }),
    create: (data: any) => api.post('/expenses/types', data),
    update: (id: number, data: any) => api.put(`/expenses/types/${id}`, data),
  },
}

export const collaboratorsApi = {
  list: (params?: any) => api.get('/collaborators', { params }),
  get: (id: number) => api.get(`/collaborators/${id}`),
  create: (data: any) => api.post('/collaborators', data),
  update: (id: number, data: any) => api.put(`/collaborators/${id}`, data),
  delete: (id: number) => api.delete(`/collaborators/${id}`),
  payslips: (id: number) => api.get(`/collaborators/${id}/payslips`),
  uploadPayslip: (id: number, period: string, file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post(`/collaborators/${id}/payslips?period=${period}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
}

export const payrollApi = {
  periods: (params?: any) => api.get('/collaborators/payroll/periods', { params }),
  createPeriod: (data: any) => api.post('/collaborators/payroll/periods', data),
  summary: (period: string) => api.get(`/collaborators/payroll/periods/${period}/summary`),
  export: (period: string) => api.get(`/collaborators/payroll/periods/${period}/export`, {
    responseType: 'blob',
  }),
}

export const reportsApi = {
  dashboard: () => api.get('/reports/dashboard'),
  monthly: (year: number) => api.get('/reports/monthly', { params: { year } }),
  vat: (dateFrom: string, dateTo: string) =>
    api.get('/reports/vat', { params: { date_from: dateFrom, date_to: dateTo } }),
  exportInvoices: (dateFrom: string, dateTo: string) =>
    api.get('/reports/export/invoices', {
      params: { date_from: dateFrom, date_to: dateTo },
      responseType: 'blob',
    }),
  exportExpenses: (dateFrom: string, dateTo: string) =>
    api.get('/reports/export/expenses', {
      params: { date_from: dateFrom, date_to: dateTo },
      responseType: 'blob',
    }),
  exportVat: (dateFrom: string, dateTo: string) =>
    api.get('/reports/export/vat', {
      params: { date_from: dateFrom, date_to: dateTo },
      responseType: 'blob',
    }),
}

export const usersApi = {
  list: () => api.get('/users'),
  get: (id: number) => api.get(`/users/${id}`),
  update: (id: number, data: any) => api.put(`/users/${id}`, data),
  delete: (id: number) => api.delete(`/users/${id}`),
}

export const emailsApi = {
  // Accounts
  accounts: {
    list: () => api.get('/emails/accounts'),
    get: (id: number) => api.get(`/emails/accounts/${id}`),
    create: (data: any) => api.post('/emails/accounts', data),
    update: (id: number, data: any) => api.put(`/emails/accounts/${id}`, data),
    delete: (id: number) => api.delete(`/emails/accounts/${id}`),
    test: (data: any) => api.post('/emails/accounts/test', data),
  },
  // Emails
  list: (params?: any) => api.get('/emails', { params }),
  get: (id: number) => api.get(`/emails/${id}`),
  send: (data: FormData) => api.post('/emails/send', data, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }),
  markRead: (id: number, isRead: boolean = true) =>
    api.post(`/emails/${id}/mark-read`, null, { params: { is_read: isRead } }),
  star: (id: number) => api.post(`/emails/${id}/star`),
  delete: (id: number) => api.delete(`/emails/${id}`),
  sync: (accountId: number, folder: string = 'INBOX') =>
    api.post('/emails/sync', { account_id: accountId, folder }),
  folders: (accountId: number) => api.get('/emails/folders', { params: { account_id: accountId } }),
  // Templates
  templates: {
    list: (templateType?: string) => api.get('/emails/templates', { params: { template_type: templateType } }),
    create: (data: any) => api.post('/emails/templates', data),
    update: (id: number, data: any) => api.put(`/emails/templates/${id}`, data),
    delete: (id: number) => api.delete(`/emails/templates/${id}`),
  },
}

export const purchasesApi = {
  // Categories
  categories: {
    list: (params?: any) => api.get('/purchases/categories', { params }),
    get: (id: number) => api.get(`/purchases/categories/${id}`),
    create: (data: any) => api.post('/purchases/categories', data),
    update: (id: number, data: any) => api.put(`/purchases/categories/${id}`, data),
    delete: (id: number) => api.delete(`/purchases/categories/${id}`),
    getDefaults: (id: number) => api.get(`/purchases/categories/${id}/defaults`),
  },
  // Contracts
  contracts: {
    list: (params?: any) => api.get('/purchases/contracts', { params }),
    get: (id: number) => api.get(`/purchases/contracts/${id}`),
    create: (data: any) => api.post('/purchases/contracts', data),
    update: (id: number, data: any) => api.put(`/purchases/contracts/${id}`, data),
    delete: (id: number) => api.delete(`/purchases/contracts/${id}`),
    billingDates: (id: number) => api.get(`/purchases/contracts/${id}/billing-dates`),
    generatePurchases: (forDate: string) =>
      api.post('/purchases/contracts/generate-purchases', null, { params: { for_date: forDate } }),
  },
  // Purchases
  list: (params?: any) => api.get('/purchases', { params }),
  get: (id: number) => api.get(`/purchases/${id}`),
  create: (data: any) => api.post('/purchases', data),
  update: (id: number, data: any) => api.put(`/purchases/${id}`, data),
  delete: (id: number) => api.delete(`/purchases/${id}`),
  validate: (id: number) => api.post(`/purchases/${id}/validate`),
  uploadDocument: (id: number, file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post(`/purchases/${id}/document`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  calculate: (data: any) => api.post('/purchases/calculate', data),
  // Fixed Assets
  assets: {
    list: (params?: any) => api.get('/purchases/assets', { params }),
    get: (id: number) => api.get(`/purchases/assets/${id}`),
    create: (data: any) => api.post('/purchases/assets', data),
    update: (id: number, data: any) => api.put(`/purchases/assets/${id}`, data),
    delete: (id: number) => api.delete(`/purchases/assets/${id}`),
    regenerateDepreciation: (id: number) => api.post(`/purchases/assets/${id}/regenerate-depreciation`),
  },
  // Reports
  reports: {
    summary: (startDate: string, endDate: string) =>
      api.get('/purchases/reports/summary', { params: { start_date: startDate, end_date: endDate } }),
    vat: (startDate: string, endDate: string) =>
      api.get('/purchases/reports/vat', { params: { start_date: startDate, end_date: endDate } }),
    pcmn: (startDate: string, endDate: string) =>
      api.get('/purchases/reports/pcmn', { params: { start_date: startDate, end_date: endDate } }),
    investments: (asOfDate: string) =>
      api.get('/purchases/reports/investments', { params: { as_of_date: asOfDate } }),
  },
}

// Document Management (GED)
export const documentsApi = {
  categories: {
    list: (params?: any) => api.get('/documents/categories', { params }),
    create: (data: any) => api.post('/documents/categories', data),
    update: (id: number, data: any) => api.put(`/documents/categories/${id}`, data),
    delete: (id: number) => api.delete(`/documents/categories/${id}`),
  },
  list: (params?: any) => api.get('/documents', { params }),
  get: (id: number) => api.get(`/documents/${id}`),
  create: (data: FormData) => api.post('/documents', data, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }),
  update: (id: number, data: any) => api.put(`/documents/${id}`, data),
  delete: (id: number) => api.delete(`/documents/${id}`),
  expiring: (days: number = 30) => api.get('/documents/expiring', { params: { days } }),
}

// Treasury & Cashflow
export const treasuryApi = {
  accounts: {
    list: (params?: any) => api.get('/treasury/accounts', { params }),
    get: (id: number) => api.get(`/treasury/accounts/${id}`),
    create: (data: any) => api.post('/treasury/accounts', data),
    update: (id: number, data: any) => api.put(`/treasury/accounts/${id}`, data),
    delete: (id: number) => api.delete(`/treasury/accounts/${id}`),
  },
  transactions: {
    list: (params?: any) => api.get('/treasury/transactions', { params }),
    get: (id: number) => api.get(`/treasury/transactions/${id}`),
    create: (data: any) => api.post('/treasury/transactions', data),
    update: (id: number, data: any) => api.put(`/treasury/transactions/${id}`, data),
    delete: (id: number) => api.delete(`/treasury/transactions/${id}`),
  },
  forecast: (accountId: number, months: number = 3) =>
    api.get('/treasury/forecast', { params: { account_id: accountId, months } }),
  weeklyForecast: (accountId: number, weeks: number = 8) =>
    api.get('/treasury/weekly-forecast', { params: { account_id: accountId, weeks } }),
  syncFromInvoices: (accountId: number) =>
    api.post('/treasury/sync-from-invoices', null, { params: { account_id: accountId } }),
}

// Stock Management
export const stockApi = {
  locations: {
    list: (params?: any) => api.get('/stock/locations', { params }),
    get: (id: number) => api.get(`/stock/locations/${id}`),
    create: (data: any) => api.post('/stock/locations', data),
    update: (id: number, data: any) => api.put(`/stock/locations/${id}`, data),
    delete: (id: number) => api.delete(`/stock/locations/${id}`),
  },
  categories: {
    list: (params?: any) => api.get('/stock/categories', { params }),
    get: (id: number) => api.get(`/stock/categories/${id}`),
    create: (data: any) => api.post('/stock/categories', data),
    update: (id: number, data: any) => api.put(`/stock/categories/${id}`, data),
    delete: (id: number) => api.delete(`/stock/categories/${id}`),
  },
  articles: {
    list: (params?: any) => api.get('/stock/articles', { params }),
    get: (id: number) => api.get(`/stock/articles/${id}`),
    create: (data: any) => api.post('/stock/articles', data),
    update: (id: number, data: any) => api.put(`/stock/articles/${id}`, data),
    delete: (id: number) => api.delete(`/stock/articles/${id}`),
  },
  items: {
    list: (params?: any) => api.get('/stock/items', { params }),
    get: (id: number) => api.get(`/stock/items/${id}`),
    create: (data: any) => api.post('/stock/items', data),
    update: (id: number, data: any) => api.put(`/stock/items/${id}`, data),
    delete: (id: number) => api.delete(`/stock/items/${id}`),
  },
  movements: {
    list: (params?: any) => api.get('/stock/movements', { params }),
    create: (data: any) => api.post('/stock/movements', data),
  },
  alerts: () => api.get('/stock/alerts'),
}

// Interventions & Planning
export const interventionsApi = {
  list: (params?: any) => api.get('/interventions', { params }),
  get: (id: number) => api.get(`/interventions/${id}`),
  create: (data: any) => api.post('/interventions', data),
  update: (id: number, data: any) => api.put(`/interventions/${id}`, data),
  delete: (id: number) => api.delete(`/interventions/${id}`),
  start: (id: number) => api.post(`/interventions/${id}/start`),
  complete: (id: number, data?: any) => api.post(`/interventions/${id}/complete`, data),
  createInvoice: (id: number) => api.post(`/interventions/${id}/create-invoice`),
  calendar: (params?: any) => api.get('/interventions/calendar', { params }),
  lines: {
    add: (interventionId: number, data: any) =>
      api.post(`/interventions/${interventionId}/lines`, data),
    update: (interventionId: number, lineId: number, data: any) =>
      api.put(`/interventions/${interventionId}/lines/${lineId}`, data),
    delete: (interventionId: number, lineId: number) =>
      api.delete(`/interventions/${interventionId}/lines/${lineId}`),
  },
}

// Quotes (Devis)
export const quotesApi = {
  list: (params?: any) => api.get('/quotes', { params }),
  get: (id: number) => api.get(`/quotes/${id}`),
  create: (data: any) => api.post('/quotes', data),
  update: (id: number, data: any) => api.put(`/quotes/${id}`, data),
  delete: (id: number) => api.delete(`/quotes/${id}`),
  send: (id: number) => api.post(`/quotes/${id}/send`),
  accept: (id: number) => api.post(`/quotes/${id}/accept`),
  reject: (id: number, reason?: string) =>
    api.post(`/quotes/${id}/reject`, null, { params: { reason } }),
  convertToInvoice: (id: number, data?: any) =>
    api.post(`/quotes/${id}/convert-to-invoice`, data),
  lines: {
    add: (quoteId: number, data: any) => api.post(`/quotes/${quoteId}/lines`, data),
    update: (quoteId: number, lineId: number, data: any) =>
      api.put(`/quotes/${quoteId}/lines/${lineId}`, data),
    delete: (quoteId: number, lineId: number) =>
      api.delete(`/quotes/${quoteId}/lines/${lineId}`),
  },
}

// CRM & Pipeline
export const crmApi = {
  tags: {
    list: (params?: any) => api.get('/crm/tags', { params }),
    create: (data: any) => api.post('/crm/tags', data),
    update: (id: number, data: any) => api.put(`/crm/tags/${id}`, data),
    delete: (id: number) => api.delete(`/crm/tags/${id}`),
    assign: (tagId: number, clientId: number) =>
      api.post(`/crm/tags/${tagId}/clients/${clientId}`),
    remove: (tagId: number, clientId: number) =>
      api.delete(`/crm/tags/${tagId}/clients/${clientId}`),
  },
  opportunities: {
    list: (params?: any) => api.get('/crm/opportunities', { params }),
    get: (id: number) => api.get(`/crm/opportunities/${id}`),
    create: (data: any) => api.post('/crm/opportunities', data),
    update: (id: number, data: any) => api.put(`/crm/opportunities/${id}`, data),
    delete: (id: number) => api.delete(`/crm/opportunities/${id}`),
    updateStage: (id: number, stage: string) =>
      api.put(`/crm/opportunities/${id}/stage`, null, { params: { stage } }),
  },
  activities: {
    list: (params?: any) => api.get('/crm/activities', { params }),
    create: (data: any) => api.post('/crm/activities', data),
    delete: (id: number) => api.delete(`/crm/activities/${id}`),
  },
  tasks: {
    list: (params?: any) => api.get('/crm/tasks', { params }),
    get: (id: number) => api.get(`/crm/tasks/${id}`),
    create: (data: any) => api.post('/crm/tasks', data),
    update: (id: number, data: any) => api.put(`/crm/tasks/${id}`, data),
    delete: (id: number) => api.delete(`/crm/tasks/${id}`),
    complete: (id: number, notes?: string) =>
      api.post(`/crm/tasks/${id}/complete`, null, { params: { notes } }),
  },
  dashboard: () => api.get('/crm/dashboard'),
  pipeline: () => api.get('/crm/pipeline'),
  convertToClient: (opportunityId: number) =>
    api.post(`/crm/opportunities/${opportunityId}/convert-to-client`),
}

// Annual Accounts & XBRL
export const annualAccountsApi = {
  fiscalYears: {
    list: () => api.get('/annual-accounts/fiscal-years'),
    get: (id: number) => api.get(`/annual-accounts/fiscal-years/${id}`),
    create: (data: any) => api.post('/annual-accounts/fiscal-years', data),
    update: (id: number, data: any) => api.put(`/annual-accounts/fiscal-years/${id}`, data),
    close: (id: number) => api.post(`/annual-accounts/fiscal-years/${id}/close`),
  },
  list: (params?: any) => api.get('/annual-accounts', { params }),
  get: (id: number) => api.get(`/annual-accounts/${id}`),
  create: (data: any) => api.post('/annual-accounts', data),
  balanceSheet: (id: number) => api.get(`/annual-accounts/${id}/balance-sheet`),
  updateBalanceSheetItem: (accountId: number, itemId: number, data: any) =>
    api.put(`/annual-accounts/${accountId}/balance-sheet/${itemId}`, data),
  incomeStatement: (id: number) => api.get(`/annual-accounts/${id}/income-statement`),
  calculate: (id: number) => api.post(`/annual-accounts/${id}/calculate`),
  validate: (id: number) => api.post(`/annual-accounts/${id}/validate`),
  generateXbrl: (id: number) => api.post(`/annual-accounts/${id}/generate-xbrl`, null, {
    responseType: 'blob',
  }),
  structure: {
    balanceSheet: () => api.get('/annual-accounts/structure/balance-sheet'),
    incomeStatement: () => api.get('/annual-accounts/structure/income-statement'),
  },
}

// Fiscal & ISoc
export const fiscalApi = {
  declarations: {
    list: (params?: any) => api.get('/fiscal/declarations', { params }),
    get: (id: number) => api.get(`/fiscal/declarations/${id}`),
    create: (data: any) => api.post('/fiscal/declarations', data),
    delete: (id: number) => api.delete(`/fiscal/declarations/${id}`),
    items: (id: number) => api.get(`/fiscal/declarations/${id}/items`),
    submitBiztax: (id: number) => api.post(`/fiscal/declarations/${id}/biztax/submit`),
  },
  isoc: {
    get: (declarationId: number) => api.get(`/fiscal/declarations/${declarationId}/isoc`),
    update: (declarationId: number, data: any) =>
      api.put(`/fiscal/declarations/${declarationId}/isoc`, data),
    calculate: (declarationId: number) =>
      api.post(`/fiscal/declarations/${declarationId}/isoc/calculate`),
  },
  prepayments: {
    list: (params?: any) => api.get('/fiscal/prepayments', { params }),
    create: (data: any) => api.post('/fiscal/prepayments', data),
    update: (id: number, data: any) => api.put(`/fiscal/prepayments/${id}`, data),
  },
  mappings: {
    list: (params?: any) => api.get('/fiscal/mappings', { params }),
    create: (data: any) => api.post('/fiscal/mappings', data),
    delete: (id: number) => api.delete(`/fiscal/mappings/${id}`),
  },
  dnaCategories: () => api.get('/fiscal/dna-categories'),
  isocStructure: () => api.get('/fiscal/isoc-structure'),
  prepaymentRates: () => api.get('/fiscal/prepayment-rates'),
}

// Legal Documents
export const legalApi = {
  meetings: {
    list: (params?: any) => api.get('/legal/meetings', { params }),
    get: (id: number) => api.get(`/legal/meetings/${id}`),
    create: (data: any) => api.post('/legal/meetings', data),
    update: (id: number, data: any) => api.put(`/legal/meetings/${id}`, data),
    approve: (id: number, president: string, secretary: string) =>
      api.post(`/legal/meetings/${id}/approve`, null, { params: { president_name: president, secretary_name: secretary } }),
    generatePv: (id: number) => api.post(`/legal/meetings/${id}/generate-pv`, null, {
      responseType: 'blob',
    }),
  },
  resolutions: {
    list: (meetingId: number) => api.get(`/legal/meetings/${meetingId}/resolutions`),
    create: (meetingId: number, data: any) =>
      api.post(`/legal/meetings/${meetingId}/resolutions`, data),
    vote: (meetingId: number, resId: number, votesFor: number, votesAgainst: number, abstain: number = 0) =>
      api.put(`/legal/meetings/${meetingId}/resolutions/${resId}/vote`, null, {
        params: { votes_for: votesFor, votes_against: votesAgainst, votes_abstain: abstain }
      }),
  },
  managementReports: {
    list: (params?: any) => api.get('/legal/management-reports', { params }),
    get: (id: number) => api.get(`/legal/management-reports/${id}`),
    create: (data: any) => api.post('/legal/management-reports', data),
    updateSection: (id: number, sectionName: string, content: string) =>
      api.put(`/legal/management-reports/${id}/section`, null, {
        params: { section_name: sectionName, content }
      }),
  },
  officers: {
    list: (params?: any) => api.get('/legal/officers', { params }),
    create: (data: any) => api.post('/legal/officers', data),
    update: (id: number, data: any) => api.put(`/legal/officers/${id}`, data),
    endMandate: (id: number, endDate: string) =>
      api.post(`/legal/officers/${id}/end-mandate`, null, { params: { end_date: endDate } }),
  },
  publications: {
    list: (params?: any) => api.get('/legal/publications', { params }),
    create: (data: any) => api.post('/legal/publications', data),
    file: (id: number) => api.post(`/legal/publications/${id}/file`),
  },
  ubo: {
    list: (params?: any) => api.get('/legal/ubo', { params }),
    create: (data: any) => api.post('/legal/ubo', data),
    declareSpf: (id: number) => api.post(`/legal/ubo/${id}/declare-spf`),
  },
  templates: () => api.get('/legal/templates'),
  functions: () => api.get('/legal/functions'),
}

// Integrations (Belcotax, Caseware, Imports)
export const integrationsApi = {
  config: {
    list: (params?: any) => api.get('/integrations/config', { params }),
    create: (data: any) => api.post('/integrations/config', data),
    update: (id: number, data: any) => api.put(`/integrations/config/${id}`, data),
    test: (id: number) => api.post(`/integrations/config/${id}/test`),
    activate: (id: number) => api.post(`/integrations/config/${id}/activate`),
  },
  belcotax: {
    declarations: {
      list: (params?: any) => api.get('/integrations/belcotax/declarations', { params }),
      get: (id: number) => api.get(`/integrations/belcotax/declarations/${id}`),
      create: (data: any) => api.post('/integrations/belcotax/declarations', data),
      fiches: (declId: number) => api.get(`/integrations/belcotax/declarations/${declId}/fiches`),
      addFiche: (declId: number, data: any) =>
        api.post(`/integrations/belcotax/declarations/${declId}/fiches`, data),
      validate: (declId: number) =>
        api.post(`/integrations/belcotax/declarations/${declId}/validate`),
      generateXml: (declId: number) =>
        api.post(`/integrations/belcotax/declarations/${declId}/generate-xml`, null, {
          responseType: 'blob',
        }),
    },
  },
  imports: {
    list: (params?: any) => api.get('/integrations/imports', { params }),
    upload: (sourceType: string, file: File, fiscalYearId?: number) => {
      const formData = new FormData()
      formData.append('source_type', sourceType)
      formData.append('file', file)
      if (fiscalYearId) formData.append('fiscal_year_id', fiscalYearId.toString())
      return api.post('/integrations/imports/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
    },
    process: (importId: number, columnMapping?: any) =>
      api.post(`/integrations/imports/${importId}/process`, { column_mapping: columnMapping }),
    entries: (importId: number, params?: any) =>
      api.get(`/integrations/imports/${importId}/entries`, { params }),
  },
  caseware: {
    projects: {
      list: (params?: any) => api.get('/integrations/caseware/projects', { params }),
      create: (data: any) => api.post('/integrations/caseware/projects', data),
      sync: (projectId: number, syncType: string = 'full') =>
        api.post(`/integrations/caseware/projects/${projectId}/sync`, null, {
          params: { sync_type: syncType }
        }),
    },
  },
  coda: {
    list: (params?: any) => api.get('/integrations/coda', { params }),
    upload: (file: File, bankAccountId?: number) => {
      const formData = new FormData()
      formData.append('file', file)
      if (bankAccountId) formData.append('bank_account_id', bankAccountId.toString())
      return api.post('/integrations/coda/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
    },
    process: (importId: number) => api.post(`/integrations/coda/${importId}/process`),
    movements: (importId: number, params?: any) =>
      api.get(`/integrations/coda/${importId}/movements`, { params }),
  },
  importMappings: () => api.get('/integrations/import-mappings'),
  codaCodes: () => api.get('/integrations/coda-codes'),
}
