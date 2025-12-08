import { useEffect, useState } from 'react'
import { payrollApi } from '../services/api'
import { ArrowDownTrayIcon } from '@heroicons/react/24/outline'
import toast from 'react-hot-toast'

interface PayrollSummary {
  collaborator_id: number
  collaborator_name: string
  contract_type: string
  gross_salary: number | null
  total_expenses: number
  bonus: number
  total_to_pay: number
}

const contractLabels: Record<string, string> = {
  cdi: 'CDI',
  cdd: 'CDD',
  freelance: 'Freelance',
  intern: 'Stagiaire',
  manager: 'Gérant',
}

export default function Payroll() {
  const [summaries, setSummaries] = useState<PayrollSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedPeriod, setSelectedPeriod] = useState('')
  const [exporting, setExporting] = useState(false)

  useEffect(() => {
    // Set current period as default
    const now = new Date()
    const currentPeriod = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(
      2,
      '0'
    )}`
    setSelectedPeriod(currentPeriod)
  }, [])

  useEffect(() => {
    if (selectedPeriod) {
      loadSummary()
    }
  }, [selectedPeriod])

  const loadSummary = async () => {
    setLoading(true)
    try {
      const response = await payrollApi.summary(selectedPeriod)
      setSummaries(response.data)
    } catch (error) {
      toast.error('Erreur lors du chargement')
    } finally {
      setLoading(false)
    }
  }

  const handleExport = async () => {
    setExporting(true)
    try {
      const response = await payrollApi.export(selectedPeriod)
      const blob = new Blob([response.data], {
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      })
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `payroll_${selectedPeriod}.xlsx`
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

  const formatCurrency = (amount: number | null) => {
    if (amount === null) return '-'
    return new Intl.NumberFormat('fr-BE', {
      style: 'currency',
      currency: 'EUR',
    }).format(amount)
  }

  // Generate period options (last 12 months)
  const getPeriodOptions = () => {
    const options = []
    const now = new Date()
    for (let i = 0; i < 12; i++) {
      const d = new Date(now.getFullYear(), now.getMonth() - i, 1)
      const period = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
      const label = d.toLocaleDateString('fr-BE', { year: 'numeric', month: 'long' })
      options.push({ value: period, label })
    }
    return options
  }

  const totalExpenses = summaries.reduce((sum, s) => sum + s.total_expenses, 0)

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="page-title mb-0">Paie</h1>
        <button
          onClick={handleExport}
          disabled={exporting || summaries.length === 0}
          className="btn-primary flex items-center"
        >
          <ArrowDownTrayIcon className="h-5 w-5 mr-1" />
          {exporting ? 'Export...' : 'Exporter Excel'}
        </button>
      </div>

      <div className="card mb-6">
        <div className="flex items-center gap-4">
          <label className="font-medium">Période:</label>
          <select
            value={selectedPeriod}
            onChange={(e) => setSelectedPeriod(e.target.value)}
            className="input max-w-xs"
          >
            {getPeriodOptions().map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
        </div>
      ) : (
        <div className="card">
          <h2 className="text-lg font-semibold mb-4">
            Récapitulatif de la période {selectedPeriod}
          </h2>

          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead>
                <tr>
                  <th className="table-header px-6 py-3">Collaborateur</th>
                  <th className="table-header px-6 py-3">Contrat</th>
                  <th className="table-header px-6 py-3">Salaire brut (info)</th>
                  <th className="table-header px-6 py-3">Frais validés</th>
                  <th className="table-header px-6 py-3">Primes</th>
                  <th className="table-header px-6 py-3">Total à verser</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {summaries.map((summary) => (
                  <tr key={summary.collaborator_id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap font-medium">
                      {summary.collaborator_name}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-gray-500">
                      {contractLabels[summary.contract_type] || summary.contract_type}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-gray-500">
                      {formatCurrency(summary.gross_salary)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {formatCurrency(summary.total_expenses)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {formatCurrency(summary.bonus)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap font-semibold text-primary-600">
                      {formatCurrency(summary.total_to_pay)}
                    </td>
                  </tr>
                ))}
              </tbody>
              <tfoot>
                <tr className="bg-gray-50">
                  <td
                    colSpan={3}
                    className="px-6 py-4 text-right font-semibold"
                  >
                    Total frais à rembourser:
                  </td>
                  <td
                    colSpan={3}
                    className="px-6 py-4 font-bold text-primary-600"
                  >
                    {formatCurrency(totalExpenses)}
                  </td>
                </tr>
              </tfoot>
            </table>

            {summaries.length === 0 && (
              <p className="text-center py-8 text-gray-500">
                Aucune donnée pour cette période
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
