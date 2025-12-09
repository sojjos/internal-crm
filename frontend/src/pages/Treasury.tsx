import { useEffect, useState } from 'react'
import { treasuryApi } from '../services/api'
import {
  PlusIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  BanknotesIcon,
  ArrowPathIcon,
} from '@heroicons/react/24/outline'
import toast from 'react-hot-toast'

interface BankAccount {
  id: number
  name: string
  bank_name: string | null
  account_number: string | null
  iban: string | null
  current_balance: number
  is_main: boolean
  is_active: boolean
}

interface Transaction {
  id: number
  transaction_date: string
  value_date: string | null
  description: string
  transaction_type: string
  category: string
  amount: number
  running_balance: number | null
  status: string
  reference: string | null
}

interface CashFlowForecast {
  month: string
  expected_income: number
  expected_expenses: number
  net_flow: number
  projected_balance: number
}

interface WeeklyForecast {
  week_start: string
  week_end: string
  expected_income: number
  expected_expenses: number
  net_flow: number
  projected_balance: number
}

const transactionCategories: Record<string, string> = {
  VENTE: 'Vente',
  ACHAT: 'Achat',
  SALAIRE: 'Salaire',
  LOYER: 'Loyer',
  IMPOT: 'Impot',
  ABONNEMENT: 'Abonnement',
  REMBOURSEMENT: 'Remboursement',
  AUTRE: 'Autre',
}

export default function Treasury() {
  const [accounts, setAccounts] = useState<BankAccount[]>([])
  const [transactions, setTransactions] = useState<Transaction[]>([])
  const [forecast, setForecast] = useState<CashFlowForecast[]>([])
  const [weeklyForecast, setWeeklyForecast] = useState<WeeklyForecast[]>([])
  const [selectedAccount, setSelectedAccount] = useState<number | null>(null)
  const [loading, setLoading] = useState(true)
  const [showAddAccount, setShowAddAccount] = useState(false)
  const [showAddTransaction, setShowAddTransaction] = useState(false)
  const [viewMode, setViewMode] = useState<'monthly' | 'weekly'>('monthly')

  const [accountForm, setAccountForm] = useState({
    name: '',
    bank_name: '',
    iban: '',
    current_balance: 0,
    is_main: false,
  })

  const [transactionForm, setTransactionForm] = useState({
    transaction_date: new Date().toISOString().split('T')[0],
    description: '',
    transaction_type: 'CREDIT',
    category: 'AUTRE',
    amount: 0,
  })

  useEffect(() => {
    loadAccounts()
  }, [])

  useEffect(() => {
    if (selectedAccount) {
      loadAccountData()
    }
  }, [selectedAccount, viewMode])

  const loadAccounts = async () => {
    try {
      const response = await treasuryApi.accounts.list()
      setAccounts(response.data)
      if (response.data.length > 0 && !selectedAccount) {
        setSelectedAccount(response.data[0].id)
      }
    } catch (error) {
      toast.error('Erreur lors du chargement des comptes')
    } finally {
      setLoading(false)
    }
  }

  const loadAccountData = async () => {
    if (!selectedAccount) return

    try {
      const [transRes, forecastRes] = await Promise.all([
        treasuryApi.transactions.list({ account_id: selectedAccount }),
        viewMode === 'monthly'
          ? treasuryApi.forecast(selectedAccount, 6)
          : treasuryApi.weeklyForecast(selectedAccount, 8),
      ])

      setTransactions(transRes.data)
      if (viewMode === 'monthly') {
        setForecast(forecastRes.data)
      } else {
        setWeeklyForecast(forecastRes.data)
      }
    } catch (error) {
      toast.error('Erreur lors du chargement')
    }
  }

  const handleAddAccount = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await treasuryApi.accounts.create(accountForm)
      toast.success('Compte ajoute')
      setShowAddAccount(false)
      setAccountForm({ name: '', bank_name: '', iban: '', current_balance: 0, is_main: false })
      loadAccounts()
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Erreur')
    }
  }

  const handleAddTransaction = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedAccount) return

    try {
      await treasuryApi.transactions.create({
        ...transactionForm,
        account_id: selectedAccount,
      })
      toast.success('Transaction ajoutee')
      setShowAddTransaction(false)
      setTransactionForm({
        transaction_date: new Date().toISOString().split('T')[0],
        description: '',
        transaction_type: 'CREDIT',
        category: 'AUTRE',
        amount: 0,
      })
      loadAccountData()
      loadAccounts()
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Erreur')
    }
  }

  const handleSyncInvoices = async () => {
    if (!selectedAccount) return

    try {
      const response = await treasuryApi.syncFromInvoices(selectedAccount)
      toast.success(`${response.data.synced_count} transactions synchronisees`)
      loadAccountData()
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
    return new Date(dateStr).toLocaleDateString('fr-BE')
  }

  const getSelectedAccount = () => accounts.find(a => a.id === selectedAccount)
  const totalBalance = accounts.reduce((sum, a) => sum + a.current_balance, 0)

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
        <h1 className="page-title mb-0">Tresorerie & Cashflow</h1>
        <div className="flex gap-2">
          <button
            onClick={() => setShowAddAccount(true)}
            className="btn-secondary flex items-center"
          >
            <PlusIcon className="h-5 w-5 mr-1" />
            Compte
          </button>
          {selectedAccount && (
            <>
              <button
                onClick={handleSyncInvoices}
                className="btn-secondary flex items-center"
                title="Synchroniser depuis les factures"
              >
                <ArrowPathIcon className="h-5 w-5 mr-1" />
                Sync factures
              </button>
              <button
                onClick={() => setShowAddTransaction(true)}
                className="btn-primary flex items-center"
              >
                <PlusIcon className="h-5 w-5 mr-1" />
                Transaction
              </button>
            </>
          )}
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="card bg-blue-50">
          <p className="text-sm text-gray-600">Solde total</p>
          <p className="text-2xl font-bold text-blue-600">
            {formatCurrency(totalBalance)}
          </p>
        </div>
        {getSelectedAccount() && (
          <>
            <div className="card bg-green-50">
              <p className="text-sm text-gray-600">{getSelectedAccount()?.name}</p>
              <p className="text-2xl font-bold text-green-600">
                {formatCurrency(getSelectedAccount()?.current_balance || 0)}
              </p>
            </div>
            <div className="card bg-purple-50">
              <p className="text-sm text-gray-600">Entrees (30j)</p>
              <p className="text-2xl font-bold text-purple-600">
                {formatCurrency(
                  transactions
                    .filter(t => t.transaction_type === 'CREDIT')
                    .reduce((sum, t) => sum + t.amount, 0)
                )}
              </p>
            </div>
            <div className="card bg-orange-50">
              <p className="text-sm text-gray-600">Sorties (30j)</p>
              <p className="text-2xl font-bold text-orange-600">
                {formatCurrency(
                  transactions
                    .filter(t => t.transaction_type === 'DEBIT')
                    .reduce((sum, t) => sum + t.amount, 0)
                )}
              </p>
            </div>
          </>
        )}
      </div>

      {/* Account selector */}
      {accounts.length > 0 && (
        <div className="card mb-6">
          <div className="flex items-center gap-4">
            <div className="flex-1">
              <label className="label">Compte bancaire</label>
              <select
                value={selectedAccount || ''}
                onChange={(e) => setSelectedAccount(Number(e.target.value))}
                className="input"
              >
                {accounts.map((account) => (
                  <option key={account.id} value={account.id}>
                    {account.name} ({account.bank_name}) - {formatCurrency(account.current_balance)}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="label">Vue</label>
              <div className="flex gap-2">
                <button
                  onClick={() => setViewMode('monthly')}
                  className={`px-4 py-2 rounded ${viewMode === 'monthly' ? 'bg-primary-600 text-white' : 'bg-gray-100'}`}
                >
                  Mensuelle
                </button>
                <button
                  onClick={() => setViewMode('weekly')}
                  className={`px-4 py-2 rounded ${viewMode === 'weekly' ? 'bg-primary-600 text-white' : 'bg-gray-100'}`}
                >
                  Hebdomadaire
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Forecast */}
      {selectedAccount && (
        <div className="card mb-6">
          <h2 className="text-lg font-semibold mb-4">
            Prevision de tresorerie ({viewMode === 'monthly' ? '6 mois' : '8 semaines'})
          </h2>
          <div className="overflow-x-auto">
            <table className="min-w-full">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-2">Periode</th>
                  <th className="text-right py-2">Entrees prevues</th>
                  <th className="text-right py-2">Sorties prevues</th>
                  <th className="text-right py-2">Flux net</th>
                  <th className="text-right py-2">Solde projete</th>
                </tr>
              </thead>
              <tbody>
                {viewMode === 'monthly'
                  ? forecast.map((f, i) => (
                      <tr key={i} className="border-b">
                        <td className="py-2 font-medium">{f.month}</td>
                        <td className="text-right text-green-600">{formatCurrency(f.expected_income)}</td>
                        <td className="text-right text-red-600">{formatCurrency(f.expected_expenses)}</td>
                        <td className={`text-right font-medium ${f.net_flow >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                          {formatCurrency(f.net_flow)}
                        </td>
                        <td className={`text-right font-bold ${f.projected_balance >= 0 ? '' : 'text-red-600'}`}>
                          {formatCurrency(f.projected_balance)}
                        </td>
                      </tr>
                    ))
                  : weeklyForecast.map((f, i) => (
                      <tr key={i} className="border-b">
                        <td className="py-2 font-medium">
                          {formatDate(f.week_start)} - {formatDate(f.week_end)}
                        </td>
                        <td className="text-right text-green-600">{formatCurrency(f.expected_income)}</td>
                        <td className="text-right text-red-600">{formatCurrency(f.expected_expenses)}</td>
                        <td className={`text-right font-medium ${f.net_flow >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                          {formatCurrency(f.net_flow)}
                        </td>
                        <td className={`text-right font-bold ${f.projected_balance >= 0 ? '' : 'text-red-600'}`}>
                          {formatCurrency(f.projected_balance)}
                        </td>
                      </tr>
                    ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Transactions */}
      {selectedAccount && (
        <div className="card">
          <h2 className="text-lg font-semibold mb-4">Dernieres transactions</h2>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead>
                <tr>
                  <th className="table-header px-6 py-3">Date</th>
                  <th className="table-header px-6 py-3">Description</th>
                  <th className="table-header px-6 py-3">Categorie</th>
                  <th className="table-header px-6 py-3 text-right">Montant</th>
                  <th className="table-header px-6 py-3 text-right">Solde</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {transactions.slice(0, 20).map((t) => (
                  <tr key={t.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      {formatDate(t.transaction_date)}
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center">
                        {t.transaction_type === 'CREDIT' ? (
                          <ArrowTrendingUpIcon className="h-4 w-4 text-green-500 mr-2" />
                        ) : (
                          <ArrowTrendingDownIcon className="h-4 w-4 text-red-500 mr-2" />
                        )}
                        {t.description}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="px-2 py-1 text-xs rounded-full bg-gray-100">
                        {transactionCategories[t.category] || t.category}
                      </span>
                    </td>
                    <td className={`px-6 py-4 whitespace-nowrap text-right font-medium ${
                      t.transaction_type === 'CREDIT' ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {t.transaction_type === 'CREDIT' ? '+' : '-'}{formatCurrency(t.amount)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right">
                      {t.running_balance !== null ? formatCurrency(t.running_balance) : '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {transactions.length === 0 && (
              <p className="text-center py-8 text-gray-500">
                Aucune transaction
              </p>
            )}
          </div>
        </div>
      )}

      {/* Add Account Modal */}
      {showAddAccount && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h2 className="text-lg font-semibold mb-4">Ajouter un compte bancaire</h2>
            <form onSubmit={handleAddAccount} className="space-y-4">
              <div>
                <label className="label">Nom du compte *</label>
                <input
                  type="text"
                  value={accountForm.name}
                  onChange={(e) => setAccountForm({ ...accountForm, name: e.target.value })}
                  className="input"
                  required
                />
              </div>
              <div>
                <label className="label">Banque</label>
                <input
                  type="text"
                  value={accountForm.bank_name}
                  onChange={(e) => setAccountForm({ ...accountForm, bank_name: e.target.value })}
                  className="input"
                />
              </div>
              <div>
                <label className="label">IBAN</label>
                <input
                  type="text"
                  value={accountForm.iban}
                  onChange={(e) => setAccountForm({ ...accountForm, iban: e.target.value })}
                  className="input"
                />
              </div>
              <div>
                <label className="label">Solde initial</label>
                <input
                  type="number"
                  step="0.01"
                  value={accountForm.current_balance}
                  onChange={(e) => setAccountForm({ ...accountForm, current_balance: parseFloat(e.target.value) })}
                  className="input"
                />
              </div>
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="is_main"
                  checked={accountForm.is_main}
                  onChange={(e) => setAccountForm({ ...accountForm, is_main: e.target.checked })}
                  className="rounded border-gray-300"
                />
                <label htmlFor="is_main" className="text-sm">Compte principal</label>
              </div>
              <div className="flex justify-end gap-2 pt-4">
                <button type="button" onClick={() => setShowAddAccount(false)} className="btn-secondary">
                  Annuler
                </button>
                <button type="submit" className="btn-primary">Ajouter</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Add Transaction Modal */}
      {showAddTransaction && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h2 className="text-lg font-semibold mb-4">Ajouter une transaction</h2>
            <form onSubmit={handleAddTransaction} className="space-y-4">
              <div>
                <label className="label">Date *</label>
                <input
                  type="date"
                  value={transactionForm.transaction_date}
                  onChange={(e) => setTransactionForm({ ...transactionForm, transaction_date: e.target.value })}
                  className="input"
                  required
                />
              </div>
              <div>
                <label className="label">Description *</label>
                <input
                  type="text"
                  value={transactionForm.description}
                  onChange={(e) => setTransactionForm({ ...transactionForm, description: e.target.value })}
                  className="input"
                  required
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="label">Type</label>
                  <select
                    value={transactionForm.transaction_type}
                    onChange={(e) => setTransactionForm({ ...transactionForm, transaction_type: e.target.value })}
                    className="input"
                  >
                    <option value="CREDIT">Entree</option>
                    <option value="DEBIT">Sortie</option>
                  </select>
                </div>
                <div>
                  <label className="label">Categorie</label>
                  <select
                    value={transactionForm.category}
                    onChange={(e) => setTransactionForm({ ...transactionForm, category: e.target.value })}
                    className="input"
                  >
                    {Object.entries(transactionCategories).map(([key, label]) => (
                      <option key={key} value={key}>{label}</option>
                    ))}
                  </select>
                </div>
              </div>
              <div>
                <label className="label">Montant *</label>
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  value={transactionForm.amount}
                  onChange={(e) => setTransactionForm({ ...transactionForm, amount: parseFloat(e.target.value) })}
                  className="input"
                  required
                />
              </div>
              <div className="flex justify-end gap-2 pt-4">
                <button type="button" onClick={() => setShowAddTransaction(false)} className="btn-secondary">
                  Annuler
                </button>
                <button type="submit" className="btn-primary">Ajouter</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {accounts.length === 0 && (
        <div className="card text-center py-12">
          <BanknotesIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">Aucun compte bancaire</h3>
          <p className="text-gray-500 mb-4">Commencez par ajouter un compte bancaire</p>
          <button onClick={() => setShowAddAccount(true)} className="btn-primary">
            <PlusIcon className="h-5 w-5 mr-1 inline" />
            Ajouter un compte
          </button>
        </div>
      )}
    </div>
  )
}
