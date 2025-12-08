import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { purchasesApi, suppliersApi } from '../services/api'
import toast from 'react-hot-toast'
import { ArrowLeftIcon } from '@heroicons/react/24/outline'

interface Category {
  id: number
  name: string
}

interface Supplier {
  id: number
  name: string
}

interface FormData {
  supplier_id: string
  category_id: string
  contract_type: string
  name: string
  description: string
  reference: string
  start_date: string
  end_date: string
  periodicity: string
  amount_htva: string
  vat_rate: string
  payment_method: string
  billing_day: string
  vehicle_type: string
  vehicle_co2: string
  vehicle_registration: string
  is_active: boolean
}

const initialFormData: FormData = {
  supplier_id: '',
  category_id: '',
  contract_type: 'ABONNEMENT',
  name: '',
  description: '',
  reference: '',
  start_date: new Date().toISOString().split('T')[0],
  end_date: '',
  periodicity: 'MENSUEL',
  amount_htva: '',
  vat_rate: '21',
  payment_method: 'DOMICILIATION',
  billing_day: '1',
  vehicle_type: '',
  vehicle_co2: '',
  vehicle_registration: '',
  is_active: true,
}

const contractTypes = [
  { value: 'ABONNEMENT', label: 'Abonnement' },
  { value: 'LEASING', label: 'Leasing' },
  { value: 'LOCATION', label: 'Location' },
  { value: 'MAINTENANCE', label: 'Maintenance' },
  { value: 'LICENCE', label: 'Licence' },
  { value: 'ASSURANCE', label: 'Assurance' },
  { value: 'AUTRE', label: 'Autre' },
]

const periodicities = [
  { value: 'MENSUEL', label: 'Mensuel' },
  { value: 'TRIMESTRIEL', label: 'Trimestriel' },
  { value: 'SEMESTRIEL', label: 'Semestriel' },
  { value: 'ANNUEL', label: 'Annuel' },
]

const paymentMethods = [
  { value: 'VIREMENT', label: 'Virement' },
  { value: 'CARTE', label: 'Carte bancaire' },
  { value: 'DOMICILIATION', label: 'Domiciliation' },
  { value: 'ESPECES', label: 'Especes' },
  { value: 'CHEQUE', label: 'Cheque' },
]

const vehicleTypes = [
  { value: '', label: 'Non applicable' },
  { value: 'VOITURE', label: 'Voiture' },
  { value: 'UTILITAIRE', label: 'Utilitaire' },
  { value: 'MOTO', label: 'Moto' },
  { value: 'VELO', label: 'Velo' },
]

export default function ContractForm() {
  const { id } = useParams()
  const navigate = useNavigate()
  const isEdit = Boolean(id)

  const [formData, setFormData] = useState<FormData>(initialFormData)
  const [categories, setCategories] = useState<Category[]>([])
  const [suppliers, setSuppliers] = useState<Supplier[]>([])
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    loadInitialData()
  }, [])

  useEffect(() => {
    if (id) {
      loadContract(Number(id))
    }
  }, [id])

  const loadInitialData = async () => {
    setLoading(true)
    try {
      const [categoriesRes, suppliersRes] = await Promise.all([
        purchasesApi.categories.list({ is_active: true }),
        suppliersApi.list({ is_active: true }),
      ])
      setCategories(categoriesRes.data)
      setSuppliers(suppliersRes.data)
    } catch (error) {
      toast.error('Erreur de chargement')
    } finally {
      setLoading(false)
    }
  }

  const loadContract = async (contractId: number) => {
    try {
      const response = await purchasesApi.contracts.get(contractId)
      const contract = response.data
      setFormData({
        supplier_id: String(contract.supplier_id),
        category_id: String(contract.category_id),
        contract_type: contract.contract_type,
        name: contract.name,
        description: contract.description || '',
        reference: contract.reference || '',
        start_date: contract.start_date,
        end_date: contract.end_date || '',
        periodicity: contract.periodicity,
        amount_htva: String(contract.amount_htva),
        vat_rate: String(contract.vat_rate),
        payment_method: contract.payment_method,
        billing_day: String(contract.billing_day),
        vehicle_type: contract.vehicle_type || '',
        vehicle_co2: contract.vehicle_co2 ? String(contract.vehicle_co2) : '',
        vehicle_registration: contract.vehicle_registration || '',
        is_active: contract.is_active,
      })
    } catch (error) {
      toast.error('Erreur de chargement')
      navigate('/purchases/contracts')
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!formData.supplier_id || !formData.category_id || !formData.name) {
      toast.error('Veuillez remplir les champs obligatoires')
      return
    }

    setSaving(true)
    try {
      const data = {
        supplier_id: Number(formData.supplier_id),
        category_id: Number(formData.category_id),
        contract_type: formData.contract_type,
        name: formData.name,
        description: formData.description || null,
        reference: formData.reference || null,
        start_date: formData.start_date,
        end_date: formData.end_date || null,
        periodicity: formData.periodicity,
        amount_htva: parseFloat(formData.amount_htva),
        vat_rate: parseFloat(formData.vat_rate),
        payment_method: formData.payment_method,
        billing_day: Number(formData.billing_day),
        vehicle_type: formData.vehicle_type || null,
        vehicle_co2: formData.vehicle_co2 ? Number(formData.vehicle_co2) : null,
        vehicle_registration: formData.vehicle_registration || null,
        is_active: formData.is_active,
      }

      if (isEdit) {
        await purchasesApi.contracts.update(Number(id), data)
        toast.success('Contrat mis a jour')
      } else {
        await purchasesApi.contracts.create(data)
        toast.success('Contrat cree')
      }
      navigate('/purchases/contracts')
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Erreur lors de la sauvegarde')
    } finally {
      setSaving(false)
    }
  }

  const isVehicleContract = formData.contract_type === 'LEASING' || formData.contract_type === 'LOCATION'

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  return (
    <div>
      <div className="flex items-center gap-4 mb-6">
        <button
          onClick={() => navigate('/purchases/contracts')}
          className="text-gray-600 hover:text-gray-900"
        >
          <ArrowLeftIcon className="h-5 w-5" />
        </button>
        <h1 className="page-title mb-0">
          {isEdit ? 'Modifier contrat' : 'Nouveau contrat'}
        </h1>
      </div>

      <form onSubmit={handleSubmit} className="max-w-3xl space-y-6">
        {/* Basic info */}
        <div className="card">
          <h2 className="text-lg font-medium mb-4">Informations generales</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="md:col-span-2">
              <label className="label">Nom du contrat *</label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                className="input"
                required
                placeholder="Ex: Abonnement Microsoft 365"
              />
            </div>

            <div>
              <label className="label">Fournisseur *</label>
              <select
                value={formData.supplier_id}
                onChange={(e) => setFormData(prev => ({ ...prev, supplier_id: e.target.value }))}
                className="input"
                required
              >
                <option value="">Selectionner</option>
                {suppliers.map((s) => (
                  <option key={s.id} value={s.id}>{s.name}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="label">Categorie *</label>
              <select
                value={formData.category_id}
                onChange={(e) => setFormData(prev => ({ ...prev, category_id: e.target.value }))}
                className="input"
                required
              >
                <option value="">Selectionner</option>
                {categories.map((c) => (
                  <option key={c.id} value={c.id}>{c.name}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="label">Type de contrat</label>
              <select
                value={formData.contract_type}
                onChange={(e) => setFormData(prev => ({ ...prev, contract_type: e.target.value }))}
                className="input"
              >
                {contractTypes.map((t) => (
                  <option key={t.value} value={t.value}>{t.label}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="label">Reference</label>
              <input
                type="text"
                value={formData.reference}
                onChange={(e) => setFormData(prev => ({ ...prev, reference: e.target.value }))}
                className="input"
                placeholder="N contrat fournisseur"
              />
            </div>

            <div className="md:col-span-2">
              <label className="label">Description</label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                className="input"
                rows={2}
                placeholder="Description optionnelle..."
              />
            </div>
          </div>
        </div>

        {/* Billing */}
        <div className="card">
          <h2 className="text-lg font-medium mb-4">Facturation</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="label">Periodicite</label>
              <select
                value={formData.periodicity}
                onChange={(e) => setFormData(prev => ({ ...prev, periodicity: e.target.value }))}
                className="input"
              >
                {periodicities.map((p) => (
                  <option key={p.value} value={p.value}>{p.label}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="label">Montant HTVA *</label>
              <input
                type="number"
                step="0.01"
                value={formData.amount_htva}
                onChange={(e) => setFormData(prev => ({ ...prev, amount_htva: e.target.value }))}
                className="input"
                required
                placeholder="0.00"
              />
            </div>

            <div>
              <label className="label">Taux TVA %</label>
              <select
                value={formData.vat_rate}
                onChange={(e) => setFormData(prev => ({ ...prev, vat_rate: e.target.value }))}
                className="input"
              >
                <option value="0">0%</option>
                <option value="6">6%</option>
                <option value="12">12%</option>
                <option value="21">21%</option>
              </select>
            </div>

            <div>
              <label className="label">Jour de facturation</label>
              <input
                type="number"
                min="1"
                max="31"
                value={formData.billing_day}
                onChange={(e) => setFormData(prev => ({ ...prev, billing_day: e.target.value }))}
                className="input"
              />
            </div>

            <div>
              <label className="label">Methode de paiement</label>
              <select
                value={formData.payment_method}
                onChange={(e) => setFormData(prev => ({ ...prev, payment_method: e.target.value }))}
                className="input"
              >
                {paymentMethods.map((m) => (
                  <option key={m.value} value={m.value}>{m.label}</option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Dates */}
        <div className="card">
          <h2 className="text-lg font-medium mb-4">Duree</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="label">Date de debut *</label>
              <input
                type="date"
                value={formData.start_date}
                onChange={(e) => setFormData(prev => ({ ...prev, start_date: e.target.value }))}
                className="input"
                required
              />
            </div>

            <div>
              <label className="label">Date de fin</label>
              <input
                type="date"
                value={formData.end_date}
                onChange={(e) => setFormData(prev => ({ ...prev, end_date: e.target.value }))}
                className="input"
              />
              <p className="text-xs text-gray-500 mt-1">Laisser vide pour un contrat sans fin</p>
            </div>

            {isEdit && (
              <div className="md:col-span-2">
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={formData.is_active}
                    onChange={(e) => setFormData(prev => ({ ...prev, is_active: e.target.checked }))}
                    className="rounded border-gray-300"
                  />
                  <span>Contrat actif</span>
                </label>
              </div>
            )}
          </div>
        </div>

        {/* Vehicle info (for leasing/rental) */}
        {isVehicleContract && (
          <div className="card border-blue-200 bg-blue-50">
            <h2 className="text-lg font-medium mb-4 text-blue-800">Vehicule</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="label">Type de vehicule</label>
                <select
                  value={formData.vehicle_type}
                  onChange={(e) => setFormData(prev => ({ ...prev, vehicle_type: e.target.value }))}
                  className="input"
                >
                  {vehicleTypes.map((t) => (
                    <option key={t.value} value={t.value}>{t.label}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="label">Immatriculation</label>
                <input
                  type="text"
                  value={formData.vehicle_registration}
                  onChange={(e) => setFormData(prev => ({ ...prev, vehicle_registration: e.target.value }))}
                  className="input"
                  placeholder="1-ABC-123"
                />
              </div>

              <div>
                <label className="label">CO2 (g/km)</label>
                <input
                  type="number"
                  value={formData.vehicle_co2}
                  onChange={(e) => setFormData(prev => ({ ...prev, vehicle_co2: e.target.value }))}
                  className="input"
                  placeholder="Ex: 120"
                />
                <p className="text-xs text-gray-500 mt-1">Pour le calcul de deductibilite</p>
              </div>
            </div>
          </div>
        )}

        {/* Actions */}
        <div className="flex justify-end gap-3">
          <button
            type="button"
            onClick={() => navigate('/purchases/contracts')}
            className="btn-secondary"
          >
            Annuler
          </button>
          <button
            type="submit"
            disabled={saving}
            className="btn-primary disabled:opacity-50"
          >
            {saving ? 'Sauvegarde...' : isEdit ? 'Mettre a jour' : 'Creer'}
          </button>
        </div>
      </form>
    </div>
  )
}
