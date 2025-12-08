import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { invoicesApi } from '../services/api'
import { PlusIcon, EyeIcon } from '@heroicons/react/24/outline'
import toast from 'react-hot-toast'

interface Invoice {
  id: number
  invoice_number: string
  client_id: number
  invoice_date: string
  due_date: string
  status: string
  total_htva: number
  total_tvac: number
}

const statusLabels: Record<string, string> = {
  draft: 'Brouillon',
  sent: 'Envoyée',
  paid: 'Payée',
  overdue: 'En retard',
  cancelled: 'Annulée',
}

const statusColors: Record<string, string> = {
  draft: 'bg-gray-100 text-gray-800',
  sent: 'bg-blue-100 text-blue-800',
  paid: 'bg-green-100 text-green-800',
  overdue: 'bg-red-100 text-red-800',
  cancelled: 'bg-gray-100 text-gray-500',
}

export default function Invoices() {
  const [invoices, setInvoices] = useState<Invoice[]>([])
  const [loading, setLoading] = useState(true)
  const [statusFilter, setStatusFilter] = useState('')

  useEffect(() => {
    loadInvoices()
  }, [statusFilter])

  const loadInvoices = async () => {
    try {
      const params: any = {}
      if (statusFilter) params.status_filter = statusFilter
      const response = await invoicesApi.list(params)
      setInvoices(response.data)
    } catch (error) {
      toast.error('Erreur lors du chargement des factures')
    } finally {
      setLoading(false)
    }
  }

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('fr-BE')
  }

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('fr-BE', {
      style: 'currency',
      currency: 'EUR',
    }).format(amount)
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="page-title mb-0">Factures</h1>
        <Link to="/invoices/new" className="btn-primary flex items-center">
          <PlusIcon className="h-5 w-5 mr-1" />
          Nouvelle facture
        </Link>
      </div>

      <div className="card">
        <div className="mb-4">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="input max-w-xs"
          >
            <option value="">Tous les statuts</option>
            <option value="draft">Brouillon</option>
            <option value="sent">Envoyée</option>
            <option value="paid">Payée</option>
            <option value="overdue">En retard</option>
            <option value="cancelled">Annulée</option>
          </select>
        </div>

        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead>
              <tr>
                <th className="table-header px-6 py-3">Numéro</th>
                <th className="table-header px-6 py-3">Date</th>
                <th className="table-header px-6 py-3">Échéance</th>
                <th className="table-header px-6 py-3">Montant TVAC</th>
                <th className="table-header px-6 py-3">Statut</th>
                <th className="table-header px-6 py-3">Actions</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {invoices.map((invoice) => (
                <tr key={invoice.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap font-medium">
                    {invoice.invoice_number}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-gray-500">
                    {formatDate(invoice.invoice_date)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-gray-500">
                    {formatDate(invoice.due_date)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap font-semibold">
                    {formatCurrency(invoice.total_tvac)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span
                      className={`px-2 py-1 text-xs font-medium rounded-full ${
                        statusColors[invoice.status]
                      }`}
                    >
                      {statusLabels[invoice.status] || invoice.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <Link
                      to={`/invoices/${invoice.id}`}
                      className="text-primary-600 hover:text-primary-800 mr-3"
                    >
                      <EyeIcon className="h-5 w-5 inline" />
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {invoices.length === 0 && (
            <p className="text-center py-8 text-gray-500">Aucune facture trouvée</p>
          )}
        </div>
      </div>
    </div>
  )
}
