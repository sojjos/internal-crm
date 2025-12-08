import { useEffect, useState } from 'react'
import { useForm } from 'react-hook-form'
import { companyApi, expensesApi } from '../services/api'
import toast from 'react-hot-toast'

interface CompanySettings {
  company_name: string
  address_street: string
  address_city: string
  address_postal_code: string
  address_country: string
  vat_number: string
  phone: string
  email: string
  website: string
  vat_rates: number[]
  default_vat_rate: number
  invoice_number_format: string
  default_payment_terms: number
  peppol_enabled: boolean
  peppol_participant_id: string
  paypal_enabled: boolean
  paypal_mode: string
  paypal_client_id: string
  paypal_client_secret: string
  default_currency: string
  legal_mentions: string
  general_terms: string
  smtp_host: string
  smtp_port: number
  smtp_user: string
  smtp_password: string
  smtp_from_email: string
  smtp_tls: boolean
}

interface ExpenseType {
  id: number
  name: string
  description: string
  is_active: boolean
}

export default function Settings() {
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [activeTab, setActiveTab] = useState('company')
  const [expenseTypes, setExpenseTypes] = useState<ExpenseType[]>([])
  const [newExpenseType, setNewExpenseType] = useState('')

  const { register, handleSubmit, reset } = useForm<CompanySettings>()

  useEffect(() => {
    loadSettings()
    loadExpenseTypes()
  }, [])

  const loadSettings = async () => {
    try {
      const response = await companyApi.get()
      reset(response.data)
    } catch (error) {
      console.error('Failed to load settings', error)
    } finally {
      setLoading(false)
    }
  }

  const loadExpenseTypes = async () => {
    try {
      const response = await expensesApi.types.list()
      setExpenseTypes(response.data)
    } catch (error) {
      console.error('Failed to load expense types', error)
    }
  }

  const onSubmit = async (data: CompanySettings) => {
    setSaving(true)
    try {
      await companyApi.update(data)
      toast.success('Paramètres enregistrés')
    } catch (error) {
      toast.error('Erreur lors de la sauvegarde')
    } finally {
      setSaving(false)
    }
  }

  const handleAddExpenseType = async () => {
    if (!newExpenseType.trim()) return

    try {
      await expensesApi.types.create({ name: newExpenseType.trim() })
      toast.success('Type de frais ajouté')
      setNewExpenseType('')
      loadExpenseTypes()
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Erreur')
    }
  }

  const tabs = [
    { id: 'company', name: 'Société' },
    { id: 'invoicing', name: 'Facturation' },
    { id: 'integrations', name: 'Intégrations' },
    { id: 'email', name: 'Email' },
    { id: 'expense_types', name: 'Types de frais' },
  ]

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  return (
    <div>
      <h1 className="page-title">Paramètres</h1>

      <div className="flex gap-4 mb-6 border-b">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-4 py-2 -mb-px ${
              activeTab === tab.id
                ? 'border-b-2 border-primary-600 text-primary-600 font-medium'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            {tab.name}
          </button>
        ))}
      </div>

      <form onSubmit={handleSubmit(onSubmit)}>
        {activeTab === 'company' && (
          <div className="card">
            <h2 className="text-lg font-semibold mb-4">Informations société</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="md:col-span-2">
                <label className="label">Nom de la société</label>
                <input {...register('company_name')} className="input" />
              </div>
              <div className="md:col-span-2">
                <label className="label">Adresse</label>
                <input {...register('address_street')} className="input" />
              </div>
              <div>
                <label className="label">Code postal</label>
                <input {...register('address_postal_code')} className="input" />
              </div>
              <div>
                <label className="label">Ville</label>
                <input {...register('address_city')} className="input" />
              </div>
              <div>
                <label className="label">Pays</label>
                <input {...register('address_country')} className="input" />
              </div>
              <div>
                <label className="label">Numéro de TVA</label>
                <input {...register('vat_number')} className="input" />
              </div>
              <div>
                <label className="label">Téléphone</label>
                <input {...register('phone')} className="input" />
              </div>
              <div>
                <label className="label">Email</label>
                <input type="email" {...register('email')} className="input" />
              </div>
              <div>
                <label className="label">Site web</label>
                <input {...register('website')} className="input" />
              </div>
            </div>
          </div>
        )}

        {activeTab === 'invoicing' && (
          <div className="card">
            <h2 className="text-lg font-semibold mb-4">Paramètres de facturation</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="label">Format numérotation</label>
                <input
                  {...register('invoice_number_format')}
                  className="input"
                  placeholder="YYYY-0001"
                />
              </div>
              <div>
                <label className="label">Délai de paiement (jours)</label>
                <input
                  type="number"
                  {...register('default_payment_terms', { valueAsNumber: true })}
                  className="input"
                />
              </div>
              <div>
                <label className="label">Taux TVA par défaut (%)</label>
                <select
                  {...register('default_vat_rate', { valueAsNumber: true })}
                  className="input"
                >
                  <option value={21}>21%</option>
                  <option value={12}>12%</option>
                  <option value={6}>6%</option>
                  <option value={0}>0%</option>
                </select>
              </div>
              <div>
                <label className="label">Devise</label>
                <input {...register('default_currency')} className="input" />
              </div>
              <div className="md:col-span-2">
                <label className="label">Mentions légales (pied de facture)</label>
                <textarea {...register('legal_mentions')} className="input" rows={3} />
              </div>
              <div className="md:col-span-2">
                <label className="label">Conditions générales</label>
                <textarea {...register('general_terms')} className="input" rows={4} />
              </div>
            </div>
          </div>
        )}

        {activeTab === 'integrations' && (
          <div className="space-y-6">
            <div className="card">
              <h2 className="text-lg font-semibold mb-4">Peppol / E-facturation</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="md:col-span-2">
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      {...register('peppol_enabled')}
                      className="rounded border-gray-300 text-primary-600 mr-2"
                    />
                    <span>Activer Peppol</span>
                  </label>
                </div>
                <div>
                  <label className="label">ID Participant Peppol</label>
                  <input {...register('peppol_participant_id')} className="input" />
                </div>
              </div>
            </div>

            <div className="card">
              <h2 className="text-lg font-semibold mb-4">PayPal</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="md:col-span-2">
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      {...register('paypal_enabled')}
                      className="rounded border-gray-300 text-primary-600 mr-2"
                    />
                    <span>Activer PayPal</span>
                  </label>
                </div>
                <div>
                  <label className="label">Mode</label>
                  <select {...register('paypal_mode')} className="input">
                    <option value="sandbox">Sandbox (test)</option>
                    <option value="live">Production</option>
                  </select>
                </div>
                <div>
                  <label className="label">Client ID</label>
                  <input {...register('paypal_client_id')} className="input" />
                </div>
                <div>
                  <label className="label">Client Secret</label>
                  <input
                    type="password"
                    {...register('paypal_client_secret')}
                    className="input"
                  />
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'email' && (
          <div className="card">
            <h2 className="text-lg font-semibold mb-4">Configuration SMTP</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="label">Serveur SMTP</label>
                <input {...register('smtp_host')} className="input" />
              </div>
              <div>
                <label className="label">Port</label>
                <input
                  type="number"
                  {...register('smtp_port', { valueAsNumber: true })}
                  className="input"
                />
              </div>
              <div>
                <label className="label">Utilisateur</label>
                <input {...register('smtp_user')} className="input" />
              </div>
              <div>
                <label className="label">Mot de passe</label>
                <input type="password" {...register('smtp_password')} className="input" />
              </div>
              <div>
                <label className="label">Email expéditeur</label>
                <input type="email" {...register('smtp_from_email')} className="input" />
              </div>
              <div className="flex items-center">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    {...register('smtp_tls')}
                    className="rounded border-gray-300 text-primary-600 mr-2"
                  />
                  <span>Utiliser TLS</span>
                </label>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'expense_types' && (
          <div className="card">
            <h2 className="text-lg font-semibold mb-4">Types de frais</h2>
            <div className="flex gap-2 mb-4">
              <input
                type="text"
                value={newExpenseType}
                onChange={(e) => setNewExpenseType(e.target.value)}
                className="input flex-1"
                placeholder="Nouveau type de frais..."
              />
              <button
                type="button"
                onClick={handleAddExpenseType}
                className="btn-primary"
              >
                Ajouter
              </button>
            </div>
            <ul className="divide-y">
              {expenseTypes.map((type) => (
                <li key={type.id} className="py-2 flex justify-between items-center">
                  <span>{type.name}</span>
                  <span
                    className={`px-2 py-1 text-xs rounded ${
                      type.is_active
                        ? 'bg-green-100 text-green-800'
                        : 'bg-gray-100 text-gray-500'
                    }`}
                  >
                    {type.is_active ? 'Actif' : 'Inactif'}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {activeTab !== 'expense_types' && (
          <div className="flex justify-end mt-6">
            <button type="submit" disabled={saving} className="btn-primary">
              {saving ? 'Enregistrement...' : 'Enregistrer'}
            </button>
          </div>
        )}
      </form>
    </div>
  )
}
