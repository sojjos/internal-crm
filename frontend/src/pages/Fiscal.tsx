import { useEffect, useState } from 'react'
import { fiscalApi, annualAccountsApi } from '../services/api'
import {
  PlusIcon,
  CalculatorIcon,
  PaperAirplaneIcon,
  BanknotesIcon,
  CheckIcon,
} from '@heroicons/react/24/outline'
import toast from 'react-hot-toast'

interface TaxDeclaration {
  id: number
  reference: string
  fiscal_year_id: number
  declaration_type: string
  status: string
  period_start: string
  period_end: string
  due_date: string | null
  enterprise_number: string
  biztax_status: string
  biztax_reference: string | null
  created_at: string
}

interface ISocCalculation {
  id: number
  accounting_result: number
  dna_total: number
  deduction_rdt: number
  deduction_innovation: number
  deduction_investment: number
  other_deductions: number
  carried_forward_losses: number
  losses_used: number
  taxable_base: number
  tax_at_standard_rate: number
  tax_at_sme_rate: number
  total_tax: number
  prepayments_q1: number
  prepayments_q2: number
  prepayments_q3: number
  prepayments_q4: number
  total_prepayments: number
  prepayment_bonus: number
  tax_balance: number
  is_sme: boolean
}

interface Prepayment {
  id: number
  fiscal_year_id: number
  quarter: number
  reference: string
  due_date: string
  payment_date: string | null
  estimated_tax: number
  amount_paid: number
  bonus_rate: number
  bonus_amount: number
  is_paid: boolean
}

interface FiscalYear {
  id: number
  name: string
}

const statusMap: Record<string, { label: string; color: string }> = {
  DRAFT: { label: 'Brouillon', color: 'bg-gray-100 text-gray-800' },
  IN_PROGRESS: { label: 'En cours', color: 'bg-yellow-100 text-yellow-800' },
  CALCULATED: { label: 'Calcule', color: 'bg-blue-100 text-blue-800' },
  VALIDATED: { label: 'Valide', color: 'bg-green-100 text-green-800' },
  SUBMITTED: { label: 'Soumis', color: 'bg-purple-100 text-purple-800' },
}

export default function Fiscal() {
  const [declarations, setDeclarations] = useState<TaxDeclaration[]>([])
  const [prepayments, setPrepayments] = useState<Prepayment[]>([])
  const [fiscalYears, setFiscalYears] = useState<FiscalYear[]>([])
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<'isoc' | 'prepayments'>('isoc')
  const [selectedDeclaration, setSelectedDeclaration] = useState<TaxDeclaration | null>(null)
  const [isocCalc, setIsocCalc] = useState<ISocCalculation | null>(null)
  const [showNewModal, setShowNewModal] = useState(false)
  const [selectedYear, setSelectedYear] = useState<number | null>(null)

  const [newDeclaration, setNewDeclaration] = useState({
    fiscal_year_id: 0,
    declaration_type: 'ISOC',
    period_start: '',
    period_end: '',
    enterprise_number: '',
    company_name: '',
  })

  useEffect(() => {
    loadInitialData()
  }, [])

  useEffect(() => {
    if (selectedYear) {
      loadDeclarations()
      loadPrepayments()
    }
  }, [selectedYear])

  const loadInitialData = async () => {
    try {
      const yearsRes = await annualAccountsApi.fiscalYears.list()
      setFiscalYears(yearsRes.data)
      if (yearsRes.data.length > 0) {
        setSelectedYear(yearsRes.data[0].id)
      }
    } catch (error) {
      console.error('Error loading data:', error)
    } finally {
      setLoading(false)
    }
  }

  const loadDeclarations = async () => {
    try {
      const response = await fiscalApi.declarations.list({ fiscal_year_id: selectedYear })
      setDeclarations(response.data)
    } catch (error) {
      console.error('Error loading declarations:', error)
    }
  }

  const loadPrepayments = async () => {
    try {
      const response = await fiscalApi.prepayments.list({ fiscal_year_id: selectedYear })
      setPrepayments(response.data)
    } catch (error) {
      console.error('Error loading prepayments:', error)
    }
  }

  const loadIsocCalculation = async (declId: number) => {
    try {
      const response = await fiscalApi.isoc.get(declId)
      setIsocCalc(response.data)
    } catch (error) {
      console.error('Error loading ISoc:', error)
    }
  }

  const handleSelectDeclaration = async (decl: TaxDeclaration) => {
    setSelectedDeclaration(decl)
    if (decl.declaration_type === 'ISOC') {
      await loadIsocCalculation(decl.id)
    }
  }

  const handleCreateDeclaration = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await fiscalApi.declarations.create({
        ...newDeclaration,
        fiscal_year_id: selectedYear,
      })
      toast.success('Declaration creee')
      setShowNewModal(false)
      loadDeclarations()
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Erreur')
    }
  }

  const handleCalculateIsoc = async () => {
    if (!selectedDeclaration) return
    try {
      await fiscalApi.isoc.calculate(selectedDeclaration.id)
      toast.success('ISoc calcule')
      await loadIsocCalculation(selectedDeclaration.id)
      loadDeclarations()
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Erreur')
    }
  }

  const handleSubmitBiztax = async () => {
    if (!selectedDeclaration) return
    try {
      await fiscalApi.declarations.submitBiztax(selectedDeclaration.id)
      toast.success('Soumis a Biztax')
      loadDeclarations()
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Erreur')
    }
  }

  const handleRecordPrepayment = async (prepId: number, amountPaid: number) => {
    try {
      await fiscalApi.prepayments.update(prepId, {
        amount_paid: amountPaid,
        payment_date: new Date().toISOString().split('T')[0],
        is_paid: true,
      })
      toast.success('VA enregistre')
      loadPrepayments()
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Erreur')
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
        <h1 className="page-title mb-0">Fiscalite & ISoc</h1>
        <button
          onClick={() => setShowNewModal(true)}
          className="btn-primary flex items-center"
        >
          <PlusIcon className="h-5 w-5 mr-1" />
          Nouvelle declaration
        </button>
      </div>

      {/* Year Selection & Tabs */}
      <div className="card mb-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <label className="label mb-0">Exercice:</label>
            <select
              value={selectedYear || ''}
              onChange={(e) => setSelectedYear(parseInt(e.target.value))}
              className="input w-auto"
            >
              {fiscalYears.map((year) => (
                <option key={year.id} value={year.id}>{year.name}</option>
              ))}
            </select>
          </div>
          <div className="flex rounded-lg overflow-hidden border">
            <button
              onClick={() => setActiveTab('isoc')}
              className={`px-4 py-2 ${activeTab === 'isoc' ? 'bg-primary-600 text-white' : 'bg-white'}`}
            >
              ISoc
            </button>
            <button
              onClick={() => setActiveTab('prepayments')}
              className={`px-4 py-2 ${activeTab === 'prepayments' ? 'bg-primary-600 text-white' : 'bg-white'}`}
            >
              Versements Anticipes
            </button>
          </div>
        </div>
      </div>

      {activeTab === 'isoc' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Declarations List */}
          <div className="card">
            <h2 className="text-lg font-semibold mb-4">Declarations ISoc</h2>
            <div className="space-y-2">
              {declarations.filter(d => d.declaration_type === 'ISOC').map((decl) => (
                <div
                  key={decl.id}
                  onClick={() => handleSelectDeclaration(decl)}
                  className={`p-4 border rounded-lg cursor-pointer hover:bg-gray-50 ${
                    selectedDeclaration?.id === decl.id ? 'border-primary-500 bg-primary-50' : ''
                  }`}
                >
                  <div className="flex justify-between items-start">
                    <div>
                      <p className="font-medium">{decl.reference}</p>
                      <p className="text-sm text-gray-500">
                        {formatDate(decl.period_start)} - {formatDate(decl.period_end)}
                      </p>
                    </div>
                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                      statusMap[decl.status]?.color || 'bg-gray-100'
                    }`}>
                      {statusMap[decl.status]?.label || decl.status}
                    </span>
                  </div>
                </div>
              ))}
              {declarations.filter(d => d.declaration_type === 'ISOC').length === 0 && (
                <p className="text-gray-500 text-center py-4">Aucune declaration</p>
              )}
            </div>
          </div>

          {/* ISoc Calculation Details */}
          <div className="card">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-semibold">Calcul ISoc</h2>
              {selectedDeclaration && (
                <div className="flex gap-2">
                  <button
                    onClick={handleCalculateIsoc}
                    className="btn-secondary flex items-center text-sm"
                  >
                    <CalculatorIcon className="h-4 w-4 mr-1" />
                    Calculer
                  </button>
                  {selectedDeclaration.status === 'CALCULATED' && (
                    <button
                      onClick={handleSubmitBiztax}
                      className="btn-primary flex items-center text-sm"
                    >
                      <PaperAirplaneIcon className="h-4 w-4 mr-1" />
                      Biztax
                    </button>
                  )}
                </div>
              )}
            </div>

            {isocCalc ? (
              <div className="space-y-4">
                <div className="bg-gray-50 p-4 rounded-lg">
                  <h3 className="font-medium mb-2">Base imposable</h3>
                  <div className="space-y-1 text-sm">
                    <div className="flex justify-between">
                      <span>Resultat comptable</span>
                      <span>{formatCurrency(isocCalc.accounting_result)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>+ DNA</span>
                      <span>{formatCurrency(isocCalc.dna_total)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>- Deductions RDT</span>
                      <span>{formatCurrency(isocCalc.deduction_rdt)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>- Pertes utilisees</span>
                      <span>{formatCurrency(isocCalc.losses_used)}</span>
                    </div>
                    <div className="flex justify-between font-semibold border-t pt-1">
                      <span>Base imposable</span>
                      <span>{formatCurrency(isocCalc.taxable_base)}</span>
                    </div>
                  </div>
                </div>

                <div className="bg-blue-50 p-4 rounded-lg">
                  <h3 className="font-medium mb-2">Impot</h3>
                  <div className="space-y-1 text-sm">
                    {isocCalc.is_sme && (
                      <div className="flex justify-between">
                        <span>Taux PME (20%)</span>
                        <span>{formatCurrency(isocCalc.tax_at_sme_rate)}</span>
                      </div>
                    )}
                    <div className="flex justify-between">
                      <span>Taux normal (25%)</span>
                      <span>{formatCurrency(isocCalc.tax_at_standard_rate)}</span>
                    </div>
                    <div className="flex justify-between font-semibold border-t pt-1">
                      <span>Impot total</span>
                      <span>{formatCurrency(isocCalc.total_tax)}</span>
                    </div>
                  </div>
                </div>

                <div className="bg-green-50 p-4 rounded-lg">
                  <h3 className="font-medium mb-2">Versements anticipes</h3>
                  <div className="space-y-1 text-sm">
                    <div className="flex justify-between">
                      <span>VA Total</span>
                      <span>{formatCurrency(isocCalc.total_prepayments)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Bonification VA</span>
                      <span>{formatCurrency(isocCalc.prepayment_bonus)}</span>
                    </div>
                    <div className="flex justify-between font-semibold border-t pt-1">
                      <span>Solde</span>
                      <span className={isocCalc.tax_balance < 0 ? 'text-green-600' : 'text-red-600'}>
                        {formatCurrency(isocCalc.tax_balance)}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <p className="text-gray-500 text-center py-8">
                Selectionnez une declaration pour voir le calcul
              </p>
            )}
          </div>
        </div>
      )}

      {activeTab === 'prepayments' && (
        <div className="card">
          <h2 className="text-lg font-semibold mb-4">Versements Anticipes (VA)</h2>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead>
                <tr>
                  <th className="table-header px-6 py-3">Reference</th>
                  <th className="table-header px-6 py-3">Trimestre</th>
                  <th className="table-header px-6 py-3">Echeance</th>
                  <th className="table-header px-6 py-3">Taux bonus</th>
                  <th className="table-header px-6 py-3">Montant paye</th>
                  <th className="table-header px-6 py-3">Bonification</th>
                  <th className="table-header px-6 py-3">Statut</th>
                  <th className="table-header px-6 py-3">Actions</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {prepayments.map((prep) => (
                  <tr key={prep.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 font-mono">{prep.reference}</td>
                    <td className="px-6 py-4">Q{prep.quarter}</td>
                    <td className="px-6 py-4">{formatDate(prep.due_date)}</td>
                    <td className="px-6 py-4">{prep.bonus_rate}%</td>
                    <td className="px-6 py-4">{formatCurrency(prep.amount_paid)}</td>
                    <td className="px-6 py-4">{formatCurrency(prep.bonus_amount)}</td>
                    <td className="px-6 py-4">
                      {prep.is_paid ? (
                        <span className="text-green-600 flex items-center">
                          <CheckIcon className="h-4 w-4 mr-1" /> Paye
                        </span>
                      ) : (
                        <span className="text-orange-600">En attente</span>
                      )}
                    </td>
                    <td className="px-6 py-4">
                      {!prep.is_paid && (
                        <button
                          onClick={() => {
                            const amount = prompt('Montant paye:')
                            if (amount) handleRecordPrepayment(prep.id, parseFloat(amount))
                          }}
                          className="text-primary-600 hover:text-primary-800"
                        >
                          <BanknotesIcon className="h-5 w-5" />
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {prepayments.length === 0 && (
              <p className="text-center py-8 text-gray-500">Aucun versement anticipe</p>
            )}
          </div>
        </div>
      )}

      {/* New Declaration Modal */}
      {showNewModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h2 className="text-lg font-semibold mb-4">Nouvelle declaration</h2>
            <form onSubmit={handleCreateDeclaration}>
              <div className="space-y-4">
                <div>
                  <label className="label">Type</label>
                  <select
                    value={newDeclaration.declaration_type}
                    onChange={(e) => setNewDeclaration({ ...newDeclaration, declaration_type: e.target.value })}
                    className="input"
                  >
                    <option value="ISOC">ISoc</option>
                    <option value="TVA">TVA</option>
                    <option value="PRECOMPTE_PRO">Precompte professionnel</option>
                  </select>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="label">Debut periode</label>
                    <input
                      type="date"
                      value={newDeclaration.period_start}
                      onChange={(e) => setNewDeclaration({ ...newDeclaration, period_start: e.target.value })}
                      className="input"
                      required
                    />
                  </div>
                  <div>
                    <label className="label">Fin periode</label>
                    <input
                      type="date"
                      value={newDeclaration.period_end}
                      onChange={(e) => setNewDeclaration({ ...newDeclaration, period_end: e.target.value })}
                      className="input"
                      required
                    />
                  </div>
                </div>
                <div>
                  <label className="label">N Entreprise</label>
                  <input
                    type="text"
                    value={newDeclaration.enterprise_number}
                    onChange={(e) => setNewDeclaration({ ...newDeclaration, enterprise_number: e.target.value })}
                    className="input"
                    required
                  />
                </div>
              </div>
              <div className="flex justify-end gap-2 mt-6">
                <button type="button" onClick={() => setShowNewModal(false)} className="btn-secondary">
                  Annuler
                </button>
                <button type="submit" className="btn-primary">Creer</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
