import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { crmApi, clientsApi } from '../services/api'
import {
  PlusIcon,
  UserPlusIcon,
  CheckIcon,
  PhoneIcon,
  EnvelopeIcon,
  CalendarIcon,
  FunnelIcon,
} from '@heroicons/react/24/outline'
import toast from 'react-hot-toast'

interface Opportunity {
  id: number
  name: string
  client_id: number | null
  client_name: string | null
  contact_name: string
  contact_email: string | null
  contact_phone: string | null
  stage: string
  estimated_value: number
  probability: number
  expected_close_date: string | null
  source: string | null
  notes: string | null
  created_at: string
}

interface Task {
  id: number
  title: string
  client_name: string | null
  opportunity_name: string | null
  due_date: string | null
  priority: string
  status: string
}

interface Activity {
  id: number
  activity_type: string
  subject: string
  client_name: string | null
  created_at: string
}

interface PipelineStage {
  stage: string
  count: number
  total_value: number
}

const stageMap: Record<string, { label: string; color: string }> = {
  PROSPECT: { label: 'Prospect', color: 'bg-gray-100' },
  QUALIFICATION: { label: 'Qualification', color: 'bg-blue-100' },
  PROPOSITION: { label: 'Proposition', color: 'bg-yellow-100' },
  NEGOCIATION: { label: 'Negociation', color: 'bg-orange-100' },
  GAGNE: { label: 'Gagne', color: 'bg-green-100' },
  PERDU: { label: 'Perdu', color: 'bg-red-100' },
}

const activityTypes: Record<string, { label: string; icon: any }> = {
  APPEL: { label: 'Appel', icon: PhoneIcon },
  EMAIL: { label: 'Email', icon: EnvelopeIcon },
  REUNION: { label: 'Reunion', icon: CalendarIcon },
  NOTE: { label: 'Note', icon: null },
}

const priorityColors: Record<string, string> = {
  BASSE: 'bg-gray-100 text-gray-800',
  NORMALE: 'bg-blue-100 text-blue-800',
  HAUTE: 'bg-orange-100 text-orange-800',
  URGENTE: 'bg-red-100 text-red-800',
}

type ViewMode = 'pipeline' | 'list' | 'tasks' | 'activities'

export default function CRM() {
  const [viewMode, setViewMode] = useState<ViewMode>('pipeline')
  const [opportunities, setOpportunities] = useState<Opportunity[]>([])
  const [tasks, setTasks] = useState<Task[]>([])
  const [activities, setActivities] = useState<Activity[]>([])
  const [pipeline, setPipeline] = useState<PipelineStage[]>([])
  const [loading, setLoading] = useState(true)

  const [showAddOpportunity, setShowAddOpportunity] = useState(false)
  const [showAddTask, setShowAddTask] = useState(false)
  const [showAddActivity, setShowAddActivity] = useState(false)

  const [clients, setClients] = useState<{ id: number; name: string }[]>([])

  const [opportunityForm, setOpportunityForm] = useState({
    name: '',
    client_id: '',
    prospect_contact: '',
    prospect_email: '',
    prospect_phone: '',
    estimated_value: 0,
    probability: 50,
    estimated_close_date: '',
    source: '',
    description: '',
  })

  const [taskForm, setTaskForm] = useState({
    title: '',
    description: '',
    client_id: '',
    opportunity_id: '',
    due_date: '',
    priority: 'NORMALE',
  })

  const [activityForm, setActivityForm] = useState({
    client_id: '',
    opportunity_id: '',
    activity_type: 'NOTE',
    subject: '',
    notes: '',
  })

  useEffect(() => {
    loadClients()
    loadData()
  }, [])

  useEffect(() => {
    loadData()
  }, [viewMode])

  const loadClients = async () => {
    try {
      const response = await clientsApi.list({ is_active: true })
      setClients(response.data)
    } catch (error) {
      console.error('Error loading clients:', error)
    }
  }

  const loadData = async () => {
    setLoading(true)
    try {
      const [oppsRes, pipelineRes, tasksRes, activitiesRes] = await Promise.all([
        crmApi.opportunities.list(),
        crmApi.pipeline(),
        crmApi.tasks.list(),
        crmApi.activities.list(),
      ])

      setOpportunities(oppsRes.data)
      setPipeline(pipelineRes.data)
      setTasks(tasksRes.data)
      setActivities(activitiesRes.data)
    } catch (error) {
      toast.error('Erreur lors du chargement')
    } finally {
      setLoading(false)
    }
  }

  const handleAddOpportunity = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await crmApi.opportunities.create({
        ...opportunityForm,
        client_id: opportunityForm.client_id ? parseInt(opportunityForm.client_id) : null,
        estimated_close_date: opportunityForm.estimated_close_date || null,
      })
      toast.success('Opportunite creee')
      setShowAddOpportunity(false)
      setOpportunityForm({
        name: '',
        client_id: '',
        prospect_contact: '',
        prospect_email: '',
        prospect_phone: '',
        estimated_value: 0,
        probability: 50,
        estimated_close_date: '',
        source: '',
        description: '',
      })
      loadData()
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Erreur')
    }
  }

  const handleAddTask = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await crmApi.tasks.create({
        ...taskForm,
        client_id: taskForm.client_id ? parseInt(taskForm.client_id) : null,
        opportunity_id: taskForm.opportunity_id ? parseInt(taskForm.opportunity_id) : null,
        due_date: taskForm.due_date || null,
      })
      toast.success('Tache creee')
      setShowAddTask(false)
      setTaskForm({
        title: '',
        description: '',
        client_id: '',
        opportunity_id: '',
        due_date: '',
        priority: 'NORMALE',
      })
      loadData()
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Erreur')
    }
  }

  const handleAddActivity = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await crmApi.activities.create({
        ...activityForm,
        client_id: activityForm.client_id ? parseInt(activityForm.client_id) : null,
        opportunity_id: activityForm.opportunity_id ? parseInt(activityForm.opportunity_id) : null,
      })
      toast.success('Activite enregistree')
      setShowAddActivity(false)
      setActivityForm({
        client_id: '',
        opportunity_id: '',
        activity_type: 'NOTE',
        subject: '',
        notes: '',
      })
      loadData()
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Erreur')
    }
  }

  const handleCompleteTask = async (id: number) => {
    try {
      await crmApi.tasks.complete(id)
      toast.success('Tache terminee')
      loadData()
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Erreur')
    }
  }

  const handleUpdateStage = async (id: number, stage: string) => {
    try {
      await crmApi.opportunities.updateStage(id, stage)
      toast.success('Etape mise a jour')
      loadData()
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Erreur')
    }
  }

  const handleConvertToClient = async (id: number) => {
    try {
      await crmApi.convertToClient(id)
      toast.success('Prospect converti en client')
      loadData()
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

  const getOpportunitiesByStage = (stage: string) => {
    return opportunities.filter(o => o.stage === stage)
  }

  // Calculate stats
  const totalPipelineValue = pipeline
    .filter(p => !['GAGNE', 'PERDU'].includes(p.stage))
    .reduce((sum, p) => sum + p.total_value, 0)
  const activeOpportunities = opportunities.filter(o => !['GAGNE', 'PERDU'].includes(o.stage)).length
  const pendingTasks = tasks.length

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
        <h1 className="page-title mb-0">CRM & Pipeline</h1>
        <div className="flex gap-2">
          <button
            onClick={() => setShowAddActivity(true)}
            className="btn-secondary flex items-center"
          >
            <PhoneIcon className="h-5 w-5 mr-1" />
            Activite
          </button>
          <button
            onClick={() => setShowAddTask(true)}
            className="btn-secondary flex items-center"
          >
            <CalendarIcon className="h-5 w-5 mr-1" />
            Tache
          </button>
          <button
            onClick={() => setShowAddOpportunity(true)}
            className="btn-primary flex items-center"
          >
            <PlusIcon className="h-5 w-5 mr-1" />
            Opportunite
          </button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="card bg-blue-50">
          <p className="text-sm text-gray-600">Opportunites actives</p>
          <p className="text-2xl font-bold text-blue-600">{activeOpportunities}</p>
        </div>
        <div className="card bg-green-50">
          <p className="text-sm text-gray-600">Valeur pipeline</p>
          <p className="text-2xl font-bold text-green-600">{formatCurrency(totalPipelineValue)}</p>
        </div>
        <div className="card bg-orange-50">
          <p className="text-sm text-gray-600">Taches en attente</p>
          <p className="text-2xl font-bold text-orange-600">{pendingTasks}</p>
        </div>
        <div className="card bg-purple-50">
          <p className="text-sm text-gray-600">Activites (7j)</p>
          <p className="text-2xl font-bold text-purple-600">{activities.length}</p>
        </div>
      </div>

      {/* View Mode Tabs */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="-mb-px flex space-x-8">
          {[
            { id: 'pipeline', label: 'Pipeline' },
            { id: 'list', label: 'Liste' },
            { id: 'tasks', label: `Taches (${pendingTasks})` },
            { id: 'activities', label: 'Activites' },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setViewMode(tab.id as ViewMode)}
              className={`whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm ${
                viewMode === tab.id
                  ? 'border-primary-500 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Pipeline View */}
      {viewMode === 'pipeline' && (
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          {['PROSPECT', 'QUALIFICATION', 'PROPOSITION', 'NEGOCIATION', 'GAGNE'].map((stage) => (
            <div key={stage} className={`rounded-lg p-4 ${stageMap[stage]?.color || 'bg-gray-100'}`}>
              <div className="flex justify-between items-center mb-3">
                <h3 className="font-semibold">{stageMap[stage]?.label}</h3>
                <span className="text-sm text-gray-600">
                  {getOpportunitiesByStage(stage).length}
                </span>
              </div>
              <div className="space-y-2">
                {getOpportunitiesByStage(stage).map((opp) => (
                  <div
                    key={opp.id}
                    className="bg-white rounded-lg p-3 shadow-sm cursor-pointer hover:shadow-md transition-shadow"
                  >
                    <div className="font-medium text-sm mb-1">{opp.name}</div>
                    <div className="text-xs text-gray-500 mb-2">
                      {opp.client_name || opp.contact_name}
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm font-semibold text-green-600">
                        {formatCurrency(opp.estimated_value)}
                      </span>
                      <span className="text-xs text-gray-500">
                        {opp.probability}%
                      </span>
                    </div>
                    {stage !== 'GAGNE' && stage !== 'PERDU' && (
                      <div className="mt-2 flex gap-1">
                        {stage === 'PROSPECT' && !opp.client_id && (
                          <button
                            onClick={() => handleConvertToClient(opp.id)}
                            className="text-xs text-blue-600 hover:text-blue-800"
                            title="Convertir en client"
                          >
                            <UserPlusIcon className="h-4 w-4" />
                          </button>
                        )}
                        <select
                          value={stage}
                          onChange={(e) => handleUpdateStage(opp.id, e.target.value)}
                          className="text-xs border rounded px-1 py-0.5"
                        >
                          {Object.entries(stageMap).map(([key, { label }]) => (
                            <option key={key} value={key}>{label}</option>
                          ))}
                        </select>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* List View */}
      {viewMode === 'list' && (
        <div className="card">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead>
                <tr>
                  <th className="table-header px-6 py-3">Nom</th>
                  <th className="table-header px-6 py-3">Contact</th>
                  <th className="table-header px-6 py-3">Etape</th>
                  <th className="table-header px-6 py-3 text-right">Valeur</th>
                  <th className="table-header px-6 py-3">Probabilite</th>
                  <th className="table-header px-6 py-3">Date cloture</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {opportunities.map((opp) => (
                  <tr key={opp.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4">
                      <Link to={`/crm/opportunities/${opp.id}`} className="font-medium text-primary-600 hover:text-primary-800">
                        {opp.name}
                      </Link>
                    </td>
                    <td className="px-6 py-4">
                      <div>{opp.client_name || opp.contact_name}</div>
                      {opp.contact_email && (
                        <div className="text-xs text-gray-500">{opp.contact_email}</div>
                      )}
                    </td>
                    <td className="px-6 py-4">
                      <span className={`px-2 py-1 text-xs font-medium rounded-full ${stageMap[opp.stage]?.color}`}>
                        {stageMap[opp.stage]?.label}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-right font-semibold text-green-600">
                      {formatCurrency(opp.estimated_value)}
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center">
                        <div className="w-16 bg-gray-200 rounded-full h-2 mr-2">
                          <div
                            className="bg-primary-600 h-2 rounded-full"
                            style={{ width: `${opp.probability}%` }}
                          />
                        </div>
                        <span className="text-sm">{opp.probability}%</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {opp.expected_close_date ? formatDate(opp.expected_close_date) : '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tasks View */}
      {viewMode === 'tasks' && (
        <div className="card">
          <div className="space-y-3">
            {tasks.map((task) => (
              <div
                key={task.id}
                className="flex items-center justify-between p-4 bg-gray-50 rounded-lg"
              >
                <div className="flex items-center gap-3">
                  <button
                    onClick={() => handleCompleteTask(task.id)}
                    className="p-1 rounded-full border-2 border-gray-300 hover:border-green-500 hover:bg-green-50"
                  >
                    <CheckIcon className="h-4 w-4 text-gray-400" />
                  </button>
                  <div>
                    <div className="font-medium">{task.title}</div>
                    <div className="text-sm text-gray-500">
                      {task.client_name || task.opportunity_name || 'Sans liaison'}
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <span className={`px-2 py-1 text-xs font-medium rounded-full ${priorityColors[task.priority]}`}>
                    {task.priority}
                  </span>
                  {task.due_date && (
                    <span className="text-sm text-gray-500">
                      {formatDate(task.due_date)}
                    </span>
                  )}
                </div>
              </div>
            ))}
            {tasks.length === 0 && (
              <p className="text-center py-8 text-gray-500">
                Aucune tache en attente
              </p>
            )}
          </div>
        </div>
      )}

      {/* Activities View */}
      {viewMode === 'activities' && (
        <div className="card">
          <div className="space-y-3">
            {activities.map((activity) => {
              const ActivityIcon = activityTypes[activity.activity_type]?.icon || FunnelIcon
              return (
                <div
                  key={activity.id}
                  className="flex items-start gap-3 p-4 bg-gray-50 rounded-lg"
                >
                  <div className="p-2 bg-white rounded-full">
                    <ActivityIcon className="h-5 w-5 text-gray-600" />
                  </div>
                  <div className="flex-1">
                    <div className="font-medium">{activity.subject}</div>
                    <div className="text-sm text-gray-500">
                      {activityTypes[activity.activity_type]?.label} - {activity.client_name || 'Sans client'}
                    </div>
                  </div>
                  <div className="text-sm text-gray-500">
                    {formatDate(activity.created_at)}
                  </div>
                </div>
              )
            })}
            {activities.length === 0 && (
              <p className="text-center py-8 text-gray-500">
                Aucune activite recente
              </p>
            )}
          </div>
        </div>
      )}

      {/* Add Opportunity Modal */}
      {showAddOpportunity && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-lg max-h-[90vh] overflow-y-auto">
            <h2 className="text-lg font-semibold mb-4">Nouvelle opportunite</h2>
            <form onSubmit={handleAddOpportunity} className="space-y-4">
              <div>
                <label className="label">Nom de l'opportunite *</label>
                <input
                  type="text"
                  value={opportunityForm.name}
                  onChange={(e) => setOpportunityForm({ ...opportunityForm, name: e.target.value })}
                  className="input"
                  required
                />
              </div>
              <div>
                <label className="label">Client existant</label>
                <select
                  value={opportunityForm.client_id}
                  onChange={(e) => setOpportunityForm({ ...opportunityForm, client_id: e.target.value })}
                  className="input"
                >
                  <option value="">Nouveau prospect</option>
                  {clients.map((c) => (
                    <option key={c.id} value={c.id}>{c.name}</option>
                  ))}
                </select>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="label">Nom du contact *</label>
                  <input
                    type="text"
                    value={opportunityForm.prospect_contact}
                    onChange={(e) => setOpportunityForm({ ...opportunityForm, prospect_contact: e.target.value })}
                    className="input"
                    required
                  />
                </div>
                <div>
                  <label className="label">Email</label>
                  <input
                    type="email"
                    value={opportunityForm.prospect_email}
                    onChange={(e) => setOpportunityForm({ ...opportunityForm, prospect_email: e.target.value })}
                    className="input"
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="label">Valeur estimee</label>
                  <input
                    type="number"
                    min="0"
                    step="100"
                    value={opportunityForm.estimated_value}
                    onChange={(e) => setOpportunityForm({ ...opportunityForm, estimated_value: parseFloat(e.target.value) })}
                    className="input"
                  />
                </div>
                <div>
                  <label className="label">Probabilite (%)</label>
                  <input
                    type="number"
                    min="0"
                    max="100"
                    value={opportunityForm.probability}
                    onChange={(e) => setOpportunityForm({ ...opportunityForm, probability: parseInt(e.target.value) })}
                    className="input"
                  />
                </div>
              </div>
              <div>
                <label className="label">Date de cloture prevue</label>
                <input
                  type="date"
                  value={opportunityForm.estimated_close_date}
                  onChange={(e) => setOpportunityForm({ ...opportunityForm, estimated_close_date: e.target.value })}
                  className="input"
                />
              </div>
              <div>
                <label className="label">Source</label>
                <input
                  type="text"
                  value={opportunityForm.source}
                  onChange={(e) => setOpportunityForm({ ...opportunityForm, source: e.target.value })}
                  className="input"
                  placeholder="Ex: Site web, Recommandation, Salon..."
                />
              </div>
              <div className="flex justify-end gap-2 pt-4">
                <button type="button" onClick={() => setShowAddOpportunity(false)} className="btn-secondary">
                  Annuler
                </button>
                <button type="submit" className="btn-primary">Creer</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Add Task Modal */}
      {showAddTask && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h2 className="text-lg font-semibold mb-4">Nouvelle tache</h2>
            <form onSubmit={handleAddTask} className="space-y-4">
              <div>
                <label className="label">Titre *</label>
                <input
                  type="text"
                  value={taskForm.title}
                  onChange={(e) => setTaskForm({ ...taskForm, title: e.target.value })}
                  className="input"
                  required
                />
              </div>
              <div>
                <label className="label">Client</label>
                <select
                  value={taskForm.client_id}
                  onChange={(e) => setTaskForm({ ...taskForm, client_id: e.target.value })}
                  className="input"
                >
                  <option value="">Aucun</option>
                  {clients.map((c) => (
                    <option key={c.id} value={c.id}>{c.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="label">Opportunite</label>
                <select
                  value={taskForm.opportunity_id}
                  onChange={(e) => setTaskForm({ ...taskForm, opportunity_id: e.target.value })}
                  className="input"
                >
                  <option value="">Aucune</option>
                  {opportunities.map((o) => (
                    <option key={o.id} value={o.id}>{o.name}</option>
                  ))}
                </select>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="label">Echeance</label>
                  <input
                    type="date"
                    value={taskForm.due_date}
                    onChange={(e) => setTaskForm({ ...taskForm, due_date: e.target.value })}
                    className="input"
                  />
                </div>
                <div>
                  <label className="label">Priorite</label>
                  <select
                    value={taskForm.priority}
                    onChange={(e) => setTaskForm({ ...taskForm, priority: e.target.value })}
                    className="input"
                  >
                    <option value="BASSE">Basse</option>
                    <option value="NORMALE">Normale</option>
                    <option value="HAUTE">Haute</option>
                    <option value="URGENTE">Urgente</option>
                  </select>
                </div>
              </div>
              <div className="flex justify-end gap-2 pt-4">
                <button type="button" onClick={() => setShowAddTask(false)} className="btn-secondary">
                  Annuler
                </button>
                <button type="submit" className="btn-primary">Creer</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Add Activity Modal */}
      {showAddActivity && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h2 className="text-lg font-semibold mb-4">Nouvelle activite</h2>
            <form onSubmit={handleAddActivity} className="space-y-4">
              <div>
                <label className="label">Type *</label>
                <select
                  value={activityForm.activity_type}
                  onChange={(e) => setActivityForm({ ...activityForm, activity_type: e.target.value })}
                  className="input"
                >
                  <option value="APPEL">Appel</option>
                  <option value="EMAIL">Email</option>
                  <option value="REUNION">Reunion</option>
                  <option value="NOTE">Note</option>
                </select>
              </div>
              <div>
                <label className="label">Sujet *</label>
                <input
                  type="text"
                  value={activityForm.subject}
                  onChange={(e) => setActivityForm({ ...activityForm, subject: e.target.value })}
                  className="input"
                  required
                />
              </div>
              <div>
                <label className="label">Client</label>
                <select
                  value={activityForm.client_id}
                  onChange={(e) => setActivityForm({ ...activityForm, client_id: e.target.value })}
                  className="input"
                >
                  <option value="">Aucun</option>
                  {clients.map((c) => (
                    <option key={c.id} value={c.id}>{c.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="label">Notes</label>
                <textarea
                  value={activityForm.notes}
                  onChange={(e) => setActivityForm({ ...activityForm, notes: e.target.value })}
                  className="input"
                  rows={3}
                />
              </div>
              <div className="flex justify-end gap-2 pt-4">
                <button type="button" onClick={() => setShowAddActivity(false)} className="btn-secondary">
                  Annuler
                </button>
                <button type="submit" className="btn-primary">Enregistrer</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
