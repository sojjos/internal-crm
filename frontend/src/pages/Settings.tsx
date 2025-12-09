import { useEffect, useState } from 'react'
import { useForm } from 'react-hook-form'
import { companyApi, expensesApi, authApi } from '../services/api'
import { useAuth } from '../context/AuthContext'
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
  const { user, refreshUser } = useAuth()
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [activeTab, setActiveTab] = useState('account')
  const [expenseTypes, setExpenseTypes] = useState<ExpenseType[]>([])
  const [newExpenseType, setNewExpenseType] = useState('')

  // Profile form
  const [profileForm, setProfileForm] = useState({
    first_name: '',
    last_name: '',
    email: '',
    phone: '',
  })
  const [passwordForm, setPasswordForm] = useState({
    current_password: '',
    new_password: '',
    confirm_password: '',
  })
  const [savingProfile, setSavingProfile] = useState(false)
  const [changingPassword, setChangingPassword] = useState(false)

  const { register, handleSubmit, reset } = useForm<CompanySettings>()

  useEffect(() => {
    loadSettings()
    loadExpenseTypes()
  }, [])

  useEffect(() => {
    if (user) {
      setProfileForm({
        first_name: user.first_name || '',
        last_name: user.last_name || '',
        email: user.email || '',
        phone: user.phone || '',
      })
    }
  }, [user])

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
      toast.success('Parametres enregistres')
    } catch (error) {
      toast.error('Erreur lors de la sauvegarde')
    } finally {
      setSaving(false)
    }
  }

  const handleSaveProfile = async () => {
    setSavingProfile(true)
    try {
      await authApi.updateProfile(profileForm)
      toast.success('Profil mis a jour')
      if (refreshUser) refreshUser()
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Erreur lors de la sauvegarde')
    } finally {
      setSavingProfile(false)
    }
  }

  const handleChangePassword = async () => {
    if (passwordForm.new_password !== passwordForm.confirm_password) {
      toast.error('Les mots de passe ne correspondent pas')
      return
    }
    if (passwordForm.new_password.length < 6) {
      toast.error('Le mot de passe doit contenir au moins 6 caracteres')
      return
    }

    setChangingPassword(true)
    try {
      await authApi.changePassword(passwordForm.current_password, passwordForm.new_password)
      toast.success('Mot de passe modifie')
      setPasswordForm({ current_password: '', new_password: '', confirm_password: '' })
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Erreur lors du changement de mot de passe')
    } finally {
      setChangingPassword(false)
    }
  }

  const handleAddExpenseType = async () => {
    if (!newExpenseType.trim()) return

    try {
      await expensesApi.types.create({ name: newExpenseType.trim() })
      toast.success('Type de frais ajoute')
      setNewExpenseType('')
      loadExpenseTypes()
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Erreur')
    }
  }

  const tabs = [
    { id: 'account', name: 'Mon compte' },
    { id: 'company', name: 'Societe' },
    { id: 'invoicing', name: 'Facturation' },
    { id: 'integrations', name: 'Integrations' },
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
      <h1 className="page-title">Parametres</h1>

      <div className="flex gap-4 mb-6 border-b overflow-x-auto">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-4 py-2 -mb-px whitespace-nowrap ${
              activeTab === tab.id
                ? 'border-b-2 border-primary-600 text-primary-600 font-medium'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            {tab.name}
          </button>
        ))}
      </div>

      {/* Mon Compte Tab */}
      {activeTab === 'account' && (
        <div className="space-y-6">
          <div className="card">
            <h2 className="text-lg font-semibold mb-4">Informations personnelles</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="label">Prenom</label>
                <input
                  type="text"
                  value={profileForm.first_name}
                  onChange={(e) => setProfileForm({ ...profileForm, first_name: e.target.value })}
                  className="input"
                />
              </div>
              <div>
                <label className="label">Nom</label>
                <input
                  type="text"
                  value={profileForm.last_name}
                  onChange={(e) => setProfileForm({ ...profileForm, last_name: e.target.value })}
                  className="input"
                />
              </div>
              <div>
                <label className="label">Email</label>
                <input
                  type="email"
                  value={profileForm.email}
                  onChange={(e) => setProfileForm({ ...profileForm, email: e.target.value })}
                  className="input"
                />
              </div>
              <div>
                <label className="label">Telephone</label>
                <input
                  type="tel"
                  value={profileForm.phone}
                  onChange={(e) => setProfileForm({ ...profileForm, phone: e.target.value })}
                  className="input"
                />
              </div>
            </div>
            <div className="flex justify-end mt-6">
              <button
                onClick={handleSaveProfile}
                disabled={savingProfile}
                className="btn-primary"
              >
                {savingProfile ? 'Enregistrement...' : 'Enregistrer le profil'}
              </button>
            </div>
          </div>

          <div className="card">
            <h2 className="text-lg font-semibold mb-4">Changer le mot de passe</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div>
                <label className="label">Mot de passe actuel</label>
                <input
                  type="password"
                  value={passwordForm.current_password}
                  onChange={(e) => setPasswordForm({ ...passwordForm, current_password: e.target.value })}
                  className="input"
                />
              </div>
              <div>
                <label className="label">Nouveau mot de passe</label>
                <input
                  type="password"
                  value={passwordForm.new_password}
                  onChange={(e) => setPasswordForm({ ...passwordForm, new_password: e.target.value })}
                  className="input"
                />
              </div>
              <div>
                <label className="label">Confirmer le mot de passe</label>
                <input
                  type="password"
                  value={passwordForm.confirm_password}
                  onChange={(e) => setPasswordForm({ ...passwordForm, confirm_password: e.target.value })}
                  className="input"
                />
              </div>
            </div>
            <div className="flex justify-end mt-6">
              <button
                onClick={handleChangePassword}
                disabled={changingPassword || !passwordForm.current_password || !passwordForm.new_password}
                className="btn-primary"
              >
                {changingPassword ? 'Changement...' : 'Changer le mot de passe'}
              </button>
            </div>
          </div>

          <div className="card bg-gray-50">
            <h2 className="text-lg font-semibold mb-2">Informations du compte</h2>
            <div className="text-sm text-gray-600 space-y-1">
              <p><span className="font-medium">Derniere connexion:</span> {user?.last_login ? new Date(user.last_login).toLocaleString('fr-BE') : 'Jamais'}</p>
              <p><span className="font-medium">Compte cree le:</span> {user?.created_at ? new Date(user.created_at).toLocaleString('fr-BE') : '-'}</p>
            </div>
          </div>
        </div>
      )}

      <form onSubmit={handleSubmit(onSubmit)}>
        {activeTab === 'company' && (
          <div className="card">
            <h2 className="text-lg font-semibold mb-4">Informations societe</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="md:col-span-2">
                <label className="label">Nom de la societe</label>
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
                <label className="label">Numero de TVA</label>
                <input {...register('vat_number')} className="input" />
              </div>
              <div>
                <label className="label">Telephone</label>
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
            <h2 className="text-lg font-semibold mb-4">Parametres de facturation</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="label">Format numerotation</label>
                <input
                  {...register('invoice_number_format')}
                  className="input"
                  placeholder="YYYY-0001"
                />
              </div>
              <div>
                <label className="label">Delai de paiement (jours)</label>
                <input
                  type="number"
                  {...register('default_payment_terms', { valueAsNumber: true })}
                  className="input"
                />
              </div>
              <div>
                <label className="label">Taux TVA par defaut (%)</label>
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
                <label className="label">Mentions legales (pied de facture)</label>
                <textarea {...register('legal_mentions')} className="input" rows={3} />
              </div>
              <div className="md:col-span-2">
                <label className="label">Conditions generales</label>
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
                <label className="label">Email expediteur</label>
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

        {!['expense_types', 'account'].includes(activeTab) && (
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
