import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { interventionsApi, clientsApi, articlesApi } from '../services/api'
import { PlusIcon, TrashIcon } from '@heroicons/react/24/outline'
import toast from 'react-hot-toast'

interface InterventionLine {
  id?: number
  article_id: number | null
  description: string
  quantity: number
  unit_price: number
  vat_rate: number
  total_htva: number
}

interface Article {
  id: number
  code: string
  name: string
  unit_price: number
  vat_rate: number
}

export default function InterventionForm() {
  const { id } = useParams()
  const navigate = useNavigate()
  const isEdit = Boolean(id)

  const [loading, setLoading] = useState(false)
  const [clients, setClients] = useState<{ id: number; name: string }[]>([])
  const [articles, setArticles] = useState<Article[]>([])

  const [form, setForm] = useState({
    client_id: '',
    title: '',
    description: '',
    scheduled_date: new Date().toISOString().split('T')[0],
    scheduled_time: '',
    estimated_duration: '',
    is_billable: true,
    notes: '',
  })

  const [lines, setLines] = useState<InterventionLine[]>([])

  useEffect(() => {
    loadInitialData()
  }, [])

  useEffect(() => {
    if (id) {
      loadIntervention()
    }
  }, [id])

  const loadInitialData = async () => {
    try {
      const [clientsRes, articlesRes] = await Promise.all([
        clientsApi.list({ is_active: true }),
        articlesApi.list({ is_active: true }),
      ])
      setClients(clientsRes.data)
      setArticles(articlesRes.data)
    } catch (error) {
      console.error('Error loading initial data:', error)
    }
  }

  const loadIntervention = async () => {
    setLoading(true)
    try {
      const response = await interventionsApi.get(parseInt(id!))
      const data = response.data

      setForm({
        client_id: data.client_id.toString(),
        title: data.title,
        description: data.description || '',
        scheduled_date: data.scheduled_date,
        scheduled_time: data.scheduled_time || '',
        estimated_duration: data.estimated_duration?.toString() || '',
        is_billable: data.is_billable,
        notes: data.notes || '',
      })

      setLines(data.lines || [])
    } catch (error) {
      toast.error('Erreur lors du chargement')
      navigate('/interventions')
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)

    try {
      const payload = {
        ...form,
        client_id: parseInt(form.client_id),
        estimated_duration: form.estimated_duration ? parseInt(form.estimated_duration) : null,
        scheduled_time: form.scheduled_time || null,
        description: form.description || null,
        notes: form.notes || null,
      }

      if (isEdit) {
        await interventionsApi.update(parseInt(id!), payload)
        toast.success('Intervention mise a jour')
      } else {
        const response = await interventionsApi.create(payload)
        toast.success('Intervention creee')
        navigate(`/interventions/${response.data.id}`)
        return
      }

      navigate('/interventions')
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Erreur')
    } finally {
      setLoading(false)
    }
  }

  const addLine = () => {
    setLines([
      ...lines,
      {
        article_id: null,
        description: '',
        quantity: 1,
        unit_price: 0,
        vat_rate: 21,
        total_htva: 0,
      },
    ])
  }

  const updateLine = (index: number, field: keyof InterventionLine, value: any) => {
    const newLines = [...lines]
    newLines[index] = { ...newLines[index], [field]: value }

    if (field === 'article_id' && value) {
      const article = articles.find(a => a.id === parseInt(value))
      if (article) {
        newLines[index].description = article.name
        newLines[index].unit_price = article.unit_price
        newLines[index].vat_rate = article.vat_rate
      }
    }

    if (['quantity', 'unit_price'].includes(field)) {
      newLines[index].total_htva = newLines[index].quantity * newLines[index].unit_price
    }

    setLines(newLines)
  }

  const removeLine = async (index: number) => {
    const line = lines[index]
    if (line.id && isEdit) {
      try {
        await interventionsApi.lines.delete(parseInt(id!), line.id)
        toast.success('Ligne supprimee')
      } catch (error: any) {
        toast.error(error.response?.data?.detail || 'Erreur')
        return
      }
    }
    setLines(lines.filter((_, i) => i !== index))
  }

  const saveLine = async (index: number) => {
    if (!isEdit) return

    const line = lines[index]
    try {
      if (line.id) {
        await interventionsApi.lines.update(parseInt(id!), line.id, line)
      } else {
        const response = await interventionsApi.lines.add(parseInt(id!), line)
        const newLines = [...lines]
        newLines[index] = response.data
        setLines(newLines)
      }
      toast.success('Ligne sauvegardee')
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

  const totalHtva = lines.reduce((sum, l) => sum + l.total_htva, 0)
  const totalVat = lines.reduce((sum, l) => sum + (l.total_htva * l.vat_rate / 100), 0)
  const totalTtc = totalHtva + totalVat

  if (loading && isEdit) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  return (
    <div>
      <h1 className="page-title">
        {isEdit ? 'Modifier l\'intervention' : 'Nouvelle intervention'}
      </h1>

      <form onSubmit={handleSubmit}>
        <div className="card mb-6">
          <h2 className="text-lg font-semibold mb-4">Informations generales</h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="label">Client *</label>
              <select
                value={form.client_id}
                onChange={(e) => setForm({ ...form, client_id: e.target.value })}
                className="input"
                required
              >
                <option value="">Selectionner un client</option>
                {clients.map((c) => (
                  <option key={c.id} value={c.id}>{c.name}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="label">Titre *</label>
              <input
                type="text"
                value={form.title}
                onChange={(e) => setForm({ ...form, title: e.target.value })}
                className="input"
                required
              />
            </div>

            <div>
              <label className="label">Date prevue *</label>
              <input
                type="date"
                value={form.scheduled_date}
                onChange={(e) => setForm({ ...form, scheduled_date: e.target.value })}
                className="input"
                required
              />
            </div>

            <div>
              <label className="label">Heure</label>
              <input
                type="time"
                value={form.scheduled_time}
                onChange={(e) => setForm({ ...form, scheduled_time: e.target.value })}
                className="input"
              />
            </div>

            <div>
              <label className="label">Duree estimee (heures)</label>
              <input
                type="number"
                min="0"
                step="0.5"
                value={form.estimated_duration}
                onChange={(e) => setForm({ ...form, estimated_duration: e.target.value })}
                className="input"
              />
            </div>

            <div className="flex items-center pt-6">
              <input
                type="checkbox"
                id="is_billable"
                checked={form.is_billable}
                onChange={(e) => setForm({ ...form, is_billable: e.target.checked })}
                className="rounded border-gray-300 mr-2"
              />
              <label htmlFor="is_billable">Intervention facturable</label>
            </div>

            <div className="md:col-span-2">
              <label className="label">Description</label>
              <textarea
                value={form.description}
                onChange={(e) => setForm({ ...form, description: e.target.value })}
                className="input"
                rows={3}
              />
            </div>

            <div className="md:col-span-2">
              <label className="label">Notes internes</label>
              <textarea
                value={form.notes}
                onChange={(e) => setForm({ ...form, notes: e.target.value })}
                className="input"
                rows={2}
              />
            </div>
          </div>
        </div>

        {/* Lines section - only for edit mode */}
        {isEdit && (
          <div className="card mb-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-semibold">Lignes d'intervention</h2>
              <button
                type="button"
                onClick={addLine}
                className="btn-secondary flex items-center"
              >
                <PlusIcon className="h-4 w-4 mr-1" />
                Ajouter une ligne
              </button>
            </div>

            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead>
                  <tr>
                    <th className="table-header px-4 py-2">Article</th>
                    <th className="table-header px-4 py-2">Description</th>
                    <th className="table-header px-4 py-2 w-24">Qte</th>
                    <th className="table-header px-4 py-2 w-32">Prix unit.</th>
                    <th className="table-header px-4 py-2 w-24">TVA %</th>
                    <th className="table-header px-4 py-2 w-32">Total HTVA</th>
                    <th className="table-header px-4 py-2 w-24">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {lines.map((line, index) => (
                    <tr key={index}>
                      <td className="px-4 py-2">
                        <select
                          value={line.article_id || ''}
                          onChange={(e) => updateLine(index, 'article_id', e.target.value ? parseInt(e.target.value) : null)}
                          className="input text-sm"
                        >
                          <option value="">Libre</option>
                          {articles.map((a) => (
                            <option key={a.id} value={a.id}>{a.code} - {a.name}</option>
                          ))}
                        </select>
                      </td>
                      <td className="px-4 py-2">
                        <input
                          type="text"
                          value={line.description}
                          onChange={(e) => updateLine(index, 'description', e.target.value)}
                          className="input text-sm"
                        />
                      </td>
                      <td className="px-4 py-2">
                        <input
                          type="number"
                          min="0"
                          step="0.01"
                          value={line.quantity}
                          onChange={(e) => updateLine(index, 'quantity', parseFloat(e.target.value))}
                          className="input text-sm"
                        />
                      </td>
                      <td className="px-4 py-2">
                        <input
                          type="number"
                          min="0"
                          step="0.01"
                          value={line.unit_price}
                          onChange={(e) => updateLine(index, 'unit_price', parseFloat(e.target.value))}
                          className="input text-sm"
                        />
                      </td>
                      <td className="px-4 py-2">
                        <select
                          value={line.vat_rate}
                          onChange={(e) => updateLine(index, 'vat_rate', parseFloat(e.target.value))}
                          className="input text-sm"
                        >
                          <option value="0">0%</option>
                          <option value="6">6%</option>
                          <option value="12">12%</option>
                          <option value="21">21%</option>
                        </select>
                      </td>
                      <td className="px-4 py-2 text-right font-medium">
                        {formatCurrency(line.total_htva)}
                      </td>
                      <td className="px-4 py-2">
                        <div className="flex gap-1">
                          <button
                            type="button"
                            onClick={() => saveLine(index)}
                            className="text-green-600 hover:text-green-800 text-sm"
                          >
                            Sauver
                          </button>
                          <button
                            type="button"
                            onClick={() => removeLine(index)}
                            className="text-red-600 hover:text-red-800"
                          >
                            <TrashIcon className="h-4 w-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>

              {lines.length === 0 && (
                <p className="text-center py-4 text-gray-500">
                  Aucune ligne. Cliquez sur "Ajouter une ligne" pour commencer.
                </p>
              )}
            </div>

            {/* Totals */}
            {lines.length > 0 && (
              <div className="mt-4 pt-4 border-t">
                <div className="flex justify-end">
                  <div className="w-64 space-y-2">
                    <div className="flex justify-between">
                      <span>Total HTVA:</span>
                      <span className="font-medium">{formatCurrency(totalHtva)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>TVA:</span>
                      <span>{formatCurrency(totalVat)}</span>
                    </div>
                    <div className="flex justify-between text-lg font-bold">
                      <span>Total TTC:</span>
                      <span>{formatCurrency(totalTtc)}</span>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        <div className="flex justify-end gap-4">
          <button
            type="button"
            onClick={() => navigate('/interventions')}
            className="btn-secondary"
          >
            Annuler
          </button>
          <button type="submit" className="btn-primary" disabled={loading}>
            {loading ? 'Enregistrement...' : isEdit ? 'Mettre a jour' : 'Creer'}
          </button>
        </div>
      </form>
    </div>
  )
}
