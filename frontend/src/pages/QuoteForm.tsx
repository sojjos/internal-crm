import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { quotesApi, clientsApi, articlesApi } from '../services/api'
import { PlusIcon, TrashIcon } from '@heroicons/react/24/outline'
import toast from 'react-hot-toast'

interface QuoteLine {
  id?: number
  article_id: number | null
  description: string
  quantity: number
  unit_price: number
  vat_rate: number
  discount_percent: number
  total_htva: number
}

interface Article {
  id: number
  code: string
  name: string
  unit_price: number
  vat_rate: number
}

export default function QuoteForm() {
  const { id } = useParams()
  const navigate = useNavigate()
  const isEdit = Boolean(id)

  const [loading, setLoading] = useState(false)
  const [clients, setClients] = useState<{ id: number; name: string }[]>([])
  const [articles, setArticles] = useState<Article[]>([])

  const [form, setForm] = useState({
    client_id: '',
    subject: '',
    quote_date: new Date().toISOString().split('T')[0],
    valid_until: '',
    notes: '',
    terms: '',
  })

  const [lines, setLines] = useState<QuoteLine[]>([])

  useEffect(() => {
    loadInitialData()
    // Set default validity (30 days)
    const validUntil = new Date()
    validUntil.setDate(validUntil.getDate() + 30)
    setForm(f => ({ ...f, valid_until: validUntil.toISOString().split('T')[0] }))
  }, [])

  useEffect(() => {
    if (id) {
      loadQuote()
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

  const loadQuote = async () => {
    setLoading(true)
    try {
      const response = await quotesApi.get(parseInt(id!))
      const data = response.data

      setForm({
        client_id: data.client_id.toString(),
        subject: data.subject,
        quote_date: data.quote_date,
        valid_until: data.valid_until,
        notes: data.notes || '',
        terms: data.terms || '',
      })

      setLines(data.lines || [])
    } catch (error) {
      toast.error('Erreur lors du chargement')
      navigate('/quotes')
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
        notes: form.notes || null,
        terms: form.terms || null,
      }

      if (isEdit) {
        await quotesApi.update(parseInt(id!), payload)
        toast.success('Devis mis a jour')
      } else {
        const response = await quotesApi.create(payload)
        toast.success('Devis cree')
        navigate(`/quotes/${response.data.id}`)
        return
      }

      navigate('/quotes')
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
        discount_percent: 0,
        total_htva: 0,
      },
    ])
  }

  const updateLine = (index: number, field: keyof QuoteLine, value: any) => {
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

    if (['quantity', 'unit_price', 'discount_percent'].includes(field)) {
      const line = newLines[index]
      const subtotal = line.quantity * line.unit_price
      const discount = subtotal * (line.discount_percent / 100)
      newLines[index].total_htva = subtotal - discount
    }

    setLines(newLines)
  }

  const removeLine = async (index: number) => {
    const line = lines[index]
    if (line.id && isEdit) {
      try {
        await quotesApi.lines.delete(parseInt(id!), line.id)
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
        await quotesApi.lines.update(parseInt(id!), line.id, line)
      } else {
        const response = await quotesApi.lines.add(parseInt(id!), line)
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
        {isEdit ? 'Modifier le devis' : 'Nouveau devis'}
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
              <label className="label">Objet *</label>
              <input
                type="text"
                value={form.subject}
                onChange={(e) => setForm({ ...form, subject: e.target.value })}
                className="input"
                required
                placeholder="Ex: Developpement site web"
              />
            </div>

            <div>
              <label className="label">Date du devis *</label>
              <input
                type="date"
                value={form.quote_date}
                onChange={(e) => setForm({ ...form, quote_date: e.target.value })}
                className="input"
                required
              />
            </div>

            <div>
              <label className="label">Valide jusqu'au *</label>
              <input
                type="date"
                value={form.valid_until}
                onChange={(e) => setForm({ ...form, valid_until: e.target.value })}
                className="input"
                required
              />
            </div>

            <div className="md:col-span-2">
              <label className="label">Notes</label>
              <textarea
                value={form.notes}
                onChange={(e) => setForm({ ...form, notes: e.target.value })}
                className="input"
                rows={2}
                placeholder="Notes visibles sur le devis"
              />
            </div>

            <div className="md:col-span-2">
              <label className="label">Conditions</label>
              <textarea
                value={form.terms}
                onChange={(e) => setForm({ ...form, terms: e.target.value })}
                className="input"
                rows={2}
                placeholder="Conditions generales, delais, etc."
              />
            </div>
          </div>
        </div>

        {/* Lines section - only for edit mode */}
        {isEdit && (
          <div className="card mb-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-semibold">Lignes du devis</h2>
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
                    <th className="table-header px-4 py-2 w-20">Qte</th>
                    <th className="table-header px-4 py-2 w-28">Prix unit.</th>
                    <th className="table-header px-4 py-2 w-20">Remise %</th>
                    <th className="table-header px-4 py-2 w-20">TVA %</th>
                    <th className="table-header px-4 py-2 w-28">Total HTVA</th>
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
                        <input
                          type="number"
                          min="0"
                          max="100"
                          step="0.5"
                          value={line.discount_percent}
                          onChange={(e) => updateLine(index, 'discount_percent', parseFloat(e.target.value))}
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
            onClick={() => navigate('/quotes')}
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
