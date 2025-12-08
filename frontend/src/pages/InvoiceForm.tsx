import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useForm, useFieldArray } from 'react-hook-form'
import { invoicesApi, clientsApi, articlesApi } from '../services/api'
import { PlusIcon, TrashIcon } from '@heroicons/react/24/outline'
import toast from 'react-hot-toast'

interface InvoiceLine {
  description: string
  unit: string
  quantity: number
  unit_price: number
  vat_rate: number
  discount_percent: number
  article_id?: number
}

interface InvoiceFormData {
  client_id: number
  invoice_date: string
  due_date: string
  notes: string
  footer_notes: string
  lines: InvoiceLine[]
}

interface Client {
  id: number
  name: string
}

interface Article {
  id: number
  code: string
  name: string
  base_price: number
  default_vat_rate: number
  billing_mode: string
}

export default function InvoiceForm() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [clients, setClients] = useState<Client[]>([])
  const [articles, setArticles] = useState<Article[]>([])
  const isEdit = Boolean(id)

  const today = new Date().toISOString().split('T')[0]
  const defaultDueDate = new Date(Date.now() + 30 * 24 * 60 * 60 * 1000)
    .toISOString()
    .split('T')[0]

  const {
    register,
    control,
    handleSubmit,
    watch,
    setValue,
    reset,
    formState: { errors },
  } = useForm<InvoiceFormData>({
    defaultValues: {
      invoice_date: today,
      due_date: defaultDueDate,
      lines: [
        {
          description: '',
          unit: 'u',
          quantity: 1,
          unit_price: 0,
          vat_rate: 21,
          discount_percent: 0,
        },
      ],
    },
  })

  const { fields, append, remove } = useFieldArray({
    control,
    name: 'lines',
  })

  const lines = watch('lines')

  useEffect(() => {
    loadData()
    if (isEdit) {
      loadInvoice()
    }
  }, [id])

  const loadData = async () => {
    try {
      const [clientsRes, articlesRes] = await Promise.all([
        clientsApi.list({ is_active: true }),
        articlesApi.list({ is_active: true }),
      ])
      setClients(clientsRes.data)
      setArticles(articlesRes.data)
    } catch (error) {
      toast.error('Erreur lors du chargement des données')
    }
  }

  const loadInvoice = async () => {
    try {
      const response = await invoicesApi.get(Number(id))
      const invoice = response.data
      reset({
        client_id: invoice.client_id,
        invoice_date: invoice.invoice_date,
        due_date: invoice.due_date,
        notes: invoice.notes || '',
        footer_notes: invoice.footer_notes || '',
        lines: invoice.lines.map((l: any) => ({
          description: l.description,
          unit: l.unit,
          quantity: l.quantity,
          unit_price: l.unit_price,
          vat_rate: l.vat_rate,
          discount_percent: l.discount_percent,
          article_id: l.article_id,
        })),
      })
    } catch (error) {
      toast.error('Erreur lors du chargement de la facture')
      navigate('/invoices')
    }
  }

  const handleArticleSelect = (index: number, articleId: string) => {
    if (!articleId) return
    const article = articles.find((a) => a.id === Number(articleId))
    if (article) {
      setValue(`lines.${index}.description`, article.name)
      setValue(`lines.${index}.unit_price`, article.base_price)
      setValue(`lines.${index}.vat_rate`, article.default_vat_rate)
      setValue(`lines.${index}.article_id`, article.id)

      const modeUnits: Record<string, string> = {
        hour: 'h',
        day: 'j',
        km: 'km',
        unit: 'u',
        flat: 'forfait',
      }
      setValue(`lines.${index}.unit`, modeUnits[article.billing_mode] || 'u')
    }
  }

  const calculateLineTotal = (line: InvoiceLine) => {
    const subtotal = line.quantity * line.unit_price
    const afterDiscount = subtotal * (1 - (line.discount_percent || 0) / 100)
    return afterDiscount
  }

  const calculateTotals = () => {
    let totalHtva = 0
    let totalVat = 0

    lines.forEach((line) => {
      const lineHtva = calculateLineTotal(line)
      totalHtva += lineHtva
      totalVat += lineHtva * (line.vat_rate / 100)
    })

    return {
      htva: totalHtva,
      vat: totalVat,
      tvac: totalHtva + totalVat,
    }
  }

  const totals = calculateTotals()

  const onSubmit = async (data: InvoiceFormData) => {
    if (data.lines.length === 0) {
      toast.error('Ajoutez au moins une ligne')
      return
    }

    setLoading(true)
    try {
      if (isEdit) {
        // For edit, we would need to handle differently
        toast.error("L'édition n'est pas encore implémentée")
      } else {
        await invoicesApi.create(data)
        toast.success('Facture créée')
      }
      navigate('/invoices')
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Erreur lors de la sauvegarde')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <h1 className="page-title">
        {isEdit ? 'Modifier la facture' : 'Nouvelle facture'}
      </h1>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {/* Header */}
        <div className="card">
          <h2 className="text-lg font-semibold mb-4">Informations générales</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <label className="label">Client *</label>
              <select
                {...register('client_id', {
                  required: 'Sélectionnez un client',
                  valueAsNumber: true,
                })}
                className="input"
              >
                <option value="">-- Sélectionner --</option>
                {clients.map((client) => (
                  <option key={client.id} value={client.id}>
                    {client.name}
                  </option>
                ))}
              </select>
              {errors.client_id && (
                <p className="text-red-500 text-sm mt-1">
                  {errors.client_id.message}
                </p>
              )}
            </div>

            <div>
              <label className="label">Date de facture</label>
              <input type="date" {...register('invoice_date')} className="input" />
            </div>

            <div>
              <label className="label">Date d'échéance</label>
              <input type="date" {...register('due_date')} className="input" />
            </div>
          </div>
        </div>

        {/* Lines */}
        <div className="card">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-semibold">Lignes de facture</h2>
            <button
              type="button"
              onClick={() =>
                append({
                  description: '',
                  unit: 'u',
                  quantity: 1,
                  unit_price: 0,
                  vat_rate: 21,
                  discount_percent: 0,
                })
              }
              className="btn-secondary flex items-center text-sm"
            >
              <PlusIcon className="h-4 w-4 mr-1" />
              Ajouter une ligne
            </button>
          </div>

          <div className="overflow-x-auto">
            <table className="min-w-full">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-2 px-2 text-sm font-medium">Article</th>
                  <th className="text-left py-2 px-2 text-sm font-medium">Description</th>
                  <th className="text-left py-2 px-2 text-sm font-medium w-20">Qté</th>
                  <th className="text-left py-2 px-2 text-sm font-medium w-16">Unité</th>
                  <th className="text-left py-2 px-2 text-sm font-medium w-28">Prix unit.</th>
                  <th className="text-left py-2 px-2 text-sm font-medium w-20">TVA %</th>
                  <th className="text-left py-2 px-2 text-sm font-medium w-28">Total HTVA</th>
                  <th className="w-10"></th>
                </tr>
              </thead>
              <tbody>
                {fields.map((field, index) => (
                  <tr key={field.id} className="border-b">
                    <td className="py-2 px-2">
                      <select
                        onChange={(e) => handleArticleSelect(index, e.target.value)}
                        className="input text-sm"
                      >
                        <option value="">-- Article --</option>
                        {articles.map((article) => (
                          <option key={article.id} value={article.id}>
                            {article.code} - {article.name}
                          </option>
                        ))}
                      </select>
                    </td>
                    <td className="py-2 px-2">
                      <input
                        {...register(`lines.${index}.description`)}
                        className="input text-sm"
                        placeholder="Description"
                      />
                    </td>
                    <td className="py-2 px-2">
                      <input
                        type="number"
                        step="0.01"
                        {...register(`lines.${index}.quantity`, {
                          valueAsNumber: true,
                        })}
                        className="input text-sm"
                      />
                    </td>
                    <td className="py-2 px-2">
                      <select
                        {...register(`lines.${index}.unit`)}
                        className="input text-sm"
                      >
                        <option value="u">u</option>
                        <option value="h">h</option>
                        <option value="j">j</option>
                        <option value="km">km</option>
                        <option value="forfait">forfait</option>
                      </select>
                    </td>
                    <td className="py-2 px-2">
                      <input
                        type="number"
                        step="0.01"
                        {...register(`lines.${index}.unit_price`, {
                          valueAsNumber: true,
                        })}
                        className="input text-sm"
                      />
                    </td>
                    <td className="py-2 px-2">
                      <select
                        {...register(`lines.${index}.vat_rate`, {
                          valueAsNumber: true,
                        })}
                        className="input text-sm"
                      >
                        <option value={21}>21%</option>
                        <option value={12}>12%</option>
                        <option value={6}>6%</option>
                        <option value={0}>0%</option>
                      </select>
                    </td>
                    <td className="py-2 px-2 font-medium">
                      {calculateLineTotal(lines[index] || field).toFixed(2)} €
                    </td>
                    <td className="py-2 px-2">
                      {fields.length > 1 && (
                        <button
                          type="button"
                          onClick={() => remove(index)}
                          className="text-red-600 hover:text-red-800"
                        >
                          <TrashIcon className="h-5 w-5" />
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Totals */}
          <div className="mt-6 flex justify-end">
            <div className="w-64 space-y-2">
              <div className="flex justify-between">
                <span className="text-gray-600">Total HTVA:</span>
                <span className="font-medium">{totals.htva.toFixed(2)} €</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">TVA:</span>
                <span className="font-medium">{totals.vat.toFixed(2)} €</span>
              </div>
              <div className="flex justify-between text-lg font-bold border-t pt-2">
                <span>Total TVAC:</span>
                <span className="text-primary-600">{totals.tvac.toFixed(2)} €</span>
              </div>
            </div>
          </div>
        </div>

        {/* Notes */}
        <div className="card">
          <h2 className="text-lg font-semibold mb-4">Notes</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="label">Notes internes</label>
              <textarea {...register('notes')} className="input" rows={3} />
            </div>
            <div>
              <label className="label">Notes sur la facture</label>
              <textarea {...register('footer_notes')} className="input" rows={3} />
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="flex justify-end gap-4">
          <button
            type="button"
            onClick={() => navigate('/invoices')}
            className="btn-secondary"
          >
            Annuler
          </button>
          <button type="submit" disabled={loading} className="btn-primary">
            {loading ? 'Enregistrement...' : 'Créer la facture'}
          </button>
        </div>
      </form>
    </div>
  )
}
