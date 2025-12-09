import { useEffect, useState } from 'react'
import { stockApi } from '../services/api'
import {
  PlusIcon,
  TrashIcon,
  ArrowUpIcon,
  ArrowDownIcon,
  ExclamationTriangleIcon,
  CubeIcon,
} from '@heroicons/react/24/outline'
import toast from 'react-hot-toast'

interface StockArticle {
  id: number
  code: string
  name: string
  description: string | null
  category_name: string | null
  unit: string
  min_quantity: number
  is_active: boolean
}

interface StockItem {
  id: number
  article_id: number
  article_name: string
  article_code: string
  location_name: string
  quantity: number
  reserved_quantity: number
  available_quantity: number
  unit_cost: number
  total_value: number
}

interface StockMovement {
  id: number
  article_name: string
  location_name: string
  movement_type: string
  quantity: number
  unit_cost: number | null
  reference: string | null
  notes: string | null
  created_at: string
}

interface StockAlert {
  article_id: number
  article_code: string
  article_name: string
  current_quantity: number
  min_quantity: number
  shortage: number
}

interface Location {
  id: number
  name: string
}

interface Category {
  id: number
  name: string
}

type TabType = 'articles' | 'stock' | 'movements' | 'alerts'

const movementTypes: Record<string, { label: string; color: string }> = {
  ENTREE: { label: 'Entree', color: 'text-green-600' },
  SORTIE: { label: 'Sortie', color: 'text-red-600' },
  TRANSFERT: { label: 'Transfert', color: 'text-blue-600' },
  AJUSTEMENT: { label: 'Ajustement', color: 'text-orange-600' },
  INVENTAIRE: { label: 'Inventaire', color: 'text-purple-600' },
}

export default function Stock() {
  const [activeTab, setActiveTab] = useState<TabType>('stock')
  const [articles, setArticles] = useState<StockArticle[]>([])
  const [items, setItems] = useState<StockItem[]>([])
  const [movements, setMovements] = useState<StockMovement[]>([])
  const [alerts, setAlerts] = useState<StockAlert[]>([])
  const [locations, setLocations] = useState<Location[]>([])
  const [categories, setCategories] = useState<Category[]>([])
  const [loading, setLoading] = useState(true)

  const [showAddArticle, setShowAddArticle] = useState(false)
  const [showAddMovement, setShowAddMovement] = useState(false)

  const [articleForm, setArticleForm] = useState({
    code: '',
    name: '',
    description: '',
    category_id: '',
    unit: 'PIECE',
    min_quantity: 0,
  })

  const [movementForm, setMovementForm] = useState({
    article_id: '',
    location_id: '',
    movement_type: 'ENTREE',
    quantity: 0,
    unit_cost: 0,
    reference: '',
    notes: '',
  })

  useEffect(() => {
    loadInitialData()
  }, [])

  useEffect(() => {
    loadTabData()
  }, [activeTab])

  const loadInitialData = async () => {
    try {
      const [locRes, catRes, alertsRes] = await Promise.all([
        stockApi.locations.list(),
        stockApi.categories.list(),
        stockApi.alerts(),
      ])
      setLocations(locRes.data)
      setCategories(catRes.data)
      setAlerts(alertsRes.data)
    } catch (error) {
      console.error('Error loading initial data:', error)
    }
  }

  const loadTabData = async () => {
    setLoading(true)
    try {
      switch (activeTab) {
        case 'articles':
          const articlesRes = await stockApi.articles.list()
          setArticles(articlesRes.data)
          break
        case 'stock':
          const itemsRes = await stockApi.items.list()
          setItems(itemsRes.data)
          break
        case 'movements':
          const movementsRes = await stockApi.movements.list()
          setMovements(movementsRes.data)
          break
        case 'alerts':
          const alertsRes = await stockApi.alerts()
          setAlerts(alertsRes.data)
          break
      }
    } catch (error) {
      toast.error('Erreur lors du chargement')
    } finally {
      setLoading(false)
    }
  }

  const handleAddArticle = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await stockApi.articles.create({
        ...articleForm,
        category_id: articleForm.category_id ? parseInt(articleForm.category_id) : null,
      })
      toast.success('Article ajoute')
      setShowAddArticle(false)
      setArticleForm({ code: '', name: '', description: '', category_id: '', unit: 'PIECE', min_quantity: 0 })
      loadTabData()
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Erreur')
    }
  }

  const handleAddMovement = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await stockApi.movements.create({
        ...movementForm,
        article_id: parseInt(movementForm.article_id),
        location_id: parseInt(movementForm.location_id),
        unit_cost: movementForm.unit_cost || null,
      })
      toast.success('Mouvement enregistre')
      setShowAddMovement(false)
      setMovementForm({
        article_id: '',
        location_id: '',
        movement_type: 'ENTREE',
        quantity: 0,
        unit_cost: 0,
        reference: '',
        notes: '',
      })
      loadTabData()
      loadInitialData()
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Erreur')
    }
  }

  const handleDeleteArticle = async (id: number) => {
    if (!confirm('Supprimer cet article ?')) return
    try {
      await stockApi.articles.delete(id)
      toast.success('Article supprime')
      loadTabData()
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Erreur')
    }
  }

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('fr-BE', {
      style: 'currency',
      currency: 'EUR',
    }).format(amount)
  }

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('fr-BE', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  const totalValue = items.reduce((sum, i) => sum + i.total_value, 0)

  const tabs = [
    { id: 'stock', label: 'Etat du stock' },
    { id: 'articles', label: 'Articles' },
    { id: 'movements', label: 'Mouvements' },
    { id: 'alerts', label: `Alertes (${alerts.length})` },
  ]

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="page-title mb-0">Gestion des Stocks</h1>
        <div className="flex gap-2">
          <button
            onClick={() => setShowAddArticle(true)}
            className="btn-secondary flex items-center"
          >
            <PlusIcon className="h-5 w-5 mr-1" />
            Article
          </button>
          <button
            onClick={() => setShowAddMovement(true)}
            className="btn-primary flex items-center"
          >
            <PlusIcon className="h-5 w-5 mr-1" />
            Mouvement
          </button>
        </div>
      </div>

      {/* Alerts banner */}
      {alerts.length > 0 && (
        <div className="bg-red-50 border-l-4 border-red-400 p-4 mb-6">
          <div className="flex items-center">
            <ExclamationTriangleIcon className="h-5 w-5 text-red-400 mr-2" />
            <p className="text-red-700">
              <strong>{alerts.length} article(s)</strong> en rupture ou sous le seuil minimum
            </p>
          </div>
        </div>
      )}

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="card bg-blue-50">
          <p className="text-sm text-gray-600">Articles</p>
          <p className="text-2xl font-bold text-blue-600">{articles.length || '-'}</p>
        </div>
        <div className="card bg-green-50">
          <p className="text-sm text-gray-600">Valeur totale</p>
          <p className="text-2xl font-bold text-green-600">{formatCurrency(totalValue)}</p>
        </div>
        <div className="card bg-purple-50">
          <p className="text-sm text-gray-600">Emplacements</p>
          <p className="text-2xl font-bold text-purple-600">{locations.length}</p>
        </div>
        <div className="card bg-red-50">
          <p className="text-sm text-gray-600">Alertes stock</p>
          <p className="text-2xl font-bold text-red-600">{alerts.length}</p>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="-mb-px flex space-x-8">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as TabType)}
              className={`whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab.id
                  ? 'border-primary-500 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
        </div>
      ) : (
        <div className="card">
          {/* Stock Tab */}
          {activeTab === 'stock' && (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead>
                  <tr>
                    <th className="table-header px-6 py-3">Code</th>
                    <th className="table-header px-6 py-3">Article</th>
                    <th className="table-header px-6 py-3">Emplacement</th>
                    <th className="table-header px-6 py-3 text-right">Quantite</th>
                    <th className="table-header px-6 py-3 text-right">Reserve</th>
                    <th className="table-header px-6 py-3 text-right">Disponible</th>
                    <th className="table-header px-6 py-3 text-right">Cout unit.</th>
                    <th className="table-header px-6 py-3 text-right">Valeur</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {items.map((item) => (
                    <tr key={item.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap font-mono text-sm">
                        {item.article_code}
                      </td>
                      <td className="px-6 py-4">{item.article_name}</td>
                      <td className="px-6 py-4 whitespace-nowrap">{item.location_name}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-right font-medium">
                        {item.quantity}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-orange-600">
                        {item.reserved_quantity}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-green-600 font-medium">
                        {item.available_quantity}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right">
                        {formatCurrency(item.unit_cost)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right font-semibold">
                        {formatCurrency(item.total_value)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {items.length === 0 && (
                <p className="text-center py-8 text-gray-500">Aucun stock</p>
              )}
            </div>
          )}

          {/* Articles Tab */}
          {activeTab === 'articles' && (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead>
                  <tr>
                    <th className="table-header px-6 py-3">Code</th>
                    <th className="table-header px-6 py-3">Nom</th>
                    <th className="table-header px-6 py-3">Categorie</th>
                    <th className="table-header px-6 py-3">Unite</th>
                    <th className="table-header px-6 py-3 text-right">Seuil min.</th>
                    <th className="table-header px-6 py-3">Actions</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {articles.map((article) => (
                    <tr key={article.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap font-mono text-sm">
                        {article.code}
                      </td>
                      <td className="px-6 py-4">
                        <div>
                          <div className="font-medium">{article.name}</div>
                          {article.description && (
                            <div className="text-xs text-gray-500">{article.description}</div>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {article.category_name || '-'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">{article.unit}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-right">
                        {article.min_quantity}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <button
                          onClick={() => handleDeleteArticle(article.id)}
                          className="text-red-600 hover:text-red-800"
                        >
                          <TrashIcon className="h-5 w-5" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {articles.length === 0 && (
                <p className="text-center py-8 text-gray-500">Aucun article</p>
              )}
            </div>
          )}

          {/* Movements Tab */}
          {activeTab === 'movements' && (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead>
                  <tr>
                    <th className="table-header px-6 py-3">Date</th>
                    <th className="table-header px-6 py-3">Article</th>
                    <th className="table-header px-6 py-3">Emplacement</th>
                    <th className="table-header px-6 py-3">Type</th>
                    <th className="table-header px-6 py-3 text-right">Quantite</th>
                    <th className="table-header px-6 py-3">Reference</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {movements.map((m) => (
                    <tr key={m.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        {formatDate(m.created_at)}
                      </td>
                      <td className="px-6 py-4">{m.article_name}</td>
                      <td className="px-6 py-4 whitespace-nowrap">{m.location_name}</td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`flex items-center ${movementTypes[m.movement_type]?.color || ''}`}>
                          {m.movement_type === 'ENTREE' && <ArrowDownIcon className="h-4 w-4 mr-1" />}
                          {m.movement_type === 'SORTIE' && <ArrowUpIcon className="h-4 w-4 mr-1" />}
                          {movementTypes[m.movement_type]?.label || m.movement_type}
                        </span>
                      </td>
                      <td className={`px-6 py-4 whitespace-nowrap text-right font-medium ${
                        m.movement_type === 'ENTREE' ? 'text-green-600' : m.movement_type === 'SORTIE' ? 'text-red-600' : ''
                      }`}>
                        {m.movement_type === 'ENTREE' ? '+' : m.movement_type === 'SORTIE' ? '-' : ''}{m.quantity}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {m.reference || '-'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {movements.length === 0 && (
                <p className="text-center py-8 text-gray-500">Aucun mouvement</p>
              )}
            </div>
          )}

          {/* Alerts Tab */}
          {activeTab === 'alerts' && (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead>
                  <tr>
                    <th className="table-header px-6 py-3">Code</th>
                    <th className="table-header px-6 py-3">Article</th>
                    <th className="table-header px-6 py-3 text-right">Stock actuel</th>
                    <th className="table-header px-6 py-3 text-right">Seuil min.</th>
                    <th className="table-header px-6 py-3 text-right">Manquant</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {alerts.map((alert) => (
                    <tr key={alert.article_id} className="hover:bg-gray-50 bg-red-50">
                      <td className="px-6 py-4 whitespace-nowrap font-mono text-sm">
                        {alert.article_code}
                      </td>
                      <td className="px-6 py-4 font-medium">{alert.article_name}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-right font-bold text-red-600">
                        {alert.current_quantity}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right">
                        {alert.min_quantity}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-red-600 font-medium">
                        {alert.shortage}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {alerts.length === 0 && (
                <div className="text-center py-8">
                  <CubeIcon className="h-12 w-12 text-green-400 mx-auto mb-2" />
                  <p className="text-green-600 font-medium">Tous les stocks sont au-dessus du seuil minimum</p>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Add Article Modal */}
      {showAddArticle && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h2 className="text-lg font-semibold mb-4">Nouvel article</h2>
            <form onSubmit={handleAddArticle} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="label">Code *</label>
                  <input
                    type="text"
                    value={articleForm.code}
                    onChange={(e) => setArticleForm({ ...articleForm, code: e.target.value })}
                    className="input"
                    required
                  />
                </div>
                <div>
                  <label className="label">Unite</label>
                  <select
                    value={articleForm.unit}
                    onChange={(e) => setArticleForm({ ...articleForm, unit: e.target.value })}
                    className="input"
                  >
                    <option value="PIECE">Piece</option>
                    <option value="KG">Kg</option>
                    <option value="LITRE">Litre</option>
                    <option value="METRE">Metre</option>
                    <option value="M2">m2</option>
                    <option value="M3">m3</option>
                  </select>
                </div>
              </div>
              <div>
                <label className="label">Nom *</label>
                <input
                  type="text"
                  value={articleForm.name}
                  onChange={(e) => setArticleForm({ ...articleForm, name: e.target.value })}
                  className="input"
                  required
                />
              </div>
              <div>
                <label className="label">Categorie</label>
                <select
                  value={articleForm.category_id}
                  onChange={(e) => setArticleForm({ ...articleForm, category_id: e.target.value })}
                  className="input"
                >
                  <option value="">Aucune</option>
                  {categories.map((c) => (
                    <option key={c.id} value={c.id}>{c.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="label">Seuil minimum</label>
                <input
                  type="number"
                  min="0"
                  value={articleForm.min_quantity}
                  onChange={(e) => setArticleForm({ ...articleForm, min_quantity: parseInt(e.target.value) })}
                  className="input"
                />
              </div>
              <div>
                <label className="label">Description</label>
                <textarea
                  value={articleForm.description}
                  onChange={(e) => setArticleForm({ ...articleForm, description: e.target.value })}
                  className="input"
                  rows={2}
                />
              </div>
              <div className="flex justify-end gap-2 pt-4">
                <button type="button" onClick={() => setShowAddArticle(false)} className="btn-secondary">
                  Annuler
                </button>
                <button type="submit" className="btn-primary">Ajouter</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Add Movement Modal */}
      {showAddMovement && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h2 className="text-lg font-semibold mb-4">Nouveau mouvement</h2>
            <form onSubmit={handleAddMovement} className="space-y-4">
              <div>
                <label className="label">Article *</label>
                <select
                  value={movementForm.article_id}
                  onChange={(e) => setMovementForm({ ...movementForm, article_id: e.target.value })}
                  className="input"
                  required
                >
                  <option value="">Selectionner...</option>
                  {articles.map((a) => (
                    <option key={a.id} value={a.id}>{a.code} - {a.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="label">Emplacement *</label>
                <select
                  value={movementForm.location_id}
                  onChange={(e) => setMovementForm({ ...movementForm, location_id: e.target.value })}
                  className="input"
                  required
                >
                  <option value="">Selectionner...</option>
                  {locations.map((l) => (
                    <option key={l.id} value={l.id}>{l.name}</option>
                  ))}
                </select>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="label">Type *</label>
                  <select
                    value={movementForm.movement_type}
                    onChange={(e) => setMovementForm({ ...movementForm, movement_type: e.target.value })}
                    className="input"
                  >
                    <option value="ENTREE">Entree</option>
                    <option value="SORTIE">Sortie</option>
                    <option value="AJUSTEMENT">Ajustement</option>
                    <option value="INVENTAIRE">Inventaire</option>
                  </select>
                </div>
                <div>
                  <label className="label">Quantite *</label>
                  <input
                    type="number"
                    min="0"
                    step="0.01"
                    value={movementForm.quantity}
                    onChange={(e) => setMovementForm({ ...movementForm, quantity: parseFloat(e.target.value) })}
                    className="input"
                    required
                  />
                </div>
              </div>
              <div>
                <label className="label">Cout unitaire</label>
                <input
                  type="number"
                  min="0"
                  step="0.01"
                  value={movementForm.unit_cost}
                  onChange={(e) => setMovementForm({ ...movementForm, unit_cost: parseFloat(e.target.value) })}
                  className="input"
                />
              </div>
              <div>
                <label className="label">Reference</label>
                <input
                  type="text"
                  value={movementForm.reference}
                  onChange={(e) => setMovementForm({ ...movementForm, reference: e.target.value })}
                  className="input"
                  placeholder="Ex: Bon de livraison #123"
                />
              </div>
              <div className="flex justify-end gap-2 pt-4">
                <button type="button" onClick={() => setShowAddMovement(false)} className="btn-secondary">
                  Annuler
                </button>
                <button type="submit" className="btn-primary">Enregistrer</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
