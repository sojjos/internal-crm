import { useEffect, useState } from 'react'
import { reportsApi } from '../services/api'
import { ArrowDownTrayIcon } from '@heroicons/react/24/outline'
import toast from 'react-hot-toast'

interface MonthlySummary {
  year: number
  month: number
  revenue_htva: number
  revenue_tvac: number
  vat_collected: number
  expenses_htva: number
  expenses_tvac: number
  vat_deductible: number
  invoices_count: number
  invoices_paid: number
  invoices_overdue: number
}

interface VATSummary {
  vat_collected: number
  vat_deductible: number
  vat_balance: number
}

export default function Reports() {
  const [monthlySummary, setMonthlySummary] = useState<MonthlySummary[]>([])
  const [vatSummary, setVatSummary] = useState<VATSummary | null>(null)
  const [loading, setLoading] = useState(true)
  const [selectedYear, setSelectedYear] = useState(new Date().getFullYear())
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')
  const [exporting, setExporting] = useState(false)

  useEffect(() => {
    // Set default date range (current quarter)
    const now = new Date()
    const quarterStart = new Date(now.getFullYear(), Math.floor(now.getMonth() / 3) * 3, 1)
    const quarterEnd = new Date(now.getFullYear(), Math.floor(now.getMonth() / 3) * 3 + 3, 0)
    setDateFrom(quarterStart.toISOString().split('T')[0])
    setDateTo(quarterEnd.toISOString().split('T')[0])
  }, [])

  useEffect(() => {
    loadMonthlySummary()
  }, [selectedYear])

  useEffect(() => {
    if (dateFrom && dateTo) {
      loadVatSummary()
    }
  }, [dateFrom, dateTo])

  const loadMonthlySummary = async () => {
    setLoading(true)
    try {
      const response = await reportsApi.monthly(selectedYear)
      setMonthlySummary(response.data)
    } catch (error) {
      toast.error('Erreur lors du chargement')
    } finally {
      setLoading(false)
    }
  }

  const loadVatSummary = async () => {
    try {
      const response = await reportsApi.vat(dateFrom, dateTo)
      setVatSummary(response.data)
    } catch (error) {
      console.error('Failed to load VAT summary', error)
    }
  }

  const handleExport = async (type: 'invoices' | 'expenses' | 'vat') => {
    if (!dateFrom || !dateTo) {
      toast.error('Sélectionnez une période')
      return
    }

    setExporting(true)
    try {
      let response
      let filename

      switch (type) {
        case 'invoices':
          response = await reportsApi.exportInvoices(dateFrom, dateTo)
          filename = `invoices_${dateFrom}_${dateTo}.xlsx`
          break
        case 'expenses':
          response = await reportsApi.exportExpenses(dateFrom, dateTo)
          filename = `expenses_${dateFrom}_${dateTo}.xlsx`
          break
        case 'vat':
          response = await reportsApi.exportVat(dateFrom, dateTo)
          filename = `vat_report_${dateFrom}_${dateTo}.xlsx`
          break
      }

      const blob = new Blob([response.data], {
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      })
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
      toast.success('Export téléchargé')
    } catch (error) {
      toast.error("Erreur lors de l'export")
    } finally {
      setExporting(false)
    }
  }

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('fr-BE', {
      style: 'currency',
      currency: 'EUR',
    }).format(amount)
  }

  const monthNames = [
    'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
    'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre'
  ]

  // Calculate yearly totals
  const yearlyTotals = monthlySummary.reduce(
    (acc, month) => ({
      revenue: acc.revenue + month.revenue_tvac,
      expenses: acc.expenses + month.expenses_tvac,
      vatCollected: acc.vatCollected + month.vat_collected,
      vatDeductible: acc.vatDeductible + month.vat_deductible,
    }),
    { revenue: 0, expenses: 0, vatCollected: 0, vatDeductible: 0 }
  )

  return (
    <div>
      <h1 className="page-title">Rapports & Exports</h1>

      {/* Exports section */}
      <div className="card mb-6">
        <h2 className="text-lg font-semibold mb-4">Exports comptables</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          <div>
            <label className="label">Date de début</label>
            <input
              type="date"
              value={dateFrom}
              onChange={(e) => setDateFrom(e.target.value)}
              className="input"
            />
          </div>
          <div>
            <label className="label">Date de fin</label>
            <input
              type="date"
              value={dateTo}
              onChange={(e) => setDateTo(e.target.value)}
              className="input"
            />
          </div>
        </div>
        <div className="flex flex-wrap gap-3">
          <button
            onClick={() => handleExport('invoices')}
            disabled={exporting}
            className="btn-secondary flex items-center"
          >
            <ArrowDownTrayIcon className="h-5 w-5 mr-1" />
            Export Ventes
          </button>
          <button
            onClick={() => handleExport('expenses')}
            disabled={exporting}
            className="btn-secondary flex items-center"
          >
            <ArrowDownTrayIcon className="h-5 w-5 mr-1" />
            Export Achats/Frais
          </button>
          <button
            onClick={() => handleExport('vat')}
            disabled={exporting}
            className="btn-secondary flex items-center"
          >
            <ArrowDownTrayIcon className="h-5 w-5 mr-1" />
            Export TVA
          </button>
        </div>
      </div>

      {/* VAT Summary */}
      {vatSummary && (
        <div className="card mb-6">
          <h2 className="text-lg font-semibold mb-4">Résumé TVA (période sélectionnée)</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-green-50 p-4 rounded-lg">
              <p className="text-sm text-green-600">TVA Collectée (ventes)</p>
              <p className="text-2xl font-bold text-green-700">
                {formatCurrency(vatSummary.vat_collected)}
              </p>
            </div>
            <div className="bg-red-50 p-4 rounded-lg">
              <p className="text-sm text-red-600">TVA Déductible (achats)</p>
              <p className="text-2xl font-bold text-red-700">
                {formatCurrency(vatSummary.vat_deductible)}
              </p>
            </div>
            <div className={`p-4 rounded-lg ${vatSummary.vat_balance >= 0 ? 'bg-blue-50' : 'bg-orange-50'}`}>
              <p className={`text-sm ${vatSummary.vat_balance >= 0 ? 'text-blue-600' : 'text-orange-600'}`}>
                {vatSummary.vat_balance >= 0 ? 'TVA à payer' : 'TVA à récupérer'}
              </p>
              <p className={`text-2xl font-bold ${vatSummary.vat_balance >= 0 ? 'text-blue-700' : 'text-orange-700'}`}>
                {formatCurrency(Math.abs(vatSummary.vat_balance))}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Monthly summary */}
      <div className="card">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg font-semibold">Résumé mensuel</h2>
          <select
            value={selectedYear}
            onChange={(e) => setSelectedYear(Number(e.target.value))}
            className="input w-auto"
          >
            {[0, 1, 2].map((offset) => {
              const year = new Date().getFullYear() - offset
              return (
                <option key={year} value={year}>
                  {year}
                </option>
              )
            })}
          </select>
        </div>

        {loading ? (
          <div className="flex items-center justify-center h-32">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead>
                <tr>
                  <th className="table-header px-4 py-3">Mois</th>
                  <th className="table-header px-4 py-3 text-right">CA TVAC</th>
                  <th className="table-header px-4 py-3 text-right">TVA collectée</th>
                  <th className="table-header px-4 py-3 text-right">Dépenses TVAC</th>
                  <th className="table-header px-4 py-3 text-right">TVA déductible</th>
                  <th className="table-header px-4 py-3 text-right">Factures</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {monthlySummary.map((month) => (
                  <tr key={month.month} className="hover:bg-gray-50">
                    <td className="px-4 py-3 font-medium">
                      {monthNames[month.month - 1]}
                    </td>
                    <td className="px-4 py-3 text-right">
                      {formatCurrency(month.revenue_tvac)}
                    </td>
                    <td className="px-4 py-3 text-right text-green-600">
                      {formatCurrency(month.vat_collected)}
                    </td>
                    <td className="px-4 py-3 text-right">
                      {formatCurrency(month.expenses_tvac)}
                    </td>
                    <td className="px-4 py-3 text-right text-red-600">
                      {formatCurrency(month.vat_deductible)}
                    </td>
                    <td className="px-4 py-3 text-right text-gray-500">
                      {month.invoices_count}
                    </td>
                  </tr>
                ))}
              </tbody>
              <tfoot>
                <tr className="bg-gray-50 font-semibold">
                  <td className="px-4 py-3">Total {selectedYear}</td>
                  <td className="px-4 py-3 text-right">
                    {formatCurrency(yearlyTotals.revenue)}
                  </td>
                  <td className="px-4 py-3 text-right text-green-600">
                    {formatCurrency(yearlyTotals.vatCollected)}
                  </td>
                  <td className="px-4 py-3 text-right">
                    {formatCurrency(yearlyTotals.expenses)}
                  </td>
                  <td className="px-4 py-3 text-right text-red-600">
                    {formatCurrency(yearlyTotals.vatDeductible)}
                  </td>
                  <td></td>
                </tr>
              </tfoot>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
