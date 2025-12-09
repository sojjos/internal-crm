import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { purchasesApi } from '../services/api'
import {
  PlusIcon,
  TrashIcon,
  ChartBarIcon,
  ArrowPathIcon,
} from '@heroicons/react/24/outline'
import toast from 'react-hot-toast'

interface FixedAsset {
  id: number
  name: string
  description: string | null
  asset_type: string
  acquisition_value: number
  current_book_value: number
  annual_depreciation: number
  service_start_date: string
  depreciation_years: number
  is_active: boolean
  vehicle_registration: string | null
}

const assetTypes: Record<string, string> = {
  MATERIEL_INFORMATIQUE: 'Materiel informatique',
  MOBILIER: 'Mobilier',
  VEHICULE: 'Vehicule',
  OUTILLAGE: 'Outillage',
  LOGICIEL: 'Logiciel',
  BATIMENT: 'Batiment',
  TERRAIN: 'Terrain',
  AUTRE: 'Autre',
}

export default function FixedAssets() {
  const [assets, setAssets] = useState<FixedAsset[]>([])
  const [loading, setLoading] = useState(true)
  const [showInactive, setShowInactive] = useState(false)

  useEffect(() => {
    loadAssets()
  }, [showInactive])

  const loadAssets = async () => {
    setLoading(true)
    try {
      const params: any = {}
      if (!showInactive) params.is_active = true
      const response = await purchasesApi.assets.list(params)
      setAssets(response.data)
    } catch (error) {
      toast.error('Erreur lors du chargement des immobilisations')
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (id: number) => {
    if (!confirm('Supprimer cette immobilisation ?')) return

    try {
      await purchasesApi.assets.delete(id)
      toast.success('Immobilisation supprimee')
      loadAssets()
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Erreur')
    }
  }

  const handleRegenerateDepreciation = async (id: number) => {
    try {
      await purchasesApi.assets.regenerateDepreciation(id)
      toast.success('Tableau d\'amortissement regenere')
      loadAssets()
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

  const getDepreciationProgress = (asset: FixedAsset) => {
    const depreciated = asset.acquisition_value - asset.current_book_value
    const percentage = (depreciated / asset.acquisition_value) * 100
    return Math.min(100, Math.max(0, percentage))
  }

  // Calculate totals
  const activeAssets = assets.filter(a => a.is_active)
  const totalAcquisition = activeAssets.reduce((sum, a) => sum + a.acquisition_value, 0)
  const totalBookValue = activeAssets.reduce((sum, a) => sum + a.current_book_value, 0)
  const totalAnnualDepreciation = activeAssets.reduce((sum, a) => sum + a.annual_depreciation, 0)

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
        <h1 className="page-title mb-0">Immobilisations</h1>
        <Link to="/purchases/assets/new" className="btn-primary flex items-center">
          <PlusIcon className="h-5 w-5 mr-1" />
          Nouvelle immobilisation
        </Link>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="card bg-blue-50">
          <p className="text-sm text-gray-600">Actifs</p>
          <p className="text-2xl font-bold text-blue-600">
            {activeAssets.length}
          </p>
        </div>
        <div className="card bg-green-50">
          <p className="text-sm text-gray-600">Valeur d'acquisition</p>
          <p className="text-2xl font-bold text-green-600">
            {formatCurrency(totalAcquisition)}
          </p>
        </div>
        <div className="card bg-purple-50">
          <p className="text-sm text-gray-600">Valeur comptable</p>
          <p className="text-2xl font-bold text-purple-600">
            {formatCurrency(totalBookValue)}
          </p>
        </div>
        <div className="card bg-orange-50">
          <p className="text-sm text-gray-600">Amortissement annuel</p>
          <p className="text-2xl font-bold text-orange-600">
            {formatCurrency(totalAnnualDepreciation)}
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
            <span className="text-sm text-gray-600">Afficher les actifs cedés/inactifs</span>
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
                <th className="table-header px-6 py-3">Actif</th>
                <th className="table-header px-6 py-3">Type</th>
                <th className="table-header px-6 py-3">Mise en service</th>
                <th className="table-header px-6 py-3 text-right">Acquisition</th>
                <th className="table-header px-6 py-3 text-right">Valeur nette</th>
                <th className="table-header px-6 py-3">Amortissement</th>
                <th className="table-header px-6 py-3">Actions</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {assets.map((asset) => (
                <tr key={asset.id} className={`hover:bg-gray-50 ${!asset.is_active ? 'opacity-50' : ''}`}>
                  <td className="px-6 py-4">
                    <div>
                      <div className="font-medium">{asset.name}</div>
                      {asset.description && (
                        <div className="text-xs text-gray-500">{asset.description}</div>
                      )}
                      {asset.vehicle_registration && (
                        <div className="text-xs text-blue-600">{asset.vehicle_registration}</div>
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="px-2 py-1 text-xs rounded-full bg-gray-100">
                      {assetTypes[asset.asset_type] || asset.asset_type}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {formatDate(asset.service_start_date)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right font-medium">
                    {formatCurrency(asset.acquisition_value)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right">
                    <span className={asset.current_book_value <= 0 ? 'text-gray-400' : 'text-green-600 font-medium'}>
                      {formatCurrency(asset.current_book_value)}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <div className="w-32">
                      <div className="flex items-center justify-between text-xs text-gray-500 mb-1">
                        <span>{asset.depreciation_years} ans</span>
                        <span>{Math.round(getDepreciationProgress(asset))}%</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-primary-600 h-2 rounded-full transition-all"
                          style={{ width: `${getDepreciationProgress(asset)}%` }}
                        />
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center gap-2">
                      <Link
                        to={`/purchases/assets/${asset.id}`}
                        className="text-primary-600 hover:text-primary-800"
                        title="Voir details"
                      >
                        <ChartBarIcon className="h-5 w-5" />
                      </Link>
                      <button
                        onClick={() => handleRegenerateDepreciation(asset.id)}
                        className="text-blue-600 hover:text-blue-800"
                        title="Regenerer amortissements"
                      >
                        <ArrowPathIcon className="h-5 w-5" />
                      </button>
                      {asset.is_active && (
                        <button
                          onClick={() => handleDelete(asset.id)}
                          className="text-red-600 hover:text-red-800"
                          title="Supprimer"
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

          {assets.length === 0 && (
            <p className="text-center py-8 text-gray-500">
              Aucune immobilisation trouvee
            </p>
          )}
        </div>
      </div>
    </div>
  )
}
