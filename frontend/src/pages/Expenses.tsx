import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { expensesApi } from '../services/api'
import { PlusIcon, PencilIcon, TrashIcon } from '@heroicons/react/24/outline'
import toast from 'react-hot-toast'

interface Expense {
  id: number
  expense_date: string
  description: string
  amount_tvac: number
  payroll_period: string | null
  is_validated: boolean
  is_reimbursed: boolean
}

export default function Expenses() {
  const [expenses, setExpenses] = useState<Expense[]>([])
  const [loading, setLoading] = useState(true)
  const [periodFilter, setPeriodFilter] = useState('')

  useEffect(() => {
    loadExpenses()
  }, [periodFilter])

  const loadExpenses = async () => {
    try {
      const params: any = {}
      if (periodFilter) params.payroll_period = periodFilter
      const response = await expensesApi.list(params)
      setExpenses(response.data)
    } catch (error) {
      toast.error('Erreur lors du chargement des notes de frais')
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (id: number) => {
    if (!confirm('Êtes-vous sûr de vouloir supprimer cette note de frais ?')) return

    try {
      await expensesApi.delete(id)
      toast.success('Note de frais supprimée')
      loadExpenses()
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Erreur lors de la suppression')
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

  // Generate period options (last 12 months)
  const getPeriodOptions = () => {
    const options = []
    const now = new Date()
    for (let i = 0; i < 12; i++) {
      const d = new Date(now.getFullYear(), now.getMonth() - i, 1)
      const period = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
      options.push(period)
    }
    return options
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
        <h1 className="page-title mb-0">Notes de frais</h1>
        <Link to="/expenses/new" className="btn-primary flex items-center">
          <PlusIcon className="h-5 w-5 mr-1" />
          Nouvelle note de frais
        </Link>
      </div>

      <div className="card">
        <div className="mb-4">
          <select
            value={periodFilter}
            onChange={(e) => setPeriodFilter(e.target.value)}
            className="input max-w-xs"
          >
            <option value="">Toutes les périodes</option>
            {getPeriodOptions().map((period) => (
              <option key={period} value={period}>
                {period}
              </option>
            ))}
          </select>
        </div>

        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead>
              <tr>
                <th className="table-header px-6 py-3">Date</th>
                <th className="table-header px-6 py-3">Description</th>
                <th className="table-header px-6 py-3">Montant TVAC</th>
                <th className="table-header px-6 py-3">Période</th>
                <th className="table-header px-6 py-3">Statut</th>
                <th className="table-header px-6 py-3">Actions</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {expenses.map((expense) => (
                <tr key={expense.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    {formatDate(expense.expense_date)}
                  </td>
                  <td className="px-6 py-4">{expense.description || '-'}</td>
                  <td className="px-6 py-4 whitespace-nowrap font-semibold">
                    {formatCurrency(expense.amount_tvac)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-gray-500">
                    {expense.payroll_period || '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {expense.is_reimbursed ? (
                      <span className="px-2 py-1 text-xs font-medium rounded-full bg-green-100 text-green-800">
                        Remboursé
                      </span>
                    ) : expense.is_validated ? (
                      <span className="px-2 py-1 text-xs font-medium rounded-full bg-blue-100 text-blue-800">
                        Validé
                      </span>
                    ) : (
                      <span className="px-2 py-1 text-xs font-medium rounded-full bg-gray-100 text-gray-800">
                        En attente
                      </span>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <Link
                      to={`/expenses/${expense.id}`}
                      className="text-primary-600 hover:text-primary-800 mr-3"
                    >
                      <PencilIcon className="h-5 w-5 inline" />
                    </Link>
                    {!expense.is_reimbursed && (
                      <button
                        onClick={() => handleDelete(expense.id)}
                        className="text-red-600 hover:text-red-800"
                      >
                        <TrashIcon className="h-5 w-5 inline" />
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {expenses.length === 0 && (
            <p className="text-center py-8 text-gray-500">
              Aucune note de frais trouvée
            </p>
          )}
        </div>
      </div>
    </div>
  )
}
