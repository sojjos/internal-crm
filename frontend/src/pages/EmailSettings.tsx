import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { emailsApi } from '../services/api'
import toast from 'react-hot-toast'
import {
  PlusIcon,
  PencilIcon,
  TrashIcon,
  CheckCircleIcon,
  XCircleIcon,
  ArrowPathIcon,
} from '@heroicons/react/24/outline'

interface EmailAccount {
  id: number
  name: string
  email_address: string
  account_type: string
  is_default: boolean
  is_active: boolean
  imap_host: string
  imap_port: number
  imap_ssl: boolean
  imap_username: string
  smtp_host: string
  smtp_port: number
  smtp_ssl: boolean
  smtp_tls: boolean
  smtp_username: string
  default_cc: string | null
  default_bcc: string | null
  request_read_receipt: boolean
  signature_html: string | null
  signature_text: string | null
  last_sync_at: string | null
}

interface AccountForm {
  name: string
  email_address: string
  account_type: string
  is_default: boolean
  imap_host: string
  imap_port: number
  imap_ssl: boolean
  imap_username: string
  imap_password: string
  smtp_host: string
  smtp_port: number
  smtp_ssl: boolean
  smtp_tls: boolean
  smtp_username: string
  smtp_password: string
  default_cc: string
  default_bcc: string
  request_read_receipt: boolean
  signature_text: string
}

const defaultForm: AccountForm = {
  name: '',
  email_address: '',
  account_type: 'personal',
  is_default: false,
  imap_host: '',
  imap_port: 993,
  imap_ssl: true,
  imap_username: '',
  imap_password: '',
  smtp_host: '',
  smtp_port: 587,
  smtp_ssl: false,
  smtp_tls: true,
  smtp_username: '',
  smtp_password: '',
  default_cc: '',
  default_bcc: '',
  request_read_receipt: false,
  signature_text: '',
}

// Common email provider presets
const providerPresets: { [key: string]: Partial<AccountForm> } = {
  gmail: {
    imap_host: 'imap.gmail.com',
    imap_port: 993,
    imap_ssl: true,
    smtp_host: 'smtp.gmail.com',
    smtp_port: 587,
    smtp_ssl: false,
    smtp_tls: true,
  },
  outlook: {
    imap_host: 'outlook.office365.com',
    imap_port: 993,
    imap_ssl: true,
    smtp_host: 'smtp.office365.com',
    smtp_port: 587,
    smtp_ssl: false,
    smtp_tls: true,
  },
  ovh: {
    imap_host: 'ssl0.ovh.net',
    imap_port: 993,
    imap_ssl: true,
    smtp_host: 'ssl0.ovh.net',
    smtp_port: 587,
    smtp_ssl: false,
    smtp_tls: true,
  },
}

export default function EmailSettings() {
  const navigate = useNavigate()
  const [accounts, setAccounts] = useState<EmailAccount[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [form, setForm] = useState<AccountForm>(defaultForm)
  const [testing, setTesting] = useState(false)
  const [testResult, setTestResult] = useState<any>(null)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    loadAccounts()
  }, [])

  const loadAccounts = async () => {
    try {
      const response = await emailsApi.accounts.list()
      setAccounts(response.data)
    } catch (error) {
      toast.error('Erreur de chargement')
    } finally {
      setLoading(false)
    }
  }

  const handleEdit = (account: EmailAccount) => {
    setEditingId(account.id)
    setForm({
      name: account.name,
      email_address: account.email_address,
      account_type: account.account_type,
      is_default: account.is_default,
      imap_host: account.imap_host,
      imap_port: account.imap_port,
      imap_ssl: account.imap_ssl,
      imap_username: account.imap_username,
      imap_password: '', // Don't show password
      smtp_host: account.smtp_host,
      smtp_port: account.smtp_port,
      smtp_ssl: account.smtp_ssl,
      smtp_tls: account.smtp_tls,
      smtp_username: account.smtp_username,
      smtp_password: '', // Don't show password
      default_cc: account.default_cc || '',
      default_bcc: account.default_bcc || '',
      request_read_receipt: account.request_read_receipt,
      signature_text: account.signature_text || '',
    })
    setShowForm(true)
    setTestResult(null)
  }

  const handleDelete = async (id: number) => {
    if (!confirm('Supprimer ce compte email ?')) return

    try {
      await emailsApi.accounts.delete(id)
      setAccounts(accounts.filter(a => a.id !== id))
      toast.success('Compte supprimé')
    } catch (error) {
      toast.error('Erreur de suppression')
    }
  }

  const applyPreset = (provider: string) => {
    const preset = providerPresets[provider]
    if (preset) {
      setForm(prev => ({ ...prev, ...preset }))
    }
  }

  const testConnection = async () => {
    setTesting(true)
    setTestResult(null)

    try {
      const response = await emailsApi.accounts.test({
        imap_host: form.imap_host,
        imap_port: form.imap_port,
        imap_ssl: form.imap_ssl,
        imap_username: form.imap_username,
        imap_password: form.imap_password,
        smtp_host: form.smtp_host,
        smtp_port: form.smtp_port,
        smtp_ssl: form.smtp_ssl,
        smtp_tls: form.smtp_tls,
        smtp_username: form.smtp_username,
        smtp_password: form.smtp_password,
      })
      setTestResult(response.data)
    } catch (error: any) {
      setTestResult({
        imap_success: false,
        smtp_success: false,
        imap_error: 'Erreur de test',
        smtp_error: 'Erreur de test',
      })
    } finally {
      setTesting(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSaving(true)

    try {
      if (editingId) {
        // Update - only send password if changed
        const updateData: any = { ...form }
        if (!updateData.imap_password) delete updateData.imap_password
        if (!updateData.smtp_password) delete updateData.smtp_password

        await emailsApi.accounts.update(editingId, updateData)
        toast.success('Compte mis à jour')
      } else {
        // Create
        await emailsApi.accounts.create(form)
        toast.success('Compte créé')
      }

      loadAccounts()
      setShowForm(false)
      setEditingId(null)
      setForm(defaultForm)
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Erreur')
    } finally {
      setSaving(false)
    }
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
        <h1 className="page-title">Configuration Email</h1>
        {!showForm && (
          <button
            onClick={() => {
              setShowForm(true)
              setEditingId(null)
              setForm(defaultForm)
              setTestResult(null)
            }}
            className="btn-primary flex items-center gap-2"
          >
            <PlusIcon className="h-5 w-5" />
            Ajouter un compte
          </button>
        )}
      </div>

      {showForm ? (
        <div className="card max-w-3xl">
          <h2 className="text-lg font-semibold mb-4">
            {editingId ? 'Modifier le compte' : 'Nouveau compte email'}
          </h2>

          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Provider presets */}
            <div>
              <label className="label">Configuration rapide</label>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => applyPreset('gmail')}
                  className="px-3 py-1 text-sm border rounded hover:bg-gray-50"
                >
                  Gmail
                </button>
                <button
                  type="button"
                  onClick={() => applyPreset('outlook')}
                  className="px-3 py-1 text-sm border rounded hover:bg-gray-50"
                >
                  Outlook / Office 365
                </button>
                <button
                  type="button"
                  onClick={() => applyPreset('ovh')}
                  className="px-3 py-1 text-sm border rounded hover:bg-gray-50"
                >
                  OVH
                </button>
              </div>
            </div>

            {/* Basic info */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="label">Nom du compte</label>
                <input
                  type="text"
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  className="input"
                  placeholder="Mon email pro"
                  required
                />
              </div>
              <div>
                <label className="label">Adresse email</label>
                <input
                  type="email"
                  value={form.email_address}
                  onChange={(e) => setForm({ ...form, email_address: e.target.value })}
                  className="input"
                  placeholder="email@exemple.com"
                  required
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="label">Type de compte</label>
                <select
                  value={form.account_type}
                  onChange={(e) => setForm({ ...form, account_type: e.target.value })}
                  className="input"
                >
                  <option value="personal">Personnel</option>
                  <option value="company">Entreprise (pour factures)</option>
                </select>
              </div>
              <div className="flex items-center pt-6">
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={form.is_default}
                    onChange={(e) => setForm({ ...form, is_default: e.target.checked })}
                    className="rounded"
                  />
                  Compte par défaut
                </label>
              </div>
            </div>

            {/* IMAP settings */}
            <div className="border-t pt-4">
              <h3 className="font-medium mb-3">Serveur de réception (IMAP)</h3>
              <div className="grid grid-cols-3 gap-4">
                <div className="col-span-2">
                  <label className="label">Serveur IMAP</label>
                  <input
                    type="text"
                    value={form.imap_host}
                    onChange={(e) => setForm({ ...form, imap_host: e.target.value })}
                    className="input"
                    placeholder="imap.exemple.com"
                    required
                  />
                </div>
                <div>
                  <label className="label">Port</label>
                  <input
                    type="number"
                    value={form.imap_port}
                    onChange={(e) => setForm({ ...form, imap_port: Number(e.target.value) })}
                    className="input"
                    required
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4 mt-3">
                <div>
                  <label className="label">Nom d'utilisateur</label>
                  <input
                    type="text"
                    value={form.imap_username}
                    onChange={(e) => setForm({ ...form, imap_username: e.target.value })}
                    className="input"
                    placeholder="email@exemple.com"
                    required
                  />
                </div>
                <div>
                  <label className="label">Mot de passe</label>
                  <input
                    type="password"
                    value={form.imap_password}
                    onChange={(e) => setForm({ ...form, imap_password: e.target.value })}
                    className="input"
                    placeholder={editingId ? '(inchangé)' : ''}
                    required={!editingId}
                  />
                </div>
              </div>
              <div className="mt-2">
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={form.imap_ssl}
                    onChange={(e) => setForm({ ...form, imap_ssl: e.target.checked })}
                    className="rounded"
                  />
                  Utiliser SSL
                </label>
              </div>
            </div>

            {/* SMTP settings */}
            <div className="border-t pt-4">
              <h3 className="font-medium mb-3">Serveur d'envoi (SMTP)</h3>
              <div className="grid grid-cols-3 gap-4">
                <div className="col-span-2">
                  <label className="label">Serveur SMTP</label>
                  <input
                    type="text"
                    value={form.smtp_host}
                    onChange={(e) => setForm({ ...form, smtp_host: e.target.value })}
                    className="input"
                    placeholder="smtp.exemple.com"
                    required
                  />
                </div>
                <div>
                  <label className="label">Port</label>
                  <input
                    type="number"
                    value={form.smtp_port}
                    onChange={(e) => setForm({ ...form, smtp_port: Number(e.target.value) })}
                    className="input"
                    required
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4 mt-3">
                <div>
                  <label className="label">Nom d'utilisateur</label>
                  <input
                    type="text"
                    value={form.smtp_username}
                    onChange={(e) => setForm({ ...form, smtp_username: e.target.value })}
                    className="input"
                    placeholder="email@exemple.com"
                    required
                  />
                </div>
                <div>
                  <label className="label">Mot de passe</label>
                  <input
                    type="password"
                    value={form.smtp_password}
                    onChange={(e) => setForm({ ...form, smtp_password: e.target.value })}
                    className="input"
                    placeholder={editingId ? '(inchangé)' : ''}
                    required={!editingId}
                  />
                </div>
              </div>
              <div className="mt-2 flex gap-4">
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={form.smtp_ssl}
                    onChange={(e) => setForm({ ...form, smtp_ssl: e.target.checked })}
                    className="rounded"
                  />
                  SSL
                </label>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={form.smtp_tls}
                    onChange={(e) => setForm({ ...form, smtp_tls: e.target.checked })}
                    className="rounded"
                  />
                  STARTTLS
                </label>
              </div>
            </div>

            {/* Test connection */}
            <div className="border-t pt-4">
              <button
                type="button"
                onClick={testConnection}
                disabled={testing}
                className="btn-secondary flex items-center gap-2"
              >
                <ArrowPathIcon className={`h-5 w-5 ${testing ? 'animate-spin' : ''}`} />
                {testing ? 'Test en cours...' : 'Tester la connexion'}
              </button>

              {testResult && (
                <div className="mt-3 grid grid-cols-2 gap-4">
                  <div className={`p-3 rounded ${testResult.imap_success ? 'bg-green-50' : 'bg-red-50'}`}>
                    <div className="flex items-center gap-2">
                      {testResult.imap_success ? (
                        <CheckCircleIcon className="h-5 w-5 text-green-600" />
                      ) : (
                        <XCircleIcon className="h-5 w-5 text-red-600" />
                      )}
                      <span className={testResult.imap_success ? 'text-green-700' : 'text-red-700'}>
                        IMAP: {testResult.imap_success ? 'OK' : testResult.imap_error}
                      </span>
                    </div>
                  </div>
                  <div className={`p-3 rounded ${testResult.smtp_success ? 'bg-green-50' : 'bg-red-50'}`}>
                    <div className="flex items-center gap-2">
                      {testResult.smtp_success ? (
                        <CheckCircleIcon className="h-5 w-5 text-green-600" />
                      ) : (
                        <XCircleIcon className="h-5 w-5 text-red-600" />
                      )}
                      <span className={testResult.smtp_success ? 'text-green-700' : 'text-red-700'}>
                        SMTP: {testResult.smtp_success ? 'OK' : testResult.smtp_error}
                      </span>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Invoice settings (for company accounts) */}
            {form.account_type === 'company' && (
              <div className="border-t pt-4">
                <h3 className="font-medium mb-3">Options pour les factures</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="label">CC par défaut</label>
                    <input
                      type="text"
                      value={form.default_cc}
                      onChange={(e) => setForm({ ...form, default_cc: e.target.value })}
                      className="input"
                      placeholder="copie@exemple.com"
                    />
                    <p className="text-xs text-gray-500 mt-1">
                      Toujours en copie sur les factures
                    </p>
                  </div>
                  <div>
                    <label className="label">Cci par défaut</label>
                    <input
                      type="text"
                      value={form.default_bcc}
                      onChange={(e) => setForm({ ...form, default_bcc: e.target.value })}
                      className="input"
                      placeholder="archive@exemple.com"
                    />
                  </div>
                </div>
                <div className="mt-3">
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={form.request_read_receipt}
                      onChange={(e) => setForm({ ...form, request_read_receipt: e.target.checked })}
                      className="rounded"
                    />
                    Demander un accusé de réception par défaut
                  </label>
                </div>
              </div>
            )}

            {/* Signature */}
            <div className="border-t pt-4">
              <h3 className="font-medium mb-3">Signature</h3>
              <textarea
                value={form.signature_text}
                onChange={(e) => setForm({ ...form, signature_text: e.target.value })}
                rows={4}
                className="input"
                placeholder="Cordialement,&#10;Votre nom"
              />
            </div>

            {/* Actions */}
            <div className="flex justify-between pt-4 border-t">
              <button
                type="button"
                onClick={() => {
                  setShowForm(false)
                  setEditingId(null)
                  setForm(defaultForm)
                }}
                className="btn-secondary"
              >
                Annuler
              </button>
              <button
                type="submit"
                disabled={saving}
                className="btn-primary disabled:opacity-50"
              >
                {saving ? 'Enregistrement...' : editingId ? 'Mettre à jour' : 'Créer le compte'}
              </button>
            </div>
          </form>
        </div>
      ) : (
        <div className="space-y-4">
          {accounts.length === 0 ? (
            <div className="card text-center py-8 text-gray-500">
              Aucun compte email configuré
            </div>
          ) : (
            accounts.map(account => (
              <div key={account.id} className="card">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="font-medium">{account.name}</h3>
                      {account.is_default && (
                        <span className="text-xs bg-primary-100 text-primary-700 px-2 py-0.5 rounded">
                          Par défaut
                        </span>
                      )}
                      <span className="text-xs bg-gray-100 text-gray-700 px-2 py-0.5 rounded">
                        {account.account_type === 'company' ? 'Entreprise' : 'Personnel'}
                      </span>
                    </div>
                    <p className="text-sm text-gray-500">{account.email_address}</p>
                    <p className="text-xs text-gray-400 mt-1">
                      IMAP: {account.imap_host}:{account.imap_port} |
                      SMTP: {account.smtp_host}:{account.smtp_port}
                    </p>
                    {account.last_sync_at && (
                      <p className="text-xs text-gray-400">
                        Dernière sync: {new Date(account.last_sync_at).toLocaleString('fr-FR')}
                      </p>
                    )}
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => handleEdit(account)}
                      className="p-2 text-gray-500 hover:text-gray-700"
                    >
                      <PencilIcon className="h-5 w-5" />
                    </button>
                    <button
                      onClick={() => handleDelete(account.id)}
                      className="p-2 text-red-500 hover:text-red-700"
                    >
                      <TrashIcon className="h-5 w-5" />
                    </button>
                  </div>
                </div>
              </div>
            ))
          )}

          <div className="mt-6">
            <button
              onClick={() => navigate('/emails')}
              className="btn-secondary"
            >
              Retour à la messagerie
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
