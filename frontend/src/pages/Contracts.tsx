import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { purchasesApi } from '../services/api'
import {
  PlusIcon,
  PencilIcon,
  TrashIcon,
  CalendarDaysIcon,
  ArrowPathIcon,
} from '@heroicons/react/24/outline'
import toast from 'react-hot-toast'

interface Contract {
  id: number
  name: string
  supplier_name: string | null
  category_name: string | null
  contract_type: string
  periodicity: string
  amount_htva: number
  amount_ttc: number
  monthly_amount: number
  start_date: string
  end_date: string | null
  next_billing_date: string | null
  is_active: boolean
  vehicle_registration: string | null
}

const contractTypes: Record<string, string> = {
  ABONNEMENT: 'Abonnement',
  LEASING: 'Leasing',
  LOCATION: 'Location',
  MAINTENANCE: 'Maintenance',
  LICENCE: 'Licence',
  ASSURANCE: 'Assurance',
  AUTRE: 'Autre',
}

const periodicities: Record<string, string> = {
  MENSUEL: 'Mensuel',
  TRIMESTRIEL: 'Trimestriel',
  SEMESTRIEL: 'Semestriel',
  ANNUEL: 'Annuel',
}

export default function Contracts() {
  const [contracts, setContracts] = useState<Contract[]>([])
  const [loading, setLoading] = useState(true)
  const [showInactive, setShowInactive] = useState(false)
  const [generating, setGenerating] = useState(false)

  useEffect(() => {
    loadContracts()
  }, [showInactive])

  const loadContracts = async () => {
    setLoading(true)
    try {
      const params: any = {}
      if (!showInactive) params.is_active = true
      const response = await purchasesApi.contracts.list(params)
      setContracts(response.data)
    } catch (error) {
      toast.error('Erreur lors du chargement des contrats')
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (id: number) => {
    if (!confirm('Desactiver ce contrat ?')) return

    try {
      await purchasesApi.contracts.delete(id)
      toast.success('Contrat desactive')
      loadContracts()
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Erreur')
    }
  }

  const handleGeneratePurchases = async () => {
    const today = new Date().toISOString().split('T')[0]
    setGenerating(true)
    try {
      const response = await purchasesApi.contracts.generatePurchases(today)
      toast.success(`${response.data.purchase_ids.length} achats generes`)
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Erreur')
    } finally {
      setGenerating(false)
    }
  }

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return '-'
    return new Date(dateStr).toLocaleDateString('fr-BE')
  }

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('fr-BE', {
      style: 'currency',
      currency: 'EUR',
    }).format(amount)
  }

  const isUpcoming = (nextDate: string | null) => {
    if (!nextDate) return false
    const next = new Date(nextDate)
    const today = new Date()
    const diff = (next.getTime() - today.getTime()) / (1000 * 60 * 60 * 24)
    return diff <= 7 && diff >= 0
  }

  // Calculate monthly totals
  const totalMonthly = contracts
    .filter(c => c.is_active)
    .reduce((sum, c) => sum + (c.monthly_amount || 0), 0)

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
        <h1 className="page-title mb-0">Contrats & Abonnements</h1>
        <div className="flex items-center gap-3">
          <button
            onClick={handleGeneratePurchases}
            disabled={generating}
            className="btn-secondary flex items-center"
          >
            <ArrowPathIcon className={`h-5 w-5 mr-1 ${generating ? 'animate-spin' : ''}`} />
            Generer achats
          </button>
          <Link to="/purchases/contracts/new" className="btn-primary flex items-center">
            <PlusIcon className="h-5 w-5 mr-1" />
            Nouveau contrat
          </Link>
        </div>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="card bg-blue-50">
          <p className="text-sm text-gray-600">Contrats actifs</p>
          <p className="text-2xl font-bold text-blue-600">
            {contracts.filter(c => c.is_active).length}
          </p>
        </div>
        <div className="card bg-green-50">
          <p className="text-sm text-gray-600">Cout mensuel total</p>
          <p className="text-2xl font-bold text-green-600">
            {formatCurrency(totalMonthly)}
          </p>
        </div>
        <div className="card bg-purple-50">
          <p className="text-sm text-gray-600">Cout annuel estime</p>
          <p className="text-2xl font-bold text-purple-600">
            {formatCurrency(totalMonthly * 12)}
          </p>
        </div>
      </div>

      <div className="card">
        <div className="mb-4 flex items-center justify-between">
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={showInactive}
              onChange={(e) => setShowInactive(e.target.checked)}
              className="rounded border-gray-300"
            />
            <span className="text-sm text-gray-600">Afficher les contrats inactifs</span>
          </label>
          <Link
            to="/purchases"
            className="text-sm text-primary-600 hover:text-primary-800"
          >
            Retour aux achats
          </Link>
        </div>

        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead>
              <tr>
                <th className="table-header px-6 py-3">Contrat</th>
                <th className="table-header px-6 py-3">Fournisseur</th>
                <th className="table-header px-6 py-3">Type</th>
                <th className="table-header px-6 py-3">Periodicite</th>
                <th className="table-header px-6 py-3 text-right">Montant</th>
                <th className="table-header px-6 py-3 text-right">Mensuel</th>
                <th className="table-header px-6 py-3">Prochaine ech.</th>
                <th className="table-header px-6 py-3">Statut</th>
                <th className="table-header px-6 py-3">Actions</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {contracts.map((contract) => (
                <tr key={contract.id} className={`hover:bg-gray-50 ${!contract.is_active ? 'opacity-50' : ''}`}>
                  <td className="px-6 py-4">
                    <div>
                      <div className="font-medium">{contract.name}</div>
                      {contract.vehicle_registration && (
                        <div className="text-xs text-gray-500">
                          {contract.vehicle_registration}
                        </div>
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {contract.supplier_name || '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="px-2 py-1 text-xs rounded-full bg-gray-100">
                      {contractTypes[contract.contract_type] || contract.contract_type}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {periodicities[contract.periodicity] || contract.periodicity}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right font-medium">
                    {formatCurrency(contract.amount_htva)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-gray-600">
                    {formatCurrency(contract.monthly_amount || 0)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {contract.next_billing_date ? (
                      <div className={`flex items-center gap-1 ${isUpcoming(contract.next_billing_date) ? 'text-orange-600 font-medium' : ''}`}>
                        <CalendarDaysIcon className="h-4 w-4" />
                        {formatDate(contract.next_billing_date)}
                      </div>
                    ) : '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {contract.is_active ? (
                      <span className="px-2 py-1 text-xs font-medium rounded-full bg-green-100 text-green-800">
                        Actif
                      </span>
                    ) : (
                      <span className="px-2 py-1 text-xs font-medium rounded-full bg-gray-100 text-gray-800">
                        Inactif
                      </span>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center gap-2">
                      <Link
                        to={`/purchases/contracts/${contract.id}`}
                        className="text-primary-600 hover:text-primary-800"
                      >
                        <PencilIcon className="h-5 w-5" />
                      </Link>
                      {contract.is_active && (
                        <button
                          onClick={() => handleDelete(contract.id)}
                          className="text-red-600 hover:text-red-800"
                        >
                          <TrashIcon className="h-5 w-5" />
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {contracts.length === 0 && (
            <p className="text-center py-8 text-gray-500">
              Aucun contrat trouve
            </p>
          )}
        </div>
      </div>
    </div>
  )
}
