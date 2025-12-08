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
