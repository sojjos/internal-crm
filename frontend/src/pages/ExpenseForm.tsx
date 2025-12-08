import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { expensesApi, collaboratorsApi, suppliersApi } from '../services/api'
import toast from 'react-hot-toast'

interface ExpenseFormData {
  collaborator_id: number
  expense_date: string
  expense_type_id: number
  description: string
  amount_htva: number
  vat_amount: number
  amount_tvac: number
  supplier_id: number | null
  payroll_period: string
  notes: string
}

interface ExpenseType {
  id: number
  name: string
}

interface Collaborator {
  id: number
  first_name: string
  last_name: string
}

interface Supplier {
  id: number
  name: string
}

export default function ExpenseForm() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [expenseTypes, setExpenseTypes] = useState<ExpenseType[]>([])
  const [collaborators, setCollaborators] = useState<Collaborator[]>([])
  const [suppliers, setSuppliers] = useState<Supplier[]>([])
  const isEdit = Boolean(id)

  const today = new Date().toISOString().split('T')[0]
  const currentPeriod = `${new Date().getFullYear()}-${String(
    new Date().getMonth() + 1
  ).padStart(2, '0')}`

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    reset,
    formState: { errors },
  } = useForm<ExpenseFormData>({
    defaultValues: {
      expense_date: today,
      payroll_period: currentPeriod,
      amount_htva: 0,
      vat_amount: 0,
      amount_tvac: 0,
    },
  })

  const amountHtva = watch('amount_htva')
  const vatAmount = watch('vat_amount')

  useEffect(() => {
    loadData()
    if (isEdit) {
      loadExpense()
    }
  }, [id])

  useEffect(() => {
    // Auto-calculate TVAC
    const htva = amountHtva || 0
    const vat = vatAmount || 0
    setValue('amount_tvac', htva + vat)
  }, [amountHtva, vatAmount])

  const loadData = async () => {
    try {
      const [typesRes, collabRes, suppRes] = await Promise.all([
        expensesApi.types.list({ is_active: true }),
        collaboratorsApi.list({ is_active: true }),
        suppliersApi.list({ is_active: true }),
      ])
      setExpenseTypes(typesRes.data)
      setCollaborators(collabRes.data)
      setSuppliers(suppRes.data)
    } catch (error) {
      toast.error('Erreur lors du chargement des données')
    }
  }

  const loadExpense = async () => {
    try {
      const response = await expensesApi.get(Number(id))
      reset(response.data)
    } catch (error) {
      toast.error('Erreur lors du chargement de la note de frais')
      navigate('/expenses')
    }
  }

  const onSubmit = async (data: ExpenseFormData) => {
    setLoading(true)
    try {
      if (isEdit) {
        await expensesApi.update(Number(id), data)
        toast.success('Note de frais mise à jour')
      } else {
        await expensesApi.create(data)
        toast.success('Note de frais créée')
      }
      navigate('/expenses')
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Erreur lors de la sauvegarde')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <h1 className="page-title">
        {isEdit ? 'Modifier la note de frais' : 'Nouvelle note de frais'}
      </h1>

      <form onSubmit={handleSubmit(onSubmit)} className="card max-w-3xl">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="label">Collaborateur *</label>
            <select
              {...register('collaborator_id', {
                required: 'Ce champ est requis',
                valueAsNumber: true,
              })}
              className="input"
            >
              <option value="">-- Sélectionner --</option>
              {collaborators.map((collab) => (
                <option key={collab.id} value={collab.id}>
                  {collab.first_name} {collab.last_name}
                </option>
              ))}
            </select>
            {errors.collaborator_id && (
              <p className="text-red-500 text-sm mt-1">
                {errors.collaborator_id.message}
              </p>
            )}
          </div>

          <div>
            <label className="label">Date *</label>
            <input
              type="date"
              {...register('expense_date', { required: 'Ce champ est requis' })}
              className="input"
            />
            {errors.expense_date && (
              <p className="text-red-500 text-sm mt-1">
                {errors.expense_date.message}
              </p>
            )}
          </div>

          <div>
            <label className="label">Type de frais *</label>
            <select
              {...register('expense_type_id', {
                required: 'Ce champ est requis',
                valueAsNumber: true,
              })}
              className="input"
            >
              <option value="">-- Sélectionner --</option>
              {expenseTypes.map((type) => (
                <option key={type.id} value={type.id}>
                  {type.name}
                </option>
              ))}
            </select>
            {errors.expense_type_id && (
              <p className="text-red-500 text-sm mt-1">
                {errors.expense_type_id.message}
              </p>
            )}
          </div>

          <div>
            <label className="label">Période de paie</label>
            <input
              {...register('payroll_period')}
              className="input"
              placeholder="2025-03"
            />
          </div>

          <div className="md:col-span-2">
            <label className="label">Description</label>
            <textarea {...register('description')} className="input" rows={2} />
          </div>

          <div>
            <label className="label">Montant HTVA *</label>
            <input
              type="number"
              step="0.01"
              {...register('amount_htva', {
                required: 'Ce champ est requis',
                valueAsNumber: true,
              })}
              className="input"
            />
            {errors.amount_htva && (
              <p className="text-red-500 text-sm mt-1">
                {errors.amount_htva.message}
              </p>
            )}
          </div>

          <div>
            <label className="label">Montant TVA</label>
            <input
              type="number"
              step="0.01"
              {...register('vat_amount', { valueAsNumber: true })}
              className="input"
            />
          </div>

          <div>
            <label className="label">Montant TVAC</label>
            <input
              type="number"
              step="0.01"
              {...register('amount_tvac', { valueAsNumber: true })}
              className="input bg-gray-100"
              readOnly
            />
          </div>

          <div>
            <label className="label">Fournisseur</label>
            <select
              {...register('supplier_id', { valueAsNumber: true })}
              className="input"
            >
              <option value="">-- Aucun --</option>
              {suppliers.map((supplier) => (
                <option key={supplier.id} value={supplier.id}>
                  {supplier.name}
                </option>
              ))}
            </select>
          </div>

          <div className="md:col-span-2">
            <label className="label">Notes internes</label>
            <textarea {...register('notes')} className="input" rows={2} />
          </div>
        </div>

        <div className="flex justify-end gap-4 mt-6 pt-6 border-t">
          <button
            type="button"
            onClick={() => navigate('/expenses')}
            className="btn-secondary"
          >
            Annuler
          </button>
          <button type="submit" disabled={loading} className="btn-primary">
            {loading ? 'Enregistrement...' : 'Enregistrer'}
          </button>
        </div>
      </form>
    </div>
  )
}
