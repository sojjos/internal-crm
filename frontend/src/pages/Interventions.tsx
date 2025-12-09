import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { interventionsApi, clientsApi } from '../services/api'
import {
  PlusIcon,
  PencilIcon,
  TrashIcon,
  PlayIcon,
  CheckIcon,
  DocumentTextIcon,
  CalendarIcon,
} from '@heroicons/react/24/outline'
import toast from 'react-hot-toast'

interface Intervention {
  id: number
  reference: string
  client_id: number
  client_name: string
  title: string
  description: string | null
  scheduled_date: string
  scheduled_time: string | null
  estimated_duration: number | null
  actual_start: string | null
  actual_end: string | null
  status: string
  is_billable: boolean
  total_htva: number
  total_vat: number
  total_ttc: number
  invoice_id: number | null
}

interface CalendarEvent {
  id: number
  title: string
  client_name: string
  start: string
  end: string | null
  status: string
  is_billable: boolean
}

const statusMap: Record<string, { label: string; color: string }> = {
  PLANIFIE: { label: 'Planifie', color: 'bg-blue-100 text-blue-800' },
  EN_COURS: { label: 'En cours', color: 'bg-yellow-100 text-yellow-800' },
  TERMINE: { label: 'Termine', color: 'bg-green-100 text-green-800' },
  FACTURE: { label: 'Facture', color: 'bg-purple-100 text-purple-800' },
  ANNULE: { label: 'Annule', color: 'bg-red-100 text-red-800' },
}

type ViewMode = 'list' | 'calendar'

export default function Interventions() {
  const [interventions, setInterventions] = useState<Intervention[]>([])
  const [calendarEvents, setCalendarEvents] = useState<CalendarEvent[]>([])
  const [loading, setLoading] = useState(true)
  const [viewMode, setViewMode] = useState<ViewMode>('list')
  const [statusFilter, setStatusFilter] = useState('')
  const [clientFilter, setClientFilter] = useState('')
  const [clients, setClients] = useState<{ id: number; name: string }[]>([])

  const [selectedWeek, setSelectedWeek] = useState(() => {
    const now = new Date()
    const monday = new Date(now)
    monday.setDate(now.getDate() - now.getDay() + 1)
    return monday.toISOString().split('T')[0]
  })

  useEffect(() => {
    loadClients()
  }, [])

  useEffect(() => {
    if (viewMode === 'list') {
      loadInterventions()
    } else {
      loadCalendar()
    }
  }, [viewMode, statusFilter, clientFilter, selectedWeek])

  const loadClients = async () => {
    try {
      const response = await clientsApi.list({ is_active: true })
      setClients(response.data)
    } catch (error) {
      console.error('Error loading clients:', error)
    }
  }

  const loadInterventions = async () => {
    setLoading(true)
    try {
      const params: any = {}
      if (statusFilter) params.status = statusFilter
      if (clientFilter) params.client_id = clientFilter

      const response = await interventionsApi.list(params)
      setInterventions(response.data)
    } catch (error) {
      toast.error('Erreur lors du chargement')
    } finally {
      setLoading(false)
    }
  }

  const loadCalendar = async () => {
    setLoading(true)
    try {
      const weekStart = new Date(selectedWeek)
      const weekEnd = new Date(weekStart)
      weekEnd.setDate(weekEnd.getDate() + 6)

      const response = await interventionsApi.calendar({
        date_from: weekStart.toISOString().split('T')[0],
        date_to: weekEnd.toISOString().split('T')[0],
      })
      setCalendarEvents(response.data)
    } catch (error) {
      toast.error('Erreur lors du chargement')
    } finally {
      setLoading(false)
    }
  }

  const handleStart = async (id: number) => {
    try {
      await interventionsApi.start(id)
      toast.success('Intervention demarree')
      loadInterventions()
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Erreur')
    }
  }

  const handleComplete = async (id: number) => {
    try {
      await interventionsApi.complete(id)
      toast.success('Intervention terminee')
      loadInterventions()
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Erreur')
    }
  }

  const handleCreateInvoice = async (id: number) => {
    try {
      const response = await interventionsApi.createInvoice(id)
      toast.success('Facture creee')
      loadInterventions()
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Erreur')
    }
  }

  const handleDelete = async (id: number) => {
    if (!confirm('Supprimer cette intervention ?')) return

    try {
      await interventionsApi.delete(id)
      toast.success('Intervention supprimee')
      loadInterventions()
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

  const getWeekDays = () => {
    const days = []
    const start = new Date(selectedWeek)
    for (let i = 0; i < 7; i++) {
      const day = new Date(start)
      day.setDate(start.getDate() + i)
      days.push(day)
    }
    return days
  }

  const getEventsForDay = (date: Date) => {
    const dateStr = date.toISOString().split('T')[0]
    return calendarEvents.filter(e => e.start.startsWith(dateStr))
  }

  const navigateWeek = (direction: number) => {
    const current = new Date(selectedWeek)
    current.setDate(current.getDate() + direction * 7)
    setSelectedWeek(current.toISOString().split('T')[0])
  }

  if (loading && interventions.length === 0) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="page-title mb-0">Interventions & Planning</h1>
        <div className="flex gap-2">
          <div className="flex rounded-lg overflow-hidden border">
            <button
              onClick={() => setViewMode('list')}
              className={`px-4 py-2 ${viewMode === 'list' ? 'bg-primary-600 text-white' : 'bg-white'}`}
            >
              Liste
            </button>
            <button
              onClick={() => setViewMode('calendar')}
              className={`px-4 py-2 ${viewMode === 'calendar' ? 'bg-primary-600 text-white' : 'bg-white'}`}
            >
              Calendrier
            </button>
          </div>
          <Link to="/interventions/new" className="btn-primary flex items-center">
            <PlusIcon className="h-5 w-5 mr-1" />
            Nouvelle intervention
          </Link>
        </div>
      </div>

      {/* Filters */}
      {viewMode === 'list' && (
        <div className="card mb-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="label">Client</label>
              <select
                value={clientFilter}
                onChange={(e) => setClientFilter(e.target.value)}
                className="input"
              >
                <option value="">Tous</option>
                {clients.map((c) => (
                  <option key={c.id} value={c.id}>{c.name}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="label">Statut</label>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="input"
              >
                <option value="">Tous</option>
                {Object.entries(statusMap).map(([key, { label }]) => (
                  <option key={key} value={key}>{label}</option>
                ))}
              </select>
            </div>
          </div>
        </div>
      )}

      {/* Calendar View */}
      {viewMode === 'calendar' && (
        <div className="card mb-6">
          <div className="flex items-center justify-between mb-4">
            <button
              onClick={() => navigateWeek(-1)}
              className="btn-secondary"
            >
              Semaine precedente
            </button>
            <h2 className="text-lg font-semibold">
              Semaine du {formatDate(selectedWeek)}
            </h2>
            <button
              onClick={() => navigateWeek(1)}
              className="btn-secondary"
            >
              Semaine suivante
            </button>
          </div>

          <div className="grid grid-cols-7 gap-2">
            {getWeekDays().map((day, i) => (
              <div key={i} className="border rounded-lg overflow-hidden">
                <div className={`p-2 text-center font-medium ${
                  day.toDateString() === new Date().toDateString()
                    ? 'bg-primary-100 text-primary-800'
                    : 'bg-gray-100'
                }`}>
                  <div className="text-xs">{day.toLocaleDateString('fr-BE', { weekday: 'short' })}</div>
                  <div className="text-lg">{day.getDate()}</div>
                </div>
                <div className="p-2 min-h-[150px] space-y-1">
                  {getEventsForDay(day).map((event) => (
                    <Link
                      key={event.id}
                      to={`/interventions/${event.id}`}
                      className={`block p-1 text-xs rounded ${
                        statusMap[event.status]?.color || 'bg-gray-100'
                      }`}
                    >
                      <div className="font-medium truncate">{event.title}</div>
                      <div className="truncate text-gray-600">{event.client_name}</div>
                    </Link>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* List View */}
      {viewMode === 'list' && (
        <div className="card">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead>
                <tr>
                  <th className="table-header px-6 py-3">Reference</th>
                  <th className="table-header px-6 py-3">Client</th>
                  <th className="table-header px-6 py-3">Titre</th>
                  <th className="table-header px-6 py-3">Date</th>
                  <th className="table-header px-6 py-3">Statut</th>
                  <th className="table-header px-6 py-3 text-right">Montant</th>
                  <th className="table-header px-6 py-3">Actions</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {interventions.map((intervention) => (
                  <tr key={intervention.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap font-mono text-sm">
                      {intervention.reference}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {intervention.client_name}
                    </td>
                    <td className="px-6 py-4">
                      <div>
                        <div className="font-medium">{intervention.title}</div>
                        {intervention.description && (
                          <div className="text-xs text-gray-500 truncate max-w-xs">
                            {intervention.description}
                          </div>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <CalendarIcon className="h-4 w-4 text-gray-400 mr-1" />
                        {formatDate(intervention.scheduled_date)}
                        {intervention.scheduled_time && (
                          <span className="ml-1 text-gray-500">
                            {intervention.scheduled_time}
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                        statusMap[intervention.status]?.color || 'bg-gray-100'
                      }`}>
                        {statusMap[intervention.status]?.label || intervention.status}
                      </span>
                      {intervention.is_billable && (
                        <span className="ml-1 px-1.5 py-0.5 text-xs bg-green-100 text-green-800 rounded">
                          Facturable
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right font-medium">
                      {formatCurrency(intervention.total_ttc)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center gap-2">
                        {intervention.status === 'PLANIFIE' && (
                          <button
                            onClick={() => handleStart(intervention.id)}
                            className="text-blue-600 hover:text-blue-800"
                            title="Demarrer"
                          >
                            <PlayIcon className="h-5 w-5" />
                          </button>
                        )}
                        {intervention.status === 'EN_COURS' && (
                          <button
                            onClick={() => handleComplete(intervention.id)}
                            className="text-green-600 hover:text-green-800"
                            title="Terminer"
                          >
                            <CheckIcon className="h-5 w-5" />
                          </button>
                        )}
                        {intervention.status === 'TERMINE' && intervention.is_billable && !intervention.invoice_id && (
                          <button
                            onClick={() => handleCreateInvoice(intervention.id)}
                            className="text-purple-600 hover:text-purple-800"
                            title="Creer facture"
                          >
                            <DocumentTextIcon className="h-5 w-5" />
                          </button>
                        )}
                        {intervention.invoice_id && (
                          <Link
                            to={`/invoices/${intervention.invoice_id}`}
                            className="text-purple-600 hover:text-purple-800"
                            title="Voir facture"
                          >
                            <DocumentTextIcon className="h-5 w-5" />
                          </Link>
                        )}
                        <Link
                          to={`/interventions/${intervention.id}`}
                          className="text-primary-600 hover:text-primary-800"
                        >
                          <PencilIcon className="h-5 w-5" />
                        </Link>
                        {intervention.status === 'PLANIFIE' && (
                          <button
                            onClick={() => handleDelete(intervention.id)}
                            className="text-red-600 hover:text-red-800"
                          >
                            <TrashIcon className="h-5 w-5" />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {interventions.length === 0 && (
              <p className="text-center py-8 text-gray-500">
                Aucune intervention trouvee
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
