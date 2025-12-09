import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { purchasesApi, suppliersApi } from '../services/api'
import toast from 'react-hot-toast'
import { ArrowLeftIcon, CalculatorIcon } from '@heroicons/react/24/outline'

interface Category {
  id: number
  name: string
  default_vat_rate: number
  default_vat_deductible_rate: number
  default_fiscal_deductible_rate: number
  pcmn_account: string | null
  is_potential_investment: boolean
  investment_threshold_htva: number
}

interface Supplier {
  id: number
  name: string
}

interface Contract {
  id: number
  name: string
  supplier_id: number
}

interface FormData {
  supplier_id: string
  category_id: string
  contract_id: string
  purchase_date: string
  supplier_invoice_number: string
  description: string
  amount_htva: string
  vat_rate: string
  vat_deductible_rate: string
  fiscal_deductible_rate: string
  pcmn_account: string
  is_investment: boolean
  payment_method: string
  payment_date: string
  payment_reference: string
  create_fixed_asset: boolean
  asset_name: string
  depreciation_years: string
  service_start_date: string
}

interface Calculation {
  vat_amount: number
  vat_deductible_amount: number
  vat_non_deductible_amount: number
  amount_ttc: number
}

const initialFormData: FormData = {
  supplier_id: '',
  category_id: '',
  contract_id: '',
  purchase_date: new Date().toISOString().split('T')[0],
  supplier_invoice_number: '',
  description: '',
  amount_htva: '',
  vat_rate: '21',
  vat_deductible_rate: '100',
  fiscal_deductible_rate: '100',
  pcmn_account: '',
  is_investment: false,
  payment_method: '',
  payment_date: '',
  payment_reference: '',
  create_fixed_asset: false,
  asset_name: '',
  depreciation_years: '5',
  service_start_date: '',
}

const paymentMethods = [
  { value: 'VIREMENT', label: 'Virement' },
  { value: 'CARTE', label: 'Carte bancaire' },
  { value: 'DOMICILIATION', label: 'Domiciliation' },
  { value: 'ESPECES', label: 'Especes' },
  { value: 'CHEQUE', label: 'Cheque' },
]

export default function PurchaseForm() {
  const { id } = useParams()
  const navigate = useNavigate()
  const isEdit = Boolean(id)

  const [formData, setFormData] = useState<FormData>(initialFormData)
  const [categories, setCategories] = useState<Category[]>([])
  const [suppliers, setSuppliers] = useState<Supplier[]>([])
  const [contracts, setContracts] = useState<Contract[]>([])
  const [calculation, setCalculation] = useState<Calculation | null>(null)
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [showInvestmentSection, setShowInvestmentSection] = useState(false)

  useEffect(() => {
    loadInitialData()
  }, [])

  useEffect(() => {
    if (id) {
      loadPurchase(Number(id))
    }
  }, [id])

  useEffect(() => {
    // Check if should show investment section
    if (formData.category_id && formData.amount_htva) {
      const category = categories.find(c => c.id === Number(formData.category_id))
      if (category?.is_potential_investment) {
        const amount = parseFloat(formData.amount_htva) || 0
        setShowInvestmentSection(amount >= category.investment_threshold_htva)
      } else {
        setShowInvestmentSection(false)
      }
    }
  }, [formData.category_id, formData.amount_htva, categories])

  useEffect(() => {
    // Recalculate when amounts change
    if (formData.amount_htva && formData.vat_rate && formData.vat_deductible_rate) {
      calculateAmounts()
    }
  }, [formData.amount_htva, formData.vat_rate, formData.vat_deductible_rate])

  const loadInitialData = async () => {
    setLoading(true)
    try {
      const [categoriesRes, suppliersRes, contractsRes] = await Promise.all([
        purchasesApi.categories.list({ is_active: true }),
        suppliersApi.list({ is_active: true }),
        purchasesApi.contracts.list({ is_active: true }),
      ])
      setCategories(categoriesRes.data)
      setSuppliers(suppliersRes.data)
      setContracts(contractsRes.data)
    } catch (error) {
      toast.error('Erreur de chargement')
    } finally {
      setLoading(false)
    }
  }

  const loadPurchase = async (purchaseId: number) => {
    try {
      const response = await purchasesApi.get(purchaseId)
      const purchase = response.data
      setFormData({
        supplier_id: String(purchase.supplier_id),
        category_id: String(purchase.category_id),
        contract_id: purchase.contract_id ? String(purchase.contract_id) : '',
        purchase_date: purchase.purchase_date,
        supplier_invoice_number: purchase.supplier_invoice_number || '',
        description: purchase.description,
        amount_htva: String(purchase.amount_htva),
        vat_rate: String(purchase.vat_rate),
        vat_deductible_rate: String(purchase.vat_deductible_rate),
        fiscal_deductible_rate: String(purchase.fiscal_deductible_rate),
        pcmn_account: purchase.pcmn_account || '',
        is_investment: purchase.is_investment,
        payment_method: purchase.payment_method || '',
        payment_date: purchase.payment_date || '',
        payment_reference: purchase.payment_reference || '',
        create_fixed_asset: false,
        asset_name: '',
        depreciation_years: '5',
        service_start_date: '',
      })
      setCalculation({
        vat_amount: purchase.vat_amount,
        vat_deductible_amount: purchase.vat_deductible_amount,
        vat_non_deductible_amount: purchase.vat_non_deductible_amount,
        amount_ttc: purchase.amount_ttc,
      })
    } catch (error) {
      toast.error('Erreur de chargement')
      navigate('/purchases')
    }
  }

  const handleCategoryChange = async (categoryId: string) => {
    setFormData(prev => ({ ...prev, category_id: categoryId }))
    if (categoryId) {
      try {
        const response = await purchasesApi.categories.getDefaults(Number(categoryId))
        const defaults = response.data
        setFormData(prev => ({
          ...prev,
          vat_rate: String(defaults.vat_rate),
          vat_deductible_rate: String(defaults.vat_deductible_rate),
          fiscal_deductible_rate: String(defaults.fiscal_deductible_rate),
          pcmn_account: defaults.pcmn_account || '',
        }))
      } catch (error) {
        console.error('Error loading category defaults:', error)
      }
    }
  }

  const calculateAmounts = async () => {
    try {
      const response = await purchasesApi.calculate({
        amount_htva: parseFloat(formData.amount_htva) || 0,
        vat_rate: parseFloat(formData.vat_rate) || 0,
        vat_deductible_rate: parseFloat(formData.vat_deductible_rate) || 0,
        fiscal_deductible_rate: parseFloat(formData.fiscal_deductible_rate) || 0,
      })
      setCalculation(response.data)
    } catch (error) {
      console.error('Error calculating amounts:', error)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!formData.supplier_id || !formData.category_id) {
      toast.error('Veuillez remplir les champs obligatoires')
      return
    }

    setSaving(true)
    try {
      const data = {
        supplier_id: Number(formData.supplier_id),
        category_id: Number(formData.category_id),
        contract_id: formData.contract_id ? Number(formData.contract_id) : null,
        purchase_date: formData.purchase_date,
        supplier_invoice_number: formData.supplier_invoice_number || null,
        description: formData.description,
        amount_htva: parseFloat(formData.amount_htva),
        vat_rate: parseFloat(formData.vat_rate),
        vat_deductible_rate: parseFloat(formData.vat_deductible_rate),
        fiscal_deductible_rate: parseFloat(formData.fiscal_deductible_rate),
        pcmn_account: formData.pcmn_account || null,
        is_investment: formData.is_investment,
        payment_method: formData.payment_method || null,
        payment_date: formData.payment_date || null,
        payment_reference: formData.payment_reference || null,
        create_fixed_asset: formData.create_fixed_asset,
        asset_name: formData.asset_name || null,
        depreciation_years: formData.depreciation_years ? Number(formData.depreciation_years) : null,
        service_start_date: formData.service_start_date || null,
      }

      if (isEdit) {
        await purchasesApi.update(Number(id), data)
        toast.success('Achat mis a jour')
      } else {
        await purchasesApi.create(data)
        toast.success('Achat cree')
      }
      navigate('/purchases')
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Erreur lors de la sauvegarde')
    } finally {
      setSaving(false)
    }
  }

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('fr-BE', {
      style: 'currency',
      currency: 'EUR',
    }).format(amount)
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
      <div className="flex items-center gap-4 mb-6">
        <button
          onClick={() => navigate('/purchases')}
          className="text-gray-600 hover:text-gray-900"
        >
          <ArrowLeftIcon className="h-5 w-5" />
        </button>
        <h1 className="page-title mb-0">
          {isEdit ? 'Modifier achat' : 'Nouvel achat'}
        </h1>
      </div>

      <form onSubmit={handleSubmit} className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main form */}
        <div className="lg:col-span-2 space-y-6">
          {/* Basic info */}
          <div className="card">
            <h2 className="text-lg font-medium mb-4">Informations</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
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
                  onChange={(e) => handleCategoryChange(e.target.value)}
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
                <label className="label">Date achat *</label>
                <input
                  type="date"
                  value={formData.purchase_date}
                  onChange={(e) => setFormData(prev => ({ ...prev, purchase_date: e.target.value }))}
                  className="input"
                  required
                />
              </div>

              <div>
                <label className="label">N facture fournisseur</label>
                <input
                  type="text"
                  value={formData.supplier_invoice_number}
                  onChange={(e) => setFormData(prev => ({ ...prev, supplier_invoice_number: e.target.value }))}
                  className="input"
                  placeholder="Ex: FAC-2024-001"
                />
              </div>

              <div className="md:col-span-2">
                <label className="label">Description *</label>
                <input
                  type="text"
                  value={formData.description}
                  onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                  className="input"
                  required
                  placeholder="Description de l'achat"
                />
              </div>

              <div>
                <label className="label">Contrat lie</label>
                <select
                  value={formData.contract_id}
                  onChange={(e) => setFormData(prev => ({ ...prev, contract_id: e.target.value }))}
                  className="input"
                >
                  <option value="">Aucun</option>
                  {contracts
                    .filter(c => !formData.supplier_id || c.supplier_id === Number(formData.supplier_id))
                    .map((c) => (
                      <option key={c.id} value={c.id}>{c.name}</option>
                    ))}
                </select>
              </div>
            </div>
          </div>

          {/* Amounts */}
          <div className="card">
            <h2 className="text-lg font-medium mb-4">Montants & TVA</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
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
                <label className="label">TVA deductible %</label>
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  max="100"
                  value={formData.vat_deductible_rate}
                  onChange={(e) => setFormData(prev => ({ ...prev, vat_deductible_rate: e.target.value }))}
                  className="input"
                />
              </div>

              <div>
                <label className="label">Deductibilite fiscale %</label>
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  max="100"
                  value={formData.fiscal_deductible_rate}
                  onChange={(e) => setFormData(prev => ({ ...prev, fiscal_deductible_rate: e.target.value }))}
                  className="input"
                />
              </div>

              <div>
                <label className="label">Compte PCMN</label>
                <input
                  type="text"
                  value={formData.pcmn_account}
                  onChange={(e) => setFormData(prev => ({ ...prev, pcmn_account: e.target.value }))}
                  className="input"
                  placeholder="Ex: 612000"
                />
              </div>
            </div>
          </div>

          {/* Payment */}
          <div className="card">
            <h2 className="text-lg font-medium mb-4">Paiement</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="label">Methode</label>
                <select
                  value={formData.payment_method}
                  onChange={(e) => setFormData(prev => ({ ...prev, payment_method: e.target.value }))}
                  className="input"
                >
                  <option value="">Selectionner</option>
                  {paymentMethods.map((m) => (
                    <option key={m.value} value={m.value}>{m.label}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="label">Date paiement</label>
                <input
                  type="date"
                  value={formData.payment_date}
                  onChange={(e) => setFormData(prev => ({ ...prev, payment_date: e.target.value }))}
                  className="input"
                />
              </div>

              <div>
                <label className="label">Reference</label>
                <input
                  type="text"
                  value={formData.payment_reference}
                  onChange={(e) => setFormData(prev => ({ ...prev, payment_reference: e.target.value }))}
                  className="input"
                  placeholder="Communication structuree..."
                />
              </div>
            </div>
          </div>

          {/* Investment section */}
          {showInvestmentSection && (
            <div className="card border-purple-200 bg-purple-50">
              <h2 className="text-lg font-medium mb-4 text-purple-800">
                Investissement
              </h2>
              <p className="text-sm text-purple-600 mb-4">
                Ce montant depasse le seuil d'investissement pour cette categorie.
              </p>

              <div className="space-y-4">
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={formData.is_investment}
                    onChange={(e) => setFormData(prev => ({ ...prev, is_investment: e.target.checked }))}
                    className="rounded border-gray-300"
                  />
                  <span>Traiter comme un investissement</span>
                </label>

                {formData.is_investment && (
                  <>
                    <label className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={formData.create_fixed_asset}
                        onChange={(e) => setFormData(prev => ({ ...prev, create_fixed_asset: e.target.checked }))}
                        className="rounded border-gray-300"
                      />
                      <span>Creer une immobilisation</span>
                    </label>

                    {formData.create_fixed_asset && (
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4 p-4 bg-white rounded-lg">
                        <div>
                          <label className="label">Nom de l'actif</label>
                          <input
                            type="text"
                            value={formData.asset_name}
                            onChange={(e) => setFormData(prev => ({ ...prev, asset_name: e.target.value }))}
                            className="input"
                            placeholder="Ex: MacBook Pro 2024"
                          />
                        </div>

                        <div>
                          <label className="label">Duree amortissement (annees)</label>
                          <input
                            type="number"
                            min="1"
                            max="50"
                            value={formData.depreciation_years}
                            onChange={(e) => setFormData(prev => ({ ...prev, depreciation_years: e.target.value }))}
                            className="input"
                          />
                        </div>

                        <div>
                          <label className="label">Date mise en service</label>
                          <input
                            type="date"
                            value={formData.service_start_date}
                            onChange={(e) => setFormData(prev => ({ ...prev, service_start_date: e.target.value }))}
                            className="input"
                          />
                        </div>
                      </div>
                    )}
                  </>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Sidebar - Calculation */}
        <div className="lg:col-span-1">
          <div className="card sticky top-24">
            <div className="flex items-center gap-2 mb-4">
              <CalculatorIcon className="h-5 w-5 text-primary-600" />
              <h2 className="text-lg font-medium">Calcul</h2>
            </div>

            {calculation ? (
              <div className="space-y-4">
                <div className="flex justify-between py-2 border-b">
                  <span className="text-gray-600">Montant HTVA</span>
                  <span className="font-medium">
                    {formatCurrency(parseFloat(formData.amount_htva) || 0)}
                  </span>
                </div>

                <div className="flex justify-between py-2 border-b">
                  <span className="text-gray-600">TVA ({formData.vat_rate}%)</span>
                  <span className="font-medium">
                    {formatCurrency(calculation.vat_amount)}
                  </span>
                </div>

                <div className="flex justify-between py-2 border-b text-green-600">
                  <span>TVA deductible ({formData.vat_deductible_rate}%)</span>
                  <span className="font-medium">
                    {formatCurrency(calculation.vat_deductible_amount)}
                  </span>
                </div>

                <div className="flex justify-between py-2 border-b text-orange-600">
                  <span>TVA non deductible</span>
                  <span className="font-medium">
                    {formatCurrency(calculation.vat_non_deductible_amount)}
                  </span>
                </div>

                <div className="flex justify-between py-2 text-lg font-bold">
                  <span>Total TTC</span>
                  <span className="text-primary-600">
                    {formatCurrency(calculation.amount_ttc)}
                  </span>
                </div>

                <div className="mt-4 p-3 bg-gray-50 rounded-lg text-sm">
                  <p className="text-gray-600">
                    <strong>Cout reel:</strong>{' '}
                    {formatCurrency(
                      (parseFloat(formData.amount_htva) || 0) +
                      calculation.vat_non_deductible_amount
                    )}
                  </p>
                  <p className="text-gray-500 mt-1">
                    (HTVA + TVA non deductible)
                  </p>
                </div>
              </div>
            ) : (
              <p className="text-gray-500 text-sm">
                Entrez un montant pour voir le calcul
              </p>
            )}

            <div className="mt-6 pt-6 border-t space-y-3">
              <button
                type="submit"
                disabled={saving}
                className="w-full btn-primary disabled:opacity-50"
              >
                {saving ? 'Sauvegarde...' : isEdit ? 'Mettre a jour' : 'Creer'}
              </button>

              <button
                type="button"
                onClick={() => navigate('/purchases')}
                className="w-full btn-secondary"
              >
                Annuler
              </button>
            </div>
          </div>
        </div>
      </form>
    </div>
  )
}
