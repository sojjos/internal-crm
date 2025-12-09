import { useEffect, useState } from 'react'
import { annualAccountsApi } from '../services/api'
import {
  PlusIcon,
  DocumentTextIcon,
  CheckCircleIcon,
  ArrowDownTrayIcon,
  CalendarIcon,
} from '@heroicons/react/24/outline'
import toast from 'react-hot-toast'

interface FiscalYear {
  id: number
  name: string
  start_date: string
  end_date: string
  is_closed: boolean
  schema_type: string
}

interface AnnualAccount {
  id: number
  reference: string
  fiscal_year_id: number
  status: string
  schema_type: string
  bnb_enterprise_number: string | null
  bnb_filing_date: string | null
  general_assembly_date: string | null
  created_at: string
}

const statusMap: Record<string, { label: string; color: string }> = {
  DRAFT: { label: 'Brouillon', color: 'bg-gray-100 text-gray-800' },
  IN_PROGRESS: { label: 'En cours', color: 'bg-yellow-100 text-yellow-800' },
  VALIDATED: { label: 'Valide', color: 'bg-green-100 text-green-800' },
  SUBMITTED: { label: 'Depose', color: 'bg-blue-100 text-blue-800' },
  ACCEPTED: { label: 'Accepte', color: 'bg-purple-100 text-purple-800' },
  REJECTED: { label: 'Rejete', color: 'bg-red-100 text-red-800' },
}

const schemaMap: Record<string, string> = {
  COMPLETE: 'Schema complet',
  ABBREVIATED: 'Schema abrege',
  MICRO: 'Micro-schema',
}

export default function AnnualAccounts() {
  const [fiscalYears, setFiscalYears] = useState<FiscalYear[]>([])
  const [accounts, setAccounts] = useState<AnnualAccount[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedYear, setSelectedYear] = useState<number | null>(null)
  const [showNewYearModal, setShowNewYearModal] = useState(false)
  const [showNewAccountModal, setShowNewAccountModal] = useState(false)

  // New year form
  const [newYear, setNewYear] = useState({
    name: new Date().getFullYear().toString(),
    start_date: `${new Date().getFullYear()}-01-01`,
    end_date: `${new Date().getFullYear()}-12-31`,
    schema_type: 'ABBREVIATED',
  })

  // New account form
  const [newAccount, setNewAccount] = useState({
    fiscal_year_id: 0,
    schema_type: 'ABBREVIATED',
    bnb_enterprise_number: '',
  })

  useEffect(() => {
    loadFiscalYears()
  }, [])

  useEffect(() => {
    if (selectedYear) {
      loadAccounts()
    }
  }, [selectedYear])

  const loadFiscalYears = async () => {
    try {
      const response = await annualAccountsApi.fiscalYears.list()
      setFiscalYears(response.data)
      if (response.data.length > 0 && !selectedYear) {
        setSelectedYear(response.data[0].id)
      }
    } catch (error) {
      toast.error('Erreur lors du chargement')
    } finally {
      setLoading(false)
    }
  }

  const loadAccounts = async () => {
    try {
      const response = await annualAccountsApi.list({ fiscal_year_id: selectedYear })
      setAccounts(response.data)
    } catch (error) {
      console.error('Error loading accounts:', error)
    }
  }

  const handleCreateYear = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await annualAccountsApi.fiscalYears.create(newYear)
      toast.success('Exercice cree')
      setShowNewYearModal(false)
      loadFiscalYears()
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Erreur')
    }
  }

  const handleCreateAccount = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await annualAccountsApi.create({
        ...newAccount,
        fiscal_year_id: selectedYear,
      })
      toast.success('Comptes annuels crees')
      setShowNewAccountModal(false)
      loadAccounts()
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Erreur')
    }
  }

  const handleValidate = async (id: number) => {
    try {
      const response = await annualAccountsApi.validate(id)
      if (response.data.valid) {
        toast.success('Comptes valides')
      } else {
        toast.error(response.data.errors.join(', '))
      }
      loadAccounts()
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Erreur')
    }
  }

  const handleGenerateXbrl = async (id: number) => {
    try {
      const response = await annualAccountsApi.generateXbrl(id)
      const blob = new Blob([response.data], { type: 'application/xml' })
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `comptes_annuels_${id}.xbrl`
      a.click()
      toast.success('XBRL genere')
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Erreur')
    }
  }

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('fr-BE')
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
        <h1 className="page-title mb-0">Comptes Annuels & BNB</h1>
        <div className="flex gap-2">
          <button
            onClick={() => setShowNewYearModal(true)}
            className="btn-secondary flex items-center"
          >
            <CalendarIcon className="h-5 w-5 mr-1" />
            Nouvel exercice
          </button>
          <button
            onClick={() => setShowNewAccountModal(true)}
            className="btn-primary flex items-center"
            disabled={!selectedYear}
          >
            <PlusIcon className="h-5 w-5 mr-1" />
            Nouveaux comptes
          </button>
        </div>
      </div>

      {/* Fiscal Year Selection */}
      <div className="card mb-6">
        <div className="flex items-center gap-4">
          <label className="label mb-0">Exercice comptable:</label>
          <select
            value={selectedYear || ''}
            onChange={(e) => setSelectedYear(parseInt(e.target.value))}
            className="input w-auto"
          >
            {fiscalYears.map((year) => (
              <option key={year.id} value={year.id}>
                {year.name} ({formatDate(year.start_date)} - {formatDate(year.end_date)})
                {year.is_closed ? ' [Cloture]' : ''}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Accounts List */}
      <div className="card">
        <h2 className="text-lg font-semibold mb-4">Comptes annuels</h2>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead>
              <tr>
                <th className="table-header px-6 py-3">Reference</th>
                <th className="table-header px-6 py-3">Schema</th>
                <th className="table-header px-6 py-3">N Entreprise</th>
                <th className="table-header px-6 py-3">Statut</th>
                <th className="table-header px-6 py-3">Date AG</th>
                <th className="table-header px-6 py-3">Date depot</th>
                <th className="table-header px-6 py-3">Actions</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {accounts.map((account) => (
                <tr key={account.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap font-mono">
                    {account.reference}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {schemaMap[account.schema_type] || account.schema_type}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {account.bnb_enterprise_number || '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                      statusMap[account.status]?.color || 'bg-gray-100'
                    }`}>
                      {statusMap[account.status]?.label || account.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {account.general_assembly_date
                      ? formatDate(account.general_assembly_date)
                      : '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {account.bnb_filing_date
                      ? formatDate(account.bnb_filing_date)
                      : '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => handleValidate(account.id)}
                        className="text-green-600 hover:text-green-800"
                        title="Valider"
                      >
                        <CheckCircleIcon className="h-5 w-5" />
                      </button>
                      {account.status === 'VALIDATED' && (
                        <button
                          onClick={() => handleGenerateXbrl(account.id)}
                          className="text-blue-600 hover:text-blue-800"
                          title="Generer XBRL"
                        >
                          <ArrowDownTrayIcon className="h-5 w-5" />
                        </button>
                      )}
                      <button
                        className="text-primary-600 hover:text-primary-800"
                        title="Voir details"
                      >
                        <DocumentTextIcon className="h-5 w-5" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {accounts.length === 0 && (
            <p className="text-center py-8 text-gray-500">
              Aucun compte annuel pour cet exercice
            </p>
          )}
        </div>
      </div>

      {/* New Year Modal */}
      {showNewYearModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h2 className="text-lg font-semibold mb-4">Nouvel exercice comptable</h2>
            <form onSubmit={handleCreateYear}>
              <div className="space-y-4">
                <div>
                  <label className="label">Nom</label>
                  <input
                    type="text"
                    value={newYear.name}
                    onChange={(e) => setNewYear({ ...newYear, name: e.target.value })}
                    className="input"
                    required
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="label">Date debut</label>
                    <input
                      type="date"
                      value={newYear.start_date}
                      onChange={(e) => setNewYear({ ...newYear, start_date: e.target.value })}
                      className="input"
                      required
                    />
                  </div>
                  <div>
                    <label className="label">Date fin</label>
                    <input
                      type="date"
                      value={newYear.end_date}
                      onChange={(e) => setNewYear({ ...newYear, end_date: e.target.value })}
                      className="input"
                      required
                    />
                  </div>
                </div>
                <div>
                  <label className="label">Schema</label>
                  <select
                    value={newYear.schema_type}
                    onChange={(e) => setNewYear({ ...newYear, schema_type: e.target.value })}
                    className="input"
                  >
                    <option value="ABBREVIATED">Schema abrege</option>
                    <option value="COMPLETE">Schema complet</option>
                    <option value="MICRO">Micro-schema</option>
                  </select>
                </div>
              </div>
              <div className="flex justify-end gap-2 mt-6">
                <button
                  type="button"
                  onClick={() => setShowNewYearModal(false)}
                  className="btn-secondary"
                >
                  Annuler
                </button>
                <button type="submit" className="btn-primary">
                  Creer
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* New Account Modal */}
      {showNewAccountModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h2 className="text-lg font-semibold mb-4">Nouveaux comptes annuels</h2>
            <form onSubmit={handleCreateAccount}>
              <div className="space-y-4">
                <div>
                  <label className="label">Schema</label>
                  <select
                    value={newAccount.schema_type}
                    onChange={(e) => setNewAccount({ ...newAccount, schema_type: e.target.value })}
                    className="input"
                  >
                    <option value="ABBREVIATED">Schema abrege</option>
                    <option value="COMPLETE">Schema complet</option>
                    <option value="MICRO">Micro-schema</option>
                  </select>
                </div>
                <div>
                  <label className="label">Numero d'entreprise (BCE)</label>
                  <input
                    type="text"
                    value={newAccount.bnb_enterprise_number}
                    onChange={(e) => setNewAccount({ ...newAccount, bnb_enterprise_number: e.target.value })}
                    className="input"
                    placeholder="0XXX.XXX.XXX"
                  />
                </div>
              </div>
              <div className="flex justify-end gap-2 mt-6">
                <button
                  type="button"
                  onClick={() => setShowNewAccountModal(false)}
                  className="btn-secondary"
                >
                  Annuler
                </button>
                <button type="submit" className="btn-primary">
                  Creer
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
