import { useEffect, useState } from 'react'
import { documentsApi, clientsApi, suppliersApi } from '../services/api'
import {
  PlusIcon,
  TrashIcon,
  ArrowDownTrayIcon,
  FolderIcon,
  ExclamationTriangleIcon,
  FunnelIcon,
} from '@heroicons/react/24/outline'
import toast from 'react-hot-toast'

interface Document {
  id: number
  name: string
  description: string | null
  document_type: string
  category_name: string | null
  file_path: string
  file_size: number | null
  mime_type: string | null
  expiry_date: string | null
  client_name: string | null
  supplier_name: string | null
  created_at: string
}

interface Category {
  id: number
  name: string
  description: string | null
}

const documentTypes: Record<string, string> = {
  CONTRAT: 'Contrat',
  ASSURANCE: 'Assurance',
  CERTIFICAT: 'Certificat',
  FACTURE: 'Facture',
  BON_COMMANDE: 'Bon de commande',
  GARANTIE: 'Garantie',
  LEGAL: 'Document legal',
  TECHNIQUE: 'Document technique',
  AUTRE: 'Autre',
}

export default function Documents() {
  const [documents, setDocuments] = useState<Document[]>([])
  const [categories, setCategories] = useState<Category[]>([])
  const [expiringDocs, setExpiringDocs] = useState<Document[]>([])
  const [loading, setLoading] = useState(true)
  const [showUpload, setShowUpload] = useState(false)
  const [showFilters, setShowFilters] = useState(false)

  const [typeFilter, setTypeFilter] = useState('')
  const [categoryFilter, setCategoryFilter] = useState('')
  const [entityFilter, setEntityFilter] = useState<'all' | 'clients' | 'suppliers'>('all')

  const [uploadForm, setUploadForm] = useState({
    name: '',
    description: '',
    document_type: 'AUTRE',
    category_id: '',
    client_id: '',
    supplier_id: '',
    expiry_date: '',
    file: null as File | null,
  })

  const [clients, setClients] = useState<{ id: number; name: string }[]>([])
  const [suppliers, setSuppliers] = useState<{ id: number; name: string }[]>([])

  useEffect(() => {
    loadData()
  }, [typeFilter, categoryFilter, entityFilter])

  const loadData = async () => {
    setLoading(true)
    try {
      const params: any = {}
      if (typeFilter) params.document_type = typeFilter
      if (categoryFilter) params.category_id = categoryFilter

      const [docsRes, catsRes, expiringRes, clientsRes, suppliersRes] = await Promise.all([
        documentsApi.list(params),
        documentsApi.categories.list(),
        documentsApi.expiring(30),
        clientsApi.list({ is_active: true }),
        suppliersApi.list({ is_active: true }),
      ])

      setDocuments(docsRes.data)
      setCategories(catsRes.data)
      setExpiringDocs(expiringRes.data)
      setClients(clientsRes.data)
      setSuppliers(suppliersRes.data)
    } catch (error) {
      toast.error('Erreur lors du chargement')
    } finally {
      setLoading(false)
    }
  }

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!uploadForm.file) {
      toast.error('Veuillez selectionner un fichier')
      return
    }

    const formData = new FormData()
    formData.append('file', uploadForm.file)
    formData.append('name', uploadForm.name)
    formData.append('document_type', uploadForm.document_type)
    if (uploadForm.description) formData.append('description', uploadForm.description)
    if (uploadForm.category_id) formData.append('category_id', uploadForm.category_id)
    if (uploadForm.client_id) formData.append('client_id', uploadForm.client_id)
    if (uploadForm.supplier_id) formData.append('supplier_id', uploadForm.supplier_id)
    if (uploadForm.expiry_date) formData.append('expiry_date', uploadForm.expiry_date)

    try {
      await documentsApi.create(formData)
      toast.success('Document telecharge')
      setShowUpload(false)
      setUploadForm({
        name: '',
        description: '',
        document_type: 'AUTRE',
        category_id: '',
        client_id: '',
        supplier_id: '',
        expiry_date: '',
        file: null,
      })
      loadData()
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Erreur lors du telechargement')
    }
  }

  const handleDelete = async (id: number) => {
    if (!confirm('Supprimer ce document ?')) return

    try {
      await documentsApi.delete(id)
      toast.success('Document supprime')
      loadData()
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Erreur')
    }
  }

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('fr-BE')
  }

  const formatFileSize = (bytes: number | null) => {
    if (!bytes) return '-'
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  const isExpiringSoon = (expiryDate: string | null) => {
    if (!expiryDate) return false
    const expiry = new Date(expiryDate)
    const today = new Date()
    const diff = (expiry.getTime() - today.getTime()) / (1000 * 60 * 60 * 24)
    return diff <= 30 && diff > 0
  }

  const isExpired = (expiryDate: string | null) => {
    if (!expiryDate) return false
    return new Date(expiryDate) < new Date()
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
        <h1 className="page-title mb-0">Gestion Documentaire (GED)</h1>
        <div className="flex gap-2">
          <button
            onClick={() => setShowFilters(!showFilters)}
            className="btn-secondary flex items-center"
          >
            <FunnelIcon className="h-5 w-5 mr-1" />
            Filtres
          </button>
          <button
            onClick={() => setShowUpload(true)}
            className="btn-primary flex items-center"
          >
            <PlusIcon className="h-5 w-5 mr-1" />
            Nouveau document
          </button>
        </div>
      </div>

      {/* Expiring documents alert */}
      {expiringDocs.length > 0 && (
        <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-6">
          <div className="flex items-center">
            <ExclamationTriangleIcon className="h-5 w-5 text-yellow-400 mr-2" />
            <p className="text-yellow-700">
              <strong>{expiringDocs.length} document(s)</strong> arrivent a expiration dans les 30 jours
            </p>
          </div>
        </div>
      )}

      {/* Filters */}
      {showFilters && (
        <div className="card mb-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="label">Type de document</label>
              <select
                value={typeFilter}
                onChange={(e) => setTypeFilter(e.target.value)}
                className="input"
              >
                <option value="">Tous</option>
                {Object.entries(documentTypes).map(([key, label]) => (
                  <option key={key} value={key}>{label}</option>
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
              <label className="label">Entite liee</label>
              <select
                value={entityFilter}
                onChange={(e) => setEntityFilter(e.target.value as any)}
                className="input"
              >
                <option value="all">Tous</option>
                <option value="clients">Clients</option>
                <option value="suppliers">Fournisseurs</option>
              </select>
            </div>
          </div>
        </div>
      )}

      {/* Upload Modal */}
      {showUpload && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-lg">
            <h2 className="text-lg font-semibold mb-4">Telecharger un document</h2>
            <form onSubmit={handleUpload} className="space-y-4">
              <div>
                <label className="label">Fichier *</label>
                <input
                  type="file"
                  onChange={(e) => setUploadForm({ ...uploadForm, file: e.target.files?.[0] || null })}
                  className="input"
                  required
                />
              </div>
              <div>
                <label className="label">Nom *</label>
                <input
                  type="text"
                  value={uploadForm.name}
                  onChange={(e) => setUploadForm({ ...uploadForm, name: e.target.value })}
                  className="input"
                  required
                />
              </div>
              <div>
                <label className="label">Type</label>
                <select
                  value={uploadForm.document_type}
                  onChange={(e) => setUploadForm({ ...uploadForm, document_type: e.target.value })}
                  className="input"
                >
                  {Object.entries(documentTypes).map(([key, label]) => (
                    <option key={key} value={key}>{label}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="label">Categorie</label>
                <select
                  value={uploadForm.category_id}
                  onChange={(e) => setUploadForm({ ...uploadForm, category_id: e.target.value })}
                  className="input"
                >
                  <option value="">Aucune</option>
                  {categories.map((c) => (
                    <option key={c.id} value={c.id}>{c.name}</option>
                  ))}
                </select>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="label">Client</label>
                  <select
                    value={uploadForm.client_id}
                    onChange={(e) => setUploadForm({ ...uploadForm, client_id: e.target.value })}
                    className="input"
                  >
                    <option value="">Aucun</option>
                    {clients.map((c) => (
                      <option key={c.id} value={c.id}>{c.name}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="label">Fournisseur</label>
                  <select
                    value={uploadForm.supplier_id}
                    onChange={(e) => setUploadForm({ ...uploadForm, supplier_id: e.target.value })}
                    className="input"
                  >
                    <option value="">Aucun</option>
                    {suppliers.map((s) => (
                      <option key={s.id} value={s.id}>{s.name}</option>
                    ))}
                  </select>
                </div>
              </div>
              <div>
                <label className="label">Date d'expiration</label>
                <input
                  type="date"
                  value={uploadForm.expiry_date}
                  onChange={(e) => setUploadForm({ ...uploadForm, expiry_date: e.target.value })}
                  className="input"
                />
              </div>
              <div>
                <label className="label">Description</label>
                <textarea
                  value={uploadForm.description}
                  onChange={(e) => setUploadForm({ ...uploadForm, description: e.target.value })}
                  className="input"
                  rows={2}
                />
              </div>
              <div className="flex justify-end gap-2 pt-4">
                <button
                  type="button"
                  onClick={() => setShowUpload(false)}
                  className="btn-secondary"
                >
                  Annuler
                </button>
                <button type="submit" className="btn-primary">
                  Telecharger
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Documents Table */}
      <div className="card">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead>
              <tr>
                <th className="table-header px-6 py-3">Document</th>
                <th className="table-header px-6 py-3">Type</th>
                <th className="table-header px-6 py-3">Entite liee</th>
                <th className="table-header px-6 py-3">Taille</th>
                <th className="table-header px-6 py-3">Expiration</th>
                <th className="table-header px-6 py-3">Date ajout</th>
                <th className="table-header px-6 py-3">Actions</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {documents.map((doc) => (
                <tr key={doc.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4">
                    <div className="flex items-center">
                      <FolderIcon className="h-5 w-5 text-gray-400 mr-2" />
                      <div>
                        <div className="font-medium">{doc.name}</div>
                        {doc.description && (
                          <div className="text-xs text-gray-500">{doc.description}</div>
                        )}
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="px-2 py-1 text-xs rounded-full bg-gray-100">
                      {documentTypes[doc.document_type] || doc.document_type}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {doc.client_name && (
                      <span className="text-blue-600">{doc.client_name}</span>
                    )}
                    {doc.supplier_name && (
                      <span className="text-green-600">{doc.supplier_name}</span>
                    )}
                    {!doc.client_name && !doc.supplier_name && '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {formatFileSize(doc.file_size)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {doc.expiry_date ? (
                      <span className={`px-2 py-1 text-xs rounded-full ${
                        isExpired(doc.expiry_date)
                          ? 'bg-red-100 text-red-800'
                          : isExpiringSoon(doc.expiry_date)
                          ? 'bg-yellow-100 text-yellow-800'
                          : 'bg-green-100 text-green-800'
                      }`}>
                        {formatDate(doc.expiry_date)}
                      </span>
                    ) : (
                      '-'
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {formatDate(doc.created_at)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center gap-2">
                      <a
                        href={`/uploads/${doc.file_path}`}
                        download
                        className="text-primary-600 hover:text-primary-800"
                        title="Telecharger"
                      >
                        <ArrowDownTrayIcon className="h-5 w-5" />
                      </a>
                      <button
                        onClick={() => handleDelete(doc.id)}
                        className="text-red-600 hover:text-red-800"
                        title="Supprimer"
                      >
                        <TrashIcon className="h-5 w-5" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {documents.length === 0 && (
            <p className="text-center py-8 text-gray-500">
              Aucun document trouve
            </p>
          )}
        </div>
      </div>
    </div>
  )
}
