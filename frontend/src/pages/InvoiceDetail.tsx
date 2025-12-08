import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { invoicesApi } from '../services/api'
import {
  DocumentArrowDownIcon,
  PaperAirplaneIcon,
  CheckCircleIcon,
  XCircleIcon,
} from '@heroicons/react/24/outline'
import toast from 'react-hot-toast'

interface InvoiceLine {
  id: number
  description: string
  unit: string
  quantity: number
  unit_price: number
  vat_rate: number
  line_total_htva: number
  line_total_tvac: number
}

interface Invoice {
  id: number
  invoice_number: string
  client_id: number
  invoice_date: string
  due_date: string
  status: string
  total_htva: number
  total_vat: number
  total_tvac: number
  pdf_path: string | null
  sent_via_email: boolean
  sent_via_peppol: boolean
  lines: InvoiceLine[]
}

const statusLabels: Record<string, string> = {
  draft: 'Brouillon',
  sent: 'Envoyée',
  paid: 'Payée',
  overdue: 'En retard',
  cancelled: 'Annulée',
}

export default function InvoiceDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [invoice, setInvoice] = useState<Invoice | null>(null)
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState(false)

  useEffect(() => {
    loadInvoice()
  }, [id])

  const loadInvoice = async () => {
    try {
      const response = await invoicesApi.get(Number(id))
      setInvoice(response.data)
    } catch (error) {
      toast.error('Erreur lors du chargement de la facture')
      navigate('/invoices')
    } finally {
      setLoading(false)
    }
  }

  const handleGeneratePdf = async () => {
    setActionLoading(true)
    try {
      await invoicesApi.generatePdf(Number(id))
      toast.success('PDF généré')
      loadInvoice()
    } catch (error) {
      toast.error('Erreur lors de la génération du PDF')
    } finally {
      setActionLoading(false)
    }
  }

  const handleSend = async () => {
    if (!confirm('Envoyer cette facture par email ?')) return

    setActionLoading(true)
    try {
      await invoicesApi.send(Number(id), { send_email: true })
      toast.success('Facture envoyée')
      loadInvoice()
    } catch (error) {
      toast.error("Erreur lors de l'envoi")
    } finally {
      setActionLoading(false)
    }
  }

  const handleMarkPaid = async () => {
    if (!confirm('Marquer cette facture comme payée ?')) return

    setActionLoading(true)
    try {
      await invoicesApi.markPaid(Number(id))
      toast.success('Facture marquée comme payée')
      loadInvoice()
    } catch (error) {
      toast.error('Erreur')
    } finally {
      setActionLoading(false)
    }
  }

  const handleCancel = async () => {
    if (!confirm('Annuler cette facture ?')) return

    setActionLoading(true)
    try {
      await invoicesApi.delete(Number(id))
      toast.success('Facture annulée')
      loadInvoice()
    } catch (error) {
      toast.error('Erreur')
    } finally {
      setActionLoading(false)
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

  if (loading || !invoice) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  return (
    <div>
      <div className="flex justify-between items-start mb-6">
        <div>
          <h1 className="page-title mb-2">Facture {invoice.invoice_number}</h1>
          <span
            className={`px-3 py-1 text-sm font-medium rounded-full ${
              invoice.status === 'paid'
                ? 'bg-green-100 text-green-800'
                : invoice.status === 'draft'
                ? 'bg-gray-100 text-gray-800'
                : invoice.status === 'overdue'
                ? 'bg-red-100 text-red-800'
                : 'bg-blue-100 text-blue-800'
            }`}
          >
            {statusLabels[invoice.status]}
          </span>
        </div>

        <div className="flex gap-2">
          {invoice.status === 'draft' && (
            <>
              <button
                onClick={handleGeneratePdf}
                disabled={actionLoading}
                className="btn-secondary flex items-center"
              >
                <DocumentArrowDownIcon className="h-5 w-5 mr-1" />
                Générer PDF
              </button>
              <button
                onClick={handleSend}
                disabled={actionLoading}
                className="btn-primary flex items-center"
              >
                <PaperAirplaneIcon className="h-5 w-5 mr-1" />
                Envoyer
              </button>
            </>
          )}

          {invoice.status === 'sent' && (
            <>
              <button
                onClick={handleMarkPaid}
                disabled={actionLoading}
                className="btn-primary flex items-center"
              >
                <CheckCircleIcon className="h-5 w-5 mr-1" />
                Marquer payée
              </button>
              <button
                onClick={handleCancel}
                disabled={actionLoading}
                className="btn-danger flex items-center"
              >
                <XCircleIcon className="h-5 w-5 mr-1" />
                Annuler
              </button>
            </>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Invoice details */}
        <div className="lg:col-span-2 space-y-6">
          <div className="card">
            <h2 className="text-lg font-semibold mb-4">Lignes de facture</h2>
            <table className="min-w-full">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-2 text-sm font-medium">Description</th>
                  <th className="text-right py-2 text-sm font-medium">Qté</th>
                  <th className="text-right py-2 text-sm font-medium">Prix unit.</th>
                  <th className="text-right py-2 text-sm font-medium">TVA</th>
                  <th className="text-right py-2 text-sm font-medium">Total HTVA</th>
                </tr>
              </thead>
              <tbody>
                {invoice.lines.map((line) => (
                  <tr key={line.id} className="border-b">
                    <td className="py-3">{line.description}</td>
                    <td className="py-3 text-right">
                      {line.quantity} {line.unit}
                    </td>
                    <td className="py-3 text-right">
                      {formatCurrency(line.unit_price)}
                    </td>
                    <td className="py-3 text-right">{line.vat_rate}%</td>
                    <td className="py-3 text-right font-medium">
                      {formatCurrency(line.line_total_htva)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            <div className="mt-6 flex justify-end">
              <div className="w-64 space-y-2">
                <div className="flex justify-between">
                  <span className="text-gray-600">Total HTVA:</span>
                  <span>{formatCurrency(invoice.total_htva)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">TVA:</span>
                  <span>{formatCurrency(invoice.total_vat)}</span>
                </div>
                <div className="flex justify-between text-lg font-bold border-t pt-2">
                  <span>Total TVAC:</span>
                  <span className="text-primary-600">
                    {formatCurrency(invoice.total_tvac)}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          <div className="card">
            <h2 className="text-lg font-semibold mb-4">Informations</h2>
            <dl className="space-y-3">
              <div>
                <dt className="text-sm text-gray-500">Date de facture</dt>
                <dd className="font-medium">{formatDate(invoice.invoice_date)}</dd>
              </div>
              <div>
                <dt className="text-sm text-gray-500">Date d'échéance</dt>
                <dd className="font-medium">{formatDate(invoice.due_date)}</dd>
              </div>
              <div>
                <dt className="text-sm text-gray-500">Envoyée par email</dt>
                <dd className="font-medium">
                  {invoice.sent_via_email ? 'Oui' : 'Non'}
                </dd>
              </div>
              <div>
                <dt className="text-sm text-gray-500">Envoyée via Peppol</dt>
                <dd className="font-medium">
                  {invoice.sent_via_peppol ? 'Oui' : 'Non'}
                </dd>
              </div>
            </dl>
          </div>

          {invoice.pdf_path && (
            <div className="card">
              <h2 className="text-lg font-semibold mb-4">Documents</h2>
              <a
                href={`/uploads/invoices/${invoice.pdf_path.split('/').pop()}`}
                target="_blank"
                rel="noopener noreferrer"
                className="btn-secondary w-full flex items-center justify-center"
              >
                <DocumentArrowDownIcon className="h-5 w-5 mr-1" />
                Télécharger PDF
              </a>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
