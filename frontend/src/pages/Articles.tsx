import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { articlesApi } from '../services/api'
import { PlusIcon, PencilIcon, TrashIcon } from '@heroicons/react/24/outline'
import toast from 'react-hot-toast'

interface Article {
  id: number
  code: string
  name: string
  article_type: string
  billing_mode: string
  base_price: number
  default_vat_rate: number
  is_active: boolean
}

const typeLabels: Record<string, string> = {
  service: 'Service',
  product: 'Produit',
  expense: 'Frais',
}

const modeLabels: Record<string, string> = {
  hour: 'Heure',
  day: 'Jour',
  unit: 'Unité',
  km: 'Km',
  flat: 'Forfait',
}

export default function Articles() {
  const [articles, setArticles] = useState<Article[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')

  useEffect(() => {
    loadArticles()
  }, [])

  const loadArticles = async () => {
    try {
      const response = await articlesApi.list({ is_active: true })
      setArticles(response.data)
    } catch (error) {
      toast.error('Erreur lors du chargement des articles')
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (id: number) => {
    if (!confirm('Êtes-vous sûr de vouloir désactiver cet article ?')) return

    try {
      await articlesApi.delete(id)
      toast.success('Article désactivé')
      loadArticles()
    } catch (error) {
      toast.error('Erreur lors de la désactivation')
    }
  }

  const filteredArticles = articles.filter(
    (article) =>
      article.code.toLowerCase().includes(search.toLowerCase()) ||
      article.name.toLowerCase().includes(search.toLowerCase())
  )

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
        <h1 className="page-title mb-0">Articles / Services</h1>
        <Link to="/articles/new" className="btn-primary flex items-center">
          <PlusIcon className="h-5 w-5 mr-1" />
          Nouvel article
        </Link>
      </div>

      <div className="card">
        <div className="mb-4">
          <input
            type="text"
            placeholder="Rechercher un article..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="input max-w-md"
          />
        </div>

        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead>
              <tr>
                <th className="table-header px-6 py-3">Code</th>
                <th className="table-header px-6 py-3">Nom</th>
                <th className="table-header px-6 py-3">Type</th>
                <th className="table-header px-6 py-3">Mode</th>
                <th className="table-header px-6 py-3">Prix HTVA</th>
                <th className="table-header px-6 py-3">TVA</th>
                <th className="table-header px-6 py-3">Actions</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredArticles.map((article) => (
                <tr key={article.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap font-mono text-sm">
                    {article.code}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap font-medium">
                    {article.name}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-gray-500">
                    {typeLabels[article.article_type] || article.article_type}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-gray-500">
                    {modeLabels[article.billing_mode] || article.billing_mode}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {article.base_price.toFixed(2)} €
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-gray-500">
                    {article.default_vat_rate}%
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <Link
                      to={`/articles/${article.id}`}
                      className="text-primary-600 hover:text-primary-800 mr-3"
                    >
                      <PencilIcon className="h-5 w-5 inline" />
                    </Link>
                    <button
                      onClick={() => handleDelete(article.id)}
                      className="text-red-600 hover:text-red-800"
                    >
                      <TrashIcon className="h-5 w-5 inline" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {filteredArticles.length === 0 && (
            <p className="text-center py-8 text-gray-500">Aucun article trouvé</p>
          )}
        </div>
      </div>
    </div>
  )
}
