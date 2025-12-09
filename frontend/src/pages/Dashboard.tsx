import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { reportsApi, invoicesApi, quotesApi, interventionsApi } from '../services/api'
import { useAuth } from '../context/AuthContext'
import {
  CurrencyEuroIcon,
  DocumentTextIcon,
  ExclamationTriangleIcon,
  ArrowTrendingUpIcon,
  ClockIcon,
  CalendarDaysIcon,
  WrenchScrewdriverIcon,
  DocumentDuplicateIcon,
  UserGroupIcon,
  ChartBarIcon,
} from '@heroicons/react/24/outline'

interface DashboardStats {
  total_revenue_ytd: number
  total_expenses_ytd: number
  outstanding_invoices: number
  overdue_invoices: number
  invoices_this_month: number
  expenses_this_month: number
}

interface RecentInvoice {
  id: number
  invoice_number: string
  client_name: string
  total_tvac: number
  status: string
  invoice_date: string
}

interface RecentQuote {
  id: number
  quote_number: string
  client_name: string
  total_tvac: number
  status: string
  quote_date: string
}

interface RecentIntervention {
  id: number
  reference: string
  client_name: string
  title: string
  status: string
  scheduled_date: string
}

export default function Dashboard() {
  const { user } = useAuth()
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [recentInvoices, setRecentInvoices] = useState<RecentInvoice[]>([])
  const [recentQuotes, setRecentQuotes] = useState<RecentQuote[]>([])
  const [recentInterventions, setRecentInterventions] = useState<RecentIntervention[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadDashboardData()
  }, [])

  const loadDashboardData = async () => {
    try {
      const [statsRes, invoicesRes, quotesRes, interventionsRes] = await Promise.all([
        reportsApi.dashboard(),
        invoicesApi.list({ limit: 5 }).catch(() => ({ data: [] })),
        quotesApi.list({ limit: 5 }).catch(() => ({ data: [] })),
        interventionsApi.list({ limit: 5 }).catch(() => ({ data: [] })),
      ])
      setStats(statsRes.data)
      setRecentInvoices(invoicesRes.data.slice(0, 5))
      setRecentQuotes(quotesRes.data.slice(0, 5))
      setRecentInterventions(interventionsRes.data.slice(0, 5))
    } catch (error) {
      console.error('Failed to load dashboard data', error)
    } finally {
      setLoading(false)
    }
  }

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('fr-BE', {
      style: 'currency',
      currency: 'EUR',
    }).format(amount)
  }

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('fr-BE')
  }

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      DRAFT: 'bg-gray-100 text-gray-800',
      BROUILLON: 'bg-gray-100 text-gray-800',
      SENT: 'bg-blue-100 text-blue-800',
      ENVOYE: 'bg-blue-100 text-blue-800',
      PAID: 'bg-green-100 text-green-800',
      ACCEPTE: 'bg-green-100 text-green-800',
      TERMINE: 'bg-green-100 text-green-800',
      OVERDUE: 'bg-red-100 text-red-800',
      REFUSE: 'bg-red-100 text-red-800',
      ANNULE: 'bg-red-100 text-red-800',
      PLANIFIE: 'bg-blue-100 text-blue-800',
      EN_COURS: 'bg-yellow-100 text-yellow-800',
    }
    return colors[status] || 'bg-gray-100 text-gray-800'
  }

  const getStatusLabel = (status: string) => {
    const labels: Record<string, string> = {
      DRAFT: 'Brouillon',
      BROUILLON: 'Brouillon',
      SENT: 'Envoyee',
      ENVOYE: 'Envoye',
      PAID: 'Payee',
      ACCEPTE: 'Accepte',
      TERMINE: 'Termine',
      OVERDUE: 'En retard',
      REFUSE: 'Refuse',
      ANNULE: 'Annule',
      PLANIFIE: 'Planifie',
      EN_COURS: 'En cours',
      FACTURE: 'Facture',
      CONVERTI: 'Converti',
    }
    return labels[status] || status
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
        <div>
          <h1 className="page-title mb-0">Tableau de bord</h1>
          <p className="text-gray-600">
            Bienvenue, {user?.first_name || 'Utilisateur'}
          </p>
        </div>
        <div className="text-right text-sm text-gray-500">
          {new Date().toLocaleDateString('fr-BE', {
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric',
          })}
        </div>
      </div>

      {/* Stats cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div className="card hover:shadow-lg transition-shadow">
          <div className="flex items-center">
            <div className="p-3 rounded-full bg-green-100 text-green-600">
              <ArrowTrendingUpIcon className="h-6 w-6" />
            </div>
            <div className="ml-4">
              <p className="text-sm text-gray-500">CA Annee</p>
              <p className="text-xl font-semibold text-green-600">
                {formatCurrency(stats?.total_revenue_ytd || 0)}
              </p>
            </div>
          </div>
        </div>

        <div className="card hover:shadow-lg transition-shadow">
          <div className="flex items-center">
            <div className="p-3 rounded-full bg-red-100 text-red-600">
              <CurrencyEuroIcon className="h-6 w-6" />
            </div>
            <div className="ml-4">
              <p className="text-sm text-gray-500">Depenses Annee</p>
              <p className="text-xl font-semibold text-red-600">
                {formatCurrency(stats?.total_expenses_ytd || 0)}
              </p>
            </div>
          </div>
        </div>

        <div className="card hover:shadow-lg transition-shadow">
          <div className="flex items-center">
            <div className="p-3 rounded-full bg-blue-100 text-blue-600">
              <DocumentTextIcon className="h-6 w-6" />
            </div>
            <div className="ml-4">
              <p className="text-sm text-gray-500">Factures en attente</p>
              <p className="text-xl font-semibold text-blue-600">
                {formatCurrency(stats?.outstanding_invoices || 0)}
              </p>
            </div>
          </div>
        </div>

        <div className="card hover:shadow-lg transition-shadow">
          <div className="flex items-center">
            <div className="p-3 rounded-full bg-orange-100 text-orange-600">
              <ExclamationTriangleIcon className="h-6 w-6" />
            </div>
            <div className="ml-4">
              <p className="text-sm text-gray-500">Factures en retard</p>
              <p className="text-xl font-semibold text-orange-600">
                {formatCurrency(stats?.overdue_invoices || 0)}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Result card */}
      <div className="card mb-8 bg-gradient-to-r from-primary-500 to-primary-700 text-white">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold mb-1">Resultat net estime</h2>
            <p className="text-3xl font-bold">
              {formatCurrency(
                (stats?.total_revenue_ytd || 0) - (stats?.total_expenses_ytd || 0)
              )}
            </p>
            <p className="text-sm opacity-75 mt-1">
              Revenus - Depenses (annee en cours)
            </p>
          </div>
          <div className="text-right">
            <div className="flex items-center mb-2">
              <ClockIcon className="h-5 w-5 mr-2 opacity-75" />
              <span>{stats?.invoices_this_month || 0} factures ce mois</span>
            </div>
            <div className="flex items-center">
              <CalendarDaysIcon className="h-5 w-5 mr-2 opacity-75" />
              <span>{stats?.expenses_this_month || 0} notes de frais ce mois</span>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        {/* Quick actions */}
        <div className="card">
          <h2 className="text-lg font-semibold mb-4 flex items-center">
            <ChartBarIcon className="h-5 w-5 mr-2 text-primary-600" />
            Actions rapides
          </h2>
          <div className="space-y-2">
            <Link
              to="/invoices/new"
              className="block w-full text-left px-4 py-3 rounded-lg bg-primary-50 text-primary-700 hover:bg-primary-100 transition-colors"
            >
              <DocumentTextIcon className="h-5 w-5 inline mr-2" />
              Nouvelle facture
            </Link>
            <Link
              to="/quotes/new"
              className="block w-full text-left px-4 py-3 rounded-lg bg-purple-50 text-purple-700 hover:bg-purple-100 transition-colors"
            >
              <DocumentDuplicateIcon className="h-5 w-5 inline mr-2" />
              Nouveau devis
            </Link>
            <Link
              to="/interventions/new"
              className="block w-full text-left px-4 py-3 rounded-lg bg-blue-50 text-blue-700 hover:bg-blue-100 transition-colors"
            >
              <WrenchScrewdriverIcon className="h-5 w-5 inline mr-2" />
              Nouvelle intervention
            </Link>
            <Link
              to="/expenses/new"
              className="block w-full text-left px-4 py-3 rounded-lg bg-orange-50 text-orange-700 hover:bg-orange-100 transition-colors"
            >
              <CurrencyEuroIcon className="h-5 w-5 inline mr-2" />
              Nouvelle note de frais
            </Link>
            <Link
              to="/clients/new"
              className="block w-full text-left px-4 py-3 rounded-lg bg-green-50 text-green-700 hover:bg-green-100 transition-colors"
            >
              <UserGroupIcon className="h-5 w-5 inline mr-2" />
              Nouveau client
            </Link>
          </div>
        </div>

        {/* Recent Invoices */}
        <div className="card">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-semibold flex items-center">
              <DocumentTextIcon className="h-5 w-5 mr-2 text-primary-600" />
              Dernieres factures
            </h2>
            <Link to="/invoices" className="text-sm text-primary-600 hover:underline">
              Voir tout
            </Link>
          </div>
          {recentInvoices.length > 0 ? (
            <div className="space-y-3">
              {recentInvoices.map((invoice) => (
                <Link
                  key={invoice.id}
                  to={`/invoices/${invoice.id}`}
                  className="block p-3 rounded-lg hover:bg-gray-50 transition-colors border"
                >
                  <div className="flex justify-between items-start">
                    <div>
                      <p className="font-medium text-sm">{invoice.invoice_number}</p>
                      <p className="text-xs text-gray-500">{invoice.client_name}</p>
                    </div>
                    <div className="text-right">
                      <p className="font-semibold text-sm">{formatCurrency(invoice.total_tvac)}</p>
                      <span className={`text-xs px-2 py-0.5 rounded-full ${getStatusColor(invoice.status)}`}>
                        {getStatusLabel(invoice.status)}
                      </span>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          ) : (
            <p className="text-gray-500 text-center py-4">Aucune facture</p>
          )}
        </div>

        {/* Recent Quotes */}
        <div className="card">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-semibold flex items-center">
              <DocumentDuplicateIcon className="h-5 w-5 mr-2 text-purple-600" />
              Derniers devis
            </h2>
            <Link to="/quotes" className="text-sm text-primary-600 hover:underline">
              Voir tout
            </Link>
          </div>
          {recentQuotes.length > 0 ? (
            <div className="space-y-3">
              {recentQuotes.map((quote) => (
                <Link
                  key={quote.id}
                  to={`/quotes/${quote.id}`}
                  className="block p-3 rounded-lg hover:bg-gray-50 transition-colors border"
                >
                  <div className="flex justify-between items-start">
                    <div>
                      <p className="font-medium text-sm">{quote.quote_number}</p>
                      <p className="text-xs text-gray-500">{quote.client_name}</p>
                    </div>
                    <div className="text-right">
                      <p className="font-semibold text-sm">{formatCurrency(parseFloat(String(quote.total_tvac)) || 0)}</p>
                      <span className={`text-xs px-2 py-0.5 rounded-full ${getStatusColor(quote.status)}`}>
                        {getStatusLabel(quote.status)}
                      </span>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          ) : (
            <p className="text-gray-500 text-center py-4">Aucun devis</p>
          )}
        </div>
      </div>

      {/* Recent Interventions */}
      <div className="card">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg font-semibold flex items-center">
            <WrenchScrewdriverIcon className="h-5 w-5 mr-2 text-blue-600" />
            Interventions recentes
          </h2>
          <Link to="/interventions" className="text-sm text-primary-600 hover:underline">
            Voir tout
          </Link>
        </div>
        {recentInterventions.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="min-w-full">
              <thead>
                <tr className="text-left text-xs text-gray-500 uppercase">
                  <th className="pb-2">Reference</th>
                  <th className="pb-2">Client</th>
                  <th className="pb-2">Titre</th>
                  <th className="pb-2">Date</th>
                  <th className="pb-2">Statut</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {recentInterventions.map((intervention) => (
                  <tr key={intervention.id} className="hover:bg-gray-50">
                    <td className="py-3">
                      <Link to={`/interventions/${intervention.id}`} className="text-primary-600 hover:underline font-mono text-sm">
                        {intervention.reference}
                      </Link>
                    </td>
                    <td className="py-3 text-sm">{intervention.client_name}</td>
                    <td className="py-3 text-sm">{intervention.title}</td>
                    <td className="py-3 text-sm">{formatDate(intervention.scheduled_date)}</td>
                    <td className="py-3">
                      <span className={`text-xs px-2 py-1 rounded-full ${getStatusColor(intervention.status)}`}>
                        {getStatusLabel(intervention.status)}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-gray-500 text-center py-4">Aucune intervention</p>
        )}
      </div>
    </div>
  )
}
