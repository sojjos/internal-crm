import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { quotesApi, clientsApi } from '../services/api'
import {
  PlusIcon,
  PencilIcon,
  TrashIcon,
  PaperAirplaneIcon,
  CheckIcon,
  XMarkIcon,
  DocumentDuplicateIcon,
} from '@heroicons/react/24/outline'
import toast from 'react-hot-toast'

interface Quote {
  id: number
  quote_number: string
  client_id: number
  client_name: string
  subject: string
  quote_date: string
  valid_until: string
  status: string
  total_htva: number
  total_vat: number
  total_ttc: number
  invoice_id: number | null
  sent_at: string | null
  client_accepted_at: string | null
}

const statusMap: Record<string, { label: string; color: string }> = {
  BROUILLON: { label: 'Brouillon', color: 'bg-gray-100 text-gray-800' },
  ENVOYE: { label: 'Envoye', color: 'bg-blue-100 text-blue-800' },
  ACCEPTE: { label: 'Accepte', color: 'bg-green-100 text-green-800' },
  REFUSE: { label: 'Refuse', color: 'bg-red-100 text-red-800' },
  EXPIRE: { label: 'Expire', color: 'bg-orange-100 text-orange-800' },
  CONVERTI: { label: 'Converti en facture', color: 'bg-purple-100 text-purple-800' },
}

export default function Quotes() {
  const [quotes, setQuotes] = useState<Quote[]>([])
  const [loading, setLoading] = useState(true)
  const [statusFilter, setStatusFilter] = useState('')
  const [clientFilter, setClientFilter] = useState('')
  const [clients, setClients] = useState<{ id: number; name: string }[]>([])

  useEffect(() => {
    loadClients()
    loadQuotes()
  }, [])

  useEffect(() => {
    loadQuotes()
  }, [statusFilter, clientFilter])

  const loadClients = async () => {
    try {
      const response = await clientsApi.list({ is_active: true })
      setClients(response.data)
    } catch (error) {
      console.error('Error loading clients:', error)
    }
  }

  const loadQuotes = async () => {
    setLoading(true)
    try {
      const params: any = {}
      if (statusFilter) params.status = statusFilter
      if (clientFilter) params.client_id = clientFilter

      const response = await quotesApi.list(params)
      setQuotes(response.data)
    } catch (error) {
      toast.error('Erreur lors du chargement')
    } finally {
      setLoading(false)
    }
  }

  const handleSend = async (id: number) => {
    try {
      await quotesApi.send(id)
      toast.success('Devis envoye')
      loadQuotes()
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Erreur')
    }
  }

  const handleAccept = async (id: number) => {
    try {
      await quotesApi.accept(id)
      toast.success('Devis accepte')
      loadQuotes()
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Erreur')
    }
  }

  const handleReject = async (id: number) => {
    const reason = prompt('Raison du refus (optionnel):')
    try {
      await quotesApi.reject(id, reason || undefined)
      toast.success('Devis refuse')
      loadQuotes()
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Erreur')
    }
  }

  const handleConvert = async (id: number) => {
    if (!confirm('Convertir ce devis en facture ?')) return

    try {
      const response = await quotesApi.convertToInvoice(id)
      toast.success('Facture creee')
      loadQuotes()
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Erreur')
    }
  }

  const handleDelete = async (id: number) => {
    if (!confirm('Supprimer ce devis ?')) return

    try {
      await quotesApi.delete(id)
      toast.success('Devis supprime')
      loadQuotes()
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Erreur')
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

  const isExpiringSoon = (validUntil: string) => {
    const expiry = new Date(validUntil)
    const today = new Date()
    const diff = (expiry.getTime() - today.getTime()) / (1000 * 60 * 60 * 24)
    return diff <= 7 && diff > 0
  }

  // Summary stats
  const stats = {
    total: quotes.length,
    pending: quotes.filter(q => q.status === 'ENVOYE').length,
    accepted: quotes.filter(q => q.status === 'ACCEPTE').length,
    totalValue: quotes.filter(q => ['ENVOYE', 'ACCEPTE'].includes(q.status))
      .reduce((sum, q) => sum + q.total_ttc, 0),
  }

  if (loading && quotes.length === 0) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="page-title mb-0">Devis</h1>
        <Link to="/quotes/new" className="btn-primary flex items-center">
          <PlusIcon className="h-5 w-5 mr-1" />
          Nouveau devis
        </Link>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="card bg-blue-50">
          <p className="text-sm text-gray-600">Total devis</p>
          <p className="text-2xl font-bold text-blue-600">{stats.total}</p>
        </div>
        <div className="card bg-yellow-50">
          <p className="text-sm text-gray-600">En attente</p>
          <p className="text-2xl font-bold text-yellow-600">{stats.pending}</p>
        </div>
        <div className="card bg-green-50">
          <p className="text-sm text-gray-600">Acceptes</p>
          <p className="text-2xl font-bold text-green-600">{stats.accepted}</p>
        </div>
        <div className="card bg-purple-50">
          <p className="text-sm text-gray-600">Valeur en cours</p>
          <p className="text-2xl font-bold text-purple-600">{formatCurrency(stats.totalValue)}</p>
        </div>
      </div>

      {/* Filters */}
      <div className="card mb-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="label">Client</label>
            <select
              value={clientFilter}
              onChange={(e) => setClientFilter(e.target.value)}
              className="input"
            >
              <option value="">Tous</option>
              {clients.map((c) => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="label">Statut</label>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="input"
            >
              <option value="">Tous</option>
              {Object.entries(statusMap).map(([key, { label }]) => (
                <option key={key} value={key}>{label}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Quotes Table */}
      <div className="card">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead>
              <tr>
                <th className="table-header px-6 py-3">Numero</th>
                <th className="table-header px-6 py-3">Client</th>
                <th className="table-header px-6 py-3">Objet</th>
                <th className="table-header px-6 py-3">Date</th>
                <th className="table-header px-6 py-3">Validite</th>
                <th className="table-header px-6 py-3">Statut</th>
                <th className="table-header px-6 py-3 text-right">Montant TTC</th>
                <th className="table-header px-6 py-3">Actions</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {quotes.map((quote) => (
                <tr key={quote.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap font-mono text-sm">
                    {quote.quote_number}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {quote.client_name}
                  </td>
                  <td className="px-6 py-4">
                    <div className="max-w-xs truncate">{quote.subject}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {formatDate(quote.quote_date)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={isExpiringSoon(quote.valid_until) ? 'text-orange-600 font-medium' : ''}>
                      {formatDate(quote.valid_until)}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                      statusMap[quote.status]?.color || 'bg-gray-100'
                    }`}>
                      {statusMap[quote.status]?.label || quote.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right font-semibold">
                    {formatCurrency(quote.total_ttc)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center gap-2">
                      {quote.status === 'BROUILLON' && (
                        <>
                          <button
                            onClick={() => handleSend(quote.id)}
                            className="text-blue-600 hover:text-blue-800"
                            title="Envoyer"
                          >
                            <PaperAirplaneIcon className="h-5 w-5" />
                          </button>
                          <Link
                            to={`/quotes/${quote.id}`}
                            className="text-primary-600 hover:text-primary-800"
                          >
                            <PencilIcon className="h-5 w-5" />
                          </Link>
                          <button
                            onClick={() => handleDelete(quote.id)}
                            className="text-red-600 hover:text-red-800"
                          >
                            <TrashIcon className="h-5 w-5" />
                          </button>
                        </>
                      )}
                      {quote.status === 'ENVOYE' && (
                        <>
                          <button
                            onClick={() => handleAccept(quote.id)}
                            className="text-green-600 hover:text-green-800"
                            title="Accepter"
                          >
                            <CheckIcon className="h-5 w-5" />
                          </button>
                          <button
                            onClick={() => handleReject(quote.id)}
                            className="text-red-600 hover:text-red-800"
                            title="Refuser"
                          >
                            <XMarkIcon className="h-5 w-5" />
                          </button>
                        </>
                      )}
                      {quote.status === 'ACCEPTE' && !quote.invoice_id && (
                        <button
                          onClick={() => handleConvert(quote.id)}
                          className="text-purple-600 hover:text-purple-800"
                          title="Convertir en facture"
                        >
                          <DocumentDuplicateIcon className="h-5 w-5" />
                        </button>
                      )}
                      {quote.invoice_id && (
                        <Link
                          to={`/invoices/${quote.invoice_id}`}
                          className="text-purple-600 hover:text-purple-800 text-sm"
                        >
                          Voir facture
                        </Link>
                      )}
                      {!['BROUILLON'].includes(quote.status) && (
                        <Link
                          to={`/quotes/${quote.id}`}
                          className="text-gray-600 hover:text-gray-800"
                          title="Voir"
                        >
                          <PencilIcon className="h-5 w-5" />
                        </Link>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {quotes.length === 0 && (
            <p className="text-center py-8 text-gray-500">
              Aucun devis trouve
            </p>
          )}
        </div>
      </div>
    </div>
  )
}
