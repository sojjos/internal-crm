import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { purchasesApi, suppliersApi } from '../services/api'
import {
  PlusIcon,
  PencilIcon,
  TrashIcon,
  CheckCircleIcon,
  Cog6ToothIcon,
} from '@heroicons/react/24/outline'
import toast from 'react-hot-toast'

interface Purchase {
  id: number
  purchase_date: string
  description: string
  supplier_name: string | null
  category_name: string | null
  amount_htva: number
  vat_amount: number
  amount_ttc: number
  vat_deductible_amount: number
  vat_non_deductible_amount: number
  status: string
  is_investment: boolean
}

interface Category {
  id: number
  name: string
}

interface Supplier {
  id: number
  name: string
}

type TabType = 'all' | 'investments' | 'contracts' | 'assets'

export default function Purchases() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [purchases, setPurchases] = useState<Purchase[]>([])
  const [categories, setCategories] = useState<Category[]>([])
  const [suppliers, setSuppliers] = useState<Supplier[]>([])
  const [loading, setLoading] = useState(true)

  const [activeTab, setActiveTab] = useState<TabType>(
    (searchParams.get('tab') as TabType) || 'all'
  )
  const [categoryFilter, setCategoryFilter] = useState('')
  const [supplierFilter, setSupplierFilter] = useState('')
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')

  // Category management
  const [showCategoryModal, setShowCategoryModal] = useState(false)
  const [editingCategory, setEditingCategory] = useState<Category | null>(null)
  const [categoryForm, setCategoryForm] = useState({
    name: '',
    pcmn_code: '',
    vat_deductible_percent: 100,
    description: '',
  })

  useEffect(() => {
    loadInitialData()
  }, [])

  useEffect(() => {
    loadPurchases()
  }, [categoryFilter, supplierFilter, dateFrom, dateTo, activeTab])

  const loadInitialData = async () => {
    try {
      const [categoriesRes, suppliersRes] = await Promise.all([
        purchasesApi.categories.list({ is_active: true }),
        suppliersApi.list({ is_active: true }),
      ])
      setCategories(categoriesRes.data)
      setSuppliers(suppliersRes.data)
    } catch (error) {
      console.error('Error loading initial data:', error)
    }
  }

  const loadPurchases = async () => {
    setLoading(true)
    try {
      const params: any = {}
      if (categoryFilter) params.category_id = categoryFilter
      if (supplierFilter) params.supplier_id = supplierFilter
      if (dateFrom) params.date_from = dateFrom
      if (dateTo) params.date_to = dateTo
      if (activeTab === 'investments') params.is_investment = true

      const response = await purchasesApi.list(params)
      setPurchases(response.data)
    } catch (error) {
      toast.error('Erreur lors du chargement des achats')
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (id: number) => {
    if (!confirm('Supprimer cet achat ?')) return

    try {
      await purchasesApi.delete(id)
      toast.success('Achat supprime')
      loadPurchases()
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Erreur lors de la suppression')
    }
  }

  const handleValidate = async (id: number) => {
    try {
      await purchasesApi.validate(id)
      toast.success('Achat valide')
      loadPurchases()
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Erreur lors de la validation')
    }
  }

  const handleTabChange = (tab: TabType) => {
    setActiveTab(tab)
    setSearchParams({ tab })
  }

  // Category handlers
  const openCategoryModal = (category?: Category) => {
    if (category) {
      setEditingCategory(category)
      setCategoryForm({
        name: category.name,
        pcmn_code: (category as any).pcmn_code || '',
        vat_deductible_percent: (category as any).vat_deductible_percent || 100,
        description: (category as any).description || '',
      })
    } else {
      setEditingCategory(null)
      setCategoryForm({
        name: '',
        pcmn_code: '',
        vat_deductible_percent: 100,
        description: '',
      })
    }
    setShowCategoryModal(true)
  }

  const handleSaveCategory = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      if (editingCategory) {
        await purchasesApi.categories.update(editingCategory.id, categoryForm)
        toast.success('Categorie mise a jour')
      } else {
        await purchasesApi.categories.create(categoryForm)
        toast.success('Categorie creee')
      }
      setShowCategoryModal(false)
      loadInitialData()
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Erreur')
    }
  }

  const handleDeleteCategory = async (id: number) => {
    if (!confirm('Supprimer cette categorie ?')) return
    try {
      await purchasesApi.categories.delete(id)
      toast.success('Categorie supprimee')
      loadInitialData()
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Erreur lors de la suppression')
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

  const getStatusBadge = (status: string) => {
    const statusMap: Record<string, { label: string; className: string }> = {
      BROUILLON: { label: 'Brouillon', className: 'bg-gray-100 text-gray-800' },
      VALIDE: { label: 'Valide', className: 'bg-green-100 text-green-800' },
      PAYE: { label: 'Paye', className: 'bg-blue-100 text-blue-800' },
      ANNULE: { label: 'Annule', className: 'bg-red-100 text-red-800' },
    }
    const s = statusMap[status] || statusMap.BROUILLON
    return (
      <span className={`px-2 py-1 text-xs font-medium rounded-full ${s.className}`}>
        {s.label}
      </span>
    )
  }

  const tabs = [
    { id: 'all', label: 'Tous les achats' },
    { id: 'investments', label: 'Investissements' },
    { id: 'contracts', label: 'Contrats', href: '/purchases/contracts' },
    { id: 'assets', label: 'Immobilisations', href: '/purchases/assets' },
  ]

  if (loading && purchases.length === 0) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="page-title mb-0">Achats & Investissements</h1>
        <div className="flex gap-2">
          <button
            onClick={() => openCategoryModal()}
            className="btn-secondary flex items-center"
          >
            <Cog6ToothIcon className="h-5 w-5 mr-1" />
            Categories
          </button>
          <Link to="/purchases/new" className="btn-primary flex items-center">
            <PlusIcon className="h-5 w-5 mr-1" />
            Nouvel achat
          </Link>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="-mb-px flex space-x-8">
          {tabs.map((tab) => (
            tab.href ? (
              <Link
                key={tab.id}
                to={tab.href}
                className="whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
              >
                {tab.label}
              </Link>
            ) : (
              <button
                key={tab.id}
                onClick={() => handleTabChange(tab.id as TabType)}
                className={`whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === tab.id
                    ? 'border-primary-500 text-primary-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                {tab.label}
              </button>
            )
          ))}
        </nav>
      </div>

      <div className="card">
        {/* Filters */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div>
            <label className="label">Fournisseur</label>
            <select
              value={supplierFilter}
              onChange={(e) => setSupplierFilter(e.target.value)}
              className="input"
            >
              <option value="">Tous</option>
              {suppliers.map((s) => (
                <option key={s.id} value={s.id}>{s.name}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="label">Categorie</label>
            <select
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
              className="input"
            >
              <option value="">Toutes</option>
              {categories.map((c) => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="label">Du</label>
            <input
              type="date"
              value={dateFrom}
              onChange={(e) => setDateFrom(e.target.value)}
              className="input"
            />
          </div>
          <div>
            <label className="label">Au</label>
            <input
              type="date"
              value={dateTo}
              onChange={(e) => setDateTo(e.target.value)}
              className="input"
            />
          </div>
        </div>

        {/* Table */}
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead>
              <tr>
                <th className="table-header px-6 py-3">Date</th>
                <th className="table-header px-6 py-3">Description</th>
                <th className="table-header px-6 py-3">Fournisseur</th>
                <th className="table-header px-6 py-3">Categorie</th>
                <th className="table-header px-6 py-3 text-right">HTVA</th>
                <th className="table-header px-6 py-3 text-right">TVA Ded.</th>
                <th className="table-header px-6 py-3 text-right">TTC</th>
                <th className="table-header px-6 py-3">Statut</th>
                <th className="table-header px-6 py-3">Actions</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {purchases.map((purchase) => (
                <tr key={purchase.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    {formatDate(purchase.purchase_date)}
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-2">
                      {purchase.is_investment && (
                        <span className="px-1.5 py-0.5 text-xs bg-purple-100 text-purple-800 rounded">
                          INV
                        </span>
                      )}
                      {purchase.description}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {purchase.supplier_name || '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {purchase.category_name || '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right font-medium">
                    {formatCurrency(purchase.amount_htva)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-green-600">
                    {formatCurrency(purchase.vat_deductible_amount)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right font-semibold">
                    {formatCurrency(purchase.amount_ttc)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {getStatusBadge(purchase.status)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center gap-2">
                      {purchase.status === 'BROUILLON' && (
                        <button
                          onClick={() => handleValidate(purchase.id)}
                          className="text-green-600 hover:text-green-800"
                          title="Valider"
                        >
                          <CheckCircleIcon className="h-5 w-5" />
                        </button>
                      )}
                      <Link
                        to={`/purchases/${purchase.id}`}
                        className="text-primary-600 hover:text-primary-800"
                      >
                        <PencilIcon className="h-5 w-5" />
                      </Link>
                      {purchase.status === 'BROUILLON' && (
                        <button
                          onClick={() => handleDelete(purchase.id)}
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

          {purchases.length === 0 && (
            <p className="text-center py-8 text-gray-500">
              Aucun achat trouve
            </p>
          )}
        </div>

        {/* Summary */}
        {purchases.length > 0 && (
          <div className="mt-6 pt-6 border-t border-gray-200">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="bg-gray-50 rounded-lg p-4">
                <p className="text-sm text-gray-500">Total HTVA</p>
                <p className="text-xl font-bold">
                  {formatCurrency(purchases.reduce((sum, p) => sum + p.amount_htva, 0))}
                </p>
              </div>
              <div className="bg-green-50 rounded-lg p-4">
                <p className="text-sm text-gray-500">TVA deductible</p>
                <p className="text-xl font-bold text-green-600">
                  {formatCurrency(purchases.reduce((sum, p) => sum + p.vat_deductible_amount, 0))}
                </p>
              </div>
              <div className="bg-orange-50 rounded-lg p-4">
                <p className="text-sm text-gray-500">TVA non deductible</p>
                <p className="text-xl font-bold text-orange-600">
                  {formatCurrency(purchases.reduce((sum, p) => sum + p.vat_non_deductible_amount, 0))}
                </p>
              </div>
              <div className="bg-blue-50 rounded-lg p-4">
                <p className="text-sm text-gray-500">Total TTC</p>
                <p className="text-xl font-bold text-blue-600">
                  {formatCurrency(purchases.reduce((sum, p) => sum + p.amount_ttc, 0))}
                </p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Category Management Modal */}
      {showCategoryModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <h2 className="text-lg font-semibold mb-4">
              {editingCategory ? 'Modifier la categorie' : 'Gestion des categories'}
            </h2>

            {/* Category List */}
            {!editingCategory && (
              <div className="mb-6">
                <div className="flex justify-between items-center mb-3">
                  <h3 className="font-medium">Categories existantes</h3>
                  <button
                    onClick={() => {
                      setEditingCategory(null)
                      setCategoryForm({
                        name: '',
                        pcmn_code: '',
                        vat_deductible_percent: 100,
                        description: '',
                      })
                    }}
                    className="text-sm text-primary-600 hover:text-primary-800"
                  >
                    + Nouvelle categorie
                  </button>
                </div>
                <div className="border rounded-lg divide-y max-h-48 overflow-y-auto">
                  {categories.length === 0 ? (
                    <p className="p-4 text-gray-500 text-center">Aucune categorie</p>
                  ) : (
                    categories.map((cat) => (
                      <div key={cat.id} className="flex items-center justify-between p-3 hover:bg-gray-50">
                        <span>{cat.name}</span>
                        <div className="flex gap-2">
                          <button
                            onClick={() => openCategoryModal(cat)}
                            className="text-primary-600 hover:text-primary-800"
                          >
                            <PencilIcon className="h-4 w-4" />
                          </button>
                          <button
                            onClick={() => handleDeleteCategory(cat.id)}
                            className="text-red-600 hover:text-red-800"
                          >
                            <TrashIcon className="h-4 w-4" />
                          </button>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            )}

            {/* Category Form */}
            <form onSubmit={handleSaveCategory} className="space-y-4">
              <div>
                <label className="label">Nom de la categorie *</label>
                <input
                  type="text"
                  value={categoryForm.name}
                  onChange={(e) => setCategoryForm({ ...categoryForm, name: e.target.value })}
                  className="input"
                  required
                  placeholder="Ex: Fournitures de bureau"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="label">Code PCMN</label>
                  <input
                    type="text"
                    value={categoryForm.pcmn_code}
                    onChange={(e) => setCategoryForm({ ...categoryForm, pcmn_code: e.target.value })}
                    className="input"
                    placeholder="Ex: 6100"
                  />
                </div>
                <div>
                  <label className="label">TVA deductible (%)</label>
                  <input
                    type="number"
                    min="0"
                    max="100"
                    value={categoryForm.vat_deductible_percent}
                    onChange={(e) => setCategoryForm({ ...categoryForm, vat_deductible_percent: parseInt(e.target.value) })}
                    className="input"
                  />
                </div>
              </div>
              <div>
                <label className="label">Description</label>
                <textarea
                  value={categoryForm.description}
                  onChange={(e) => setCategoryForm({ ...categoryForm, description: e.target.value })}
                  className="input"
                  rows={2}
                />
              </div>
              <div className="flex justify-end gap-2 pt-4">
                <button
                  type="button"
                  onClick={() => {
                    if (editingCategory) {
                      setEditingCategory(null)
                    } else {
                      setShowCategoryModal(false)
                    }
                  }}
                  className="btn-secondary"
                >
                  {editingCategory ? 'Retour' : 'Fermer'}
                </button>
                <button type="submit" className="btn-primary">
                  {editingCategory ? 'Mettre a jour' : 'Creer'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
