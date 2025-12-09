import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { crmApi, clientsApi } from '../services/api'
import toast from 'react-hot-toast'

const stageOptions = [
  { value: 'PROSPECT', label: 'Prospect' },
  { value: 'QUALIFICATION', label: 'Qualification' },
  { value: 'PROPOSITION', label: 'Proposition' },
  { value: 'NEGOCIATION', label: 'Negociation' },
  { value: 'GAGNE', label: 'Gagne' },
  { value: 'PERDU', label: 'Perdu' },
]

export default function OpportunityForm() {
  const { id } = useParams()
  const navigate = useNavigate()
  const isEdit = Boolean(id)

  const [loading, setLoading] = useState(false)
  const [clients, setClients] = useState<{ id: number; name: string }[]>([])

  const [form, setForm] = useState({
    name: '',
    client_id: '',
    contact_name: '',
    contact_email: '',
    contact_phone: '',
    stage: 'PROSPECT',
    estimated_value: 0,
    probability: 50,
    expected_close_date: '',
    source: '',
    notes: '',
  })

  useEffect(() => {
    loadClients()
    if (id) {
      loadOpportunity()
    }
  }, [id])

  const loadClients = async () => {
    try {
      const response = await clientsApi.list({ is_active: true })
      setClients(response.data)
    } catch (error) {
      console.error('Error loading clients:', error)
    }
  }

  const loadOpportunity = async () => {
    setLoading(true)
    try {
      const response = await crmApi.opportunities.get(parseInt(id!))
      const data = response.data

      setForm({
        name: data.name,
        client_id: data.client_id?.toString() || '',
        contact_name: data.contact_name,
        contact_email: data.contact_email || '',
        contact_phone: data.contact_phone || '',
        stage: data.stage,
        estimated_value: data.estimated_value,
        probability: data.probability,
        expected_close_date: data.expected_close_date || '',
        source: data.source || '',
        notes: data.notes || '',
      })
    } catch (error) {
      toast.error('Erreur lors du chargement')
      navigate('/crm')
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)

    try {
      const payload = {
        ...form,
        client_id: form.client_id ? parseInt(form.client_id) : null,
        expected_close_date: form.expected_close_date || null,
        contact_email: form.contact_email || null,
        contact_phone: form.contact_phone || null,
        source: form.source || null,
        notes: form.notes || null,
      }

      if (isEdit) {
        await crmApi.opportunities.update(parseInt(id!), payload)
        toast.success('Opportunite mise a jour')
      } else {
        await crmApi.opportunities.create(payload)
        toast.success('Opportunite creee')
      }

      navigate('/crm')
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Erreur')
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async () => {
    if (!confirm('Supprimer cette opportunite ?')) return

    try {
      await crmApi.opportunities.delete(parseInt(id!))
      toast.success('Opportunite supprimee')
      navigate('/crm')
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Erreur')
    }
  }

  if (loading && isEdit) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  return (
    <div>
      <h1 className="page-title">
        {isEdit ? 'Modifier l\'opportunite' : 'Nouvelle opportunite'}
      </h1>

      <form onSubmit={handleSubmit}>
        <div className="card mb-6">
          <h2 className="text-lg font-semibold mb-4">Informations generales</h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="md:col-span-2">
              <label className="label">Nom de l'opportunite *</label>
              <input
                type="text"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                className="input"
                required
                placeholder="Ex: Projet de refonte site web"
              />
            </div>

            <div>
              <label className="label">Client existant</label>
              <select
                value={form.client_id}
                onChange={(e) => setForm({ ...form, client_id: e.target.value })}
                className="input"
              >
                <option value="">Nouveau prospect</option>
                {clients.map((c) => (
                  <option key={c.id} value={c.id}>{c.name}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="label">Etape</label>
              <select
                value={form.stage}
                onChange={(e) => setForm({ ...form, stage: e.target.value })}
                className="input"
              >
                {stageOptions.map((opt) => (
                  <option key={opt.value} value={opt.value}>{opt.label}</option>
                ))}
              </select>
            </div>
          </div>
        </div>

        <div className="card mb-6">
          <h2 className="text-lg font-semibold mb-4">Contact</h2>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="label">Nom du contact *</label>
              <input
                type="text"
                value={form.contact_name}
                onChange={(e) => setForm({ ...form, contact_name: e.target.value })}
                className="input"
                required
              />
            </div>

            <div>
              <label className="label">Email</label>
              <input
                type="email"
                value={form.contact_email}
                onChange={(e) => setForm({ ...form, contact_email: e.target.value })}
                className="input"
              />
            </div>

            <div>
              <label className="label">Telephone</label>
              <input
                type="tel"
                value={form.contact_phone}
                onChange={(e) => setForm({ ...form, contact_phone: e.target.value })}
                className="input"
              />
            </div>
          </div>
        </div>

        <div className="card mb-6">
          <h2 className="text-lg font-semibold mb-4">Details commerciaux</h2>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="label">Valeur estimee</label>
              <div className="relative">
                <input
                  type="number"
                  min="0"
                  step="100"
                  value={form.estimated_value}
                  onChange={(e) => setForm({ ...form, estimated_value: parseFloat(e.target.value) || 0 })}
                  className="input pr-8"
                />
                <span className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500">EUR</span>
              </div>
            </div>

            <div>
              <label className="label">Probabilite de reussite</label>
              <div className="flex items-center gap-2">
                <input
                  type="range"
                  min="0"
                  max="100"
                  step="5"
                  value={form.probability}
                  onChange={(e) => setForm({ ...form, probability: parseInt(e.target.value) })}
                  className="flex-1"
                />
                <span className="w-12 text-center font-medium">{form.probability}%</span>
              </div>
            </div>

            <div>
              <label className="label">Date de cloture prevue</label>
              <input
                type="date"
                value={form.expected_close_date}
                onChange={(e) => setForm({ ...form, expected_close_date: e.target.value })}
                className="input"
              />
            </div>

            <div>
              <label className="label">Source</label>
              <input
                type="text"
                value={form.source}
                onChange={(e) => setForm({ ...form, source: e.target.value })}
                className="input"
                placeholder="Ex: Site web, Recommandation, Salon..."
              />
            </div>

            <div className="md:col-span-2">
              <label className="label">Notes</label>
              <textarea
                value={form.notes}
                onChange={(e) => setForm({ ...form, notes: e.target.value })}
                className="input"
                rows={3}
                placeholder="Informations complementaires..."
              />
            </div>
          </div>
        </div>

        <div className="flex justify-between">
          <div>
            {isEdit && (
              <button
                type="button"
                onClick={handleDelete}
                className="text-red-600 hover:text-red-800"
              >
                Supprimer
              </button>
            )}
          </div>
          <div className="flex gap-4">
            <button
              type="button"
              onClick={() => navigate('/crm')}
              className="btn-secondary"
            >
              Annuler
            </button>
            <button type="submit" className="btn-primary" disabled={loading}>
              {loading ? 'Enregistrement...' : isEdit ? 'Mettre a jour' : 'Creer'}
            </button>
          </div>
        </div>
      </form>
    </div>
  )
}
