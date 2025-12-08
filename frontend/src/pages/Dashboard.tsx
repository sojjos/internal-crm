import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { reportsApi } from '../services/api'
import {
  CurrencyEuroIcon,
  DocumentTextIcon,
  ExclamationTriangleIcon,
  ArrowTrendingUpIcon,
} from '@heroicons/react/24/outline'

interface DashboardStats {
  total_revenue_ytd: number
  total_expenses_ytd: number
  outstanding_invoices: number
  overdue_invoices: number
  invoices_this_month: number
  expenses_this_month: number
}

export default function Dashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadStats()
  }, [])

  const loadStats = async () => {
    try {
      const response = await reportsApi.dashboard()
      setStats(response.data)
    } catch (error) {
      console.error('Failed to load dashboard stats', error)
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

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  return (
    <div>
      <h1 className="page-title">Tableau de bord</h1>

      {/* Stats cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div className="card">
          <div className="flex items-center">
            <div className="p-3 rounded-full bg-green-100 text-green-600">
              <ArrowTrendingUpIcon className="h-6 w-6" />
            </div>
            <div className="ml-4">
              <p className="text-sm text-gray-500">CA Année</p>
              <p className="text-xl font-semibold">
                {formatCurrency(stats?.total_revenue_ytd || 0)}
              </p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center">
            <div className="p-3 rounded-full bg-red-100 text-red-600">
              <CurrencyEuroIcon className="h-6 w-6" />
            </div>
            <div className="ml-4">
              <p className="text-sm text-gray-500">Dépenses Année</p>
              <p className="text-xl font-semibold">
                {formatCurrency(stats?.total_expenses_ytd || 0)}
              </p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center">
            <div className="p-3 rounded-full bg-blue-100 text-blue-600">
              <DocumentTextIcon className="h-6 w-6" />
            </div>
            <div className="ml-4">
              <p className="text-sm text-gray-500">Factures en attente</p>
              <p className="text-xl font-semibold">
                {formatCurrency(stats?.outstanding_invoices || 0)}
              </p>
            </div>
          </div>
        </div>

        <div className="card">
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

      {/* Quick actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="card">
          <h2 className="text-lg font-semibold mb-4">Actions rapides</h2>
          <div className="space-y-2">
            <Link
              to="/invoices/new"
              className="block w-full text-left px-4 py-2 rounded-lg bg-primary-50 text-primary-700 hover:bg-primary-100"
            >
              + Nouvelle facture
            </Link>
            <Link
              to="/expenses/new"
              className="block w-full text-left px-4 py-2 rounded-lg bg-primary-50 text-primary-700 hover:bg-primary-100"
            >
              + Nouvelle note de frais
            </Link>
            <Link
              to="/clients/new"
              className="block w-full text-left px-4 py-2 rounded-lg bg-primary-50 text-primary-700 hover:bg-primary-100"
            >
              + Nouveau client
            </Link>
          </div>
        </div>

        <div className="card">
          <h2 className="text-lg font-semibold mb-4">Ce mois</h2>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-gray-600">Factures créées</span>
              <span className="font-semibold">{stats?.invoices_this_month || 0}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Notes de frais</span>
              <span className="font-semibold">{stats?.expenses_this_month || 0}</span>
            </div>
          </div>
        </div>

        <div className="card">
          <h2 className="text-lg font-semibold mb-4">Résultat net estimé</h2>
          <p className="text-3xl font-bold text-primary-600">
            {formatCurrency(
              (stats?.total_revenue_ytd || 0) - (stats?.total_expenses_ytd || 0)
            )}
          </p>
          <p className="text-sm text-gray-500 mt-2">
            Revenus - Dépenses (année en cours)
          </p>
        </div>
      </div>
    </div>
  )
}
