import { useEffect, useState } from 'react'
import { legalApi } from '../services/api'
import {
  DocumentTextIcon,
  UserGroupIcon,
  NewspaperIcon,
  BuildingLibraryIcon,
  PlusIcon,
  CheckCircleIcon,
  ClockIcon,
  DocumentArrowDownIcon,
} from '@heroicons/react/24/outline'

interface BoardMeeting {
  id: number
  meeting_type: string
  meeting_date: string
  location: string
  status: string
  attendees_count: number
  quorum_reached: boolean
  approved_at: string | null
}

interface ManagementReport {
  id: number
  fiscal_year_id: number
  fiscal_year_name: string
  report_type: string
  status: string
  created_at: string
}

interface CorporateOfficer {
  id: number
  person_type: string
  name: string
  function_type: string
  start_date: string
  end_date: string | null
  is_active: boolean
}

interface MoniteurPublication {
  id: number
  publication_type: string
  publication_date: string | null
  status: string
  reference_number: string | null
}

interface UBOEntry {
  id: number
  person_type: string
  name: string
  nationality: string
  ownership_percentage: number
  control_type: string
  declared_to_spf: boolean
}

export default function Legal() {
  const [activeTab, setActiveTab] = useState<'meetings' | 'reports' | 'officers' | 'publications' | 'ubo'>('meetings')
  const [meetings, setMeetings] = useState<BoardMeeting[]>([])
  const [reports, setReports] = useState<ManagementReport[]>([])
  const [officers, setOfficers] = useState<CorporateOfficer[]>([])
  const [publications, setPublications] = useState<MoniteurPublication[]>([])
  const [uboEntries, setUboEntries] = useState<UBOEntry[]>([])
  const [loading, setLoading] = useState(true)
  const [showMeetingModal, setShowMeetingModal] = useState(false)
  const [showOfficerModal, setShowOfficerModal] = useState(false)

  // Meeting form
  const [meetingForm, setMeetingForm] = useState({
    meeting_type: 'AG_ORDINAIRE',
    meeting_date: '',
    location: '',
    agenda: '',
  })

  // Officer form
  const [officerForm, setOfficerForm] = useState({
    person_type: 'NATURAL',
    name: '',
    function_type: 'ADMINISTRATEUR',
    national_number: '',
    company_number: '',
    start_date: '',
    address: '',
  })

  useEffect(() => {
    loadData()
  }, [activeTab])

  const loadData = async () => {
    setLoading(true)
    try {
      switch (activeTab) {
        case 'meetings':
          const meetingsRes = await legalApi.meetings.list()
          setMeetings(meetingsRes.data)
          break
        case 'reports':
          const reportsRes = await legalApi.managementReports.list()
          setReports(reportsRes.data)
          break
        case 'officers':
          const officersRes = await legalApi.officers.list()
          setOfficers(officersRes.data)
          break
        case 'publications':
          const pubsRes = await legalApi.publications.list()
          setPublications(pubsRes.data)
          break
        case 'ubo':
          const uboRes = await legalApi.ubo.list()
          setUboEntries(uboRes.data)
          break
      }
    } catch (error) {
      console.error('Failed to load data', error)
    } finally {
      setLoading(false)
    }
  }

  const handleCreateMeeting = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await legalApi.meetings.create(meetingForm)
      setShowMeetingModal(false)
      setMeetingForm({ meeting_type: 'AG_ORDINAIRE', meeting_date: '', location: '', agenda: '' })
      loadData()
    } catch (error) {
      console.error('Failed to create meeting', error)
    }
  }

  const handleCreateOfficer = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await legalApi.officers.create(officerForm)
      setShowOfficerModal(false)
      setOfficerForm({
        person_type: 'NATURAL',
        name: '',
        function_type: 'ADMINISTRATEUR',
        national_number: '',
        company_number: '',
        start_date: '',
        address: '',
      })
      loadData()
    } catch (error) {
      console.error('Failed to create officer', error)
    }
  }

  const handleGeneratePV = async (meetingId: number) => {
    try {
      const response = await legalApi.meetings.generatePv(meetingId)
      // Create download link for PDF
      const blob = new Blob([response.data], { type: 'application/pdf' })
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `pv_reunion_${meetingId}.pdf`
      a.click()
      window.URL.revokeObjectURL(url)
    } catch (error) {
      console.error('Failed to generate PV', error)
      alert('Generation du PV echouee')
    }
  }

  const handleApproveMeeting = async (meetingId: number) => {
    const president = prompt('Nom du president de seance:')
    const secretary = prompt('Nom du secretaire:')
    if (!president || !secretary) return

    try {
      await legalApi.meetings.approve(meetingId, president, secretary)
      loadData()
    } catch (error) {
      console.error('Failed to approve meeting', error)
    }
  }

  const formatDate = (dateStr: string) => {
    if (!dateStr) return '-'
    return new Date(dateStr).toLocaleDateString('fr-BE')
  }

  const getMeetingTypeLabel = (type: string) => {
    const labels: Record<string, string> = {
      AG_ORDINAIRE: 'AG Ordinaire',
      AG_EXTRAORDINAIRE: 'AG Extraordinaire',
      CA: 'Conseil d\'Administration',
      COMITE_DIRECTION: 'Comite de Direction',
    }
    return labels[type] || type
  }

  const getFunctionLabel = (func: string) => {
    const labels: Record<string, string> = {
      ADMINISTRATEUR: 'Administrateur',
      ADMINISTRATEUR_DELEGUE: 'Administrateur Delegue',
      GERANT: 'Gerant',
      PRESIDENT: 'President',
      VICE_PRESIDENT: 'Vice-President',
      SECRETAIRE: 'Secretaire',
      TRESORIER: 'Tresorier',
      COMMISSAIRE: 'Commissaire',
      LIQUIDATEUR: 'Liquidateur',
    }
    return labels[func] || func
  }

  const getStatusBadge = (status: string) => {
    const styles: Record<string, string> = {
      DRAFT: 'bg-gray-100 text-gray-800',
      BROUILLON: 'bg-gray-100 text-gray-800',
      PLANIFIE: 'bg-blue-100 text-blue-800',
      TENU: 'bg-yellow-100 text-yellow-800',
      APPROUVE: 'bg-green-100 text-green-800',
      EN_COURS: 'bg-yellow-100 text-yellow-800',
      TERMINE: 'bg-green-100 text-green-800',
      PUBLIE: 'bg-green-100 text-green-800',
      PENDING: 'bg-yellow-100 text-yellow-800',
    }
    return styles[status] || 'bg-gray-100 text-gray-800'
  }

  const tabs = [
    { id: 'meetings', label: 'Reunions & PV', icon: DocumentTextIcon },
    { id: 'reports', label: 'Rapports de Gestion', icon: NewspaperIcon },
    { id: 'officers', label: 'Mandataires', icon: UserGroupIcon },
    { id: 'publications', label: 'Moniteur Belge', icon: BuildingLibraryIcon },
    { id: 'ubo', label: 'Registre UBO', icon: UserGroupIcon },
  ]

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="page-title mb-0">Module Juridique</h1>
          <p className="text-gray-600">PV, rapports de gestion et publications</p>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="flex space-x-8">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as typeof activeTab)}
              className={`flex items-center py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab.id
                  ? 'border-primary-500 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <tab.icon className="h-5 w-5 mr-2" />
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
        </div>
      ) : (
        <>
          {/* Meetings Tab */}
          {activeTab === 'meetings' && (
            <div>
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-lg font-semibold">Reunions et Proces-Verbaux</h2>
                <button
                  onClick={() => setShowMeetingModal(true)}
                  className="btn-primary flex items-center"
                >
                  <PlusIcon className="h-5 w-5 mr-1" />
                  Nouvelle Reunion
                </button>
              </div>

              <div className="card">
                <table className="min-w-full">
                  <thead>
                    <tr className="text-left text-xs text-gray-500 uppercase border-b">
                      <th className="pb-3">Type</th>
                      <th className="pb-3">Date</th>
                      <th className="pb-3">Lieu</th>
                      <th className="pb-3">Participants</th>
                      <th className="pb-3">Quorum</th>
                      <th className="pb-3">Statut</th>
                      <th className="pb-3">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {meetings.length > 0 ? (
                      meetings.map((meeting) => (
                        <tr key={meeting.id} className="hover:bg-gray-50">
                          <td className="py-3 font-medium">{getMeetingTypeLabel(meeting.meeting_type)}</td>
                          <td className="py-3">{formatDate(meeting.meeting_date)}</td>
                          <td className="py-3">{meeting.location}</td>
                          <td className="py-3">{meeting.attendees_count}</td>
                          <td className="py-3">
                            {meeting.quorum_reached ? (
                              <CheckCircleIcon className="h-5 w-5 text-green-500" />
                            ) : (
                              <ClockIcon className="h-5 w-5 text-gray-400" />
                            )}
                          </td>
                          <td className="py-3">
                            <span className={`px-2 py-1 rounded-full text-xs ${getStatusBadge(meeting.status)}`}>
                              {meeting.status}
                            </span>
                          </td>
                          <td className="py-3">
                            <div className="flex space-x-2">
                              <button
                                onClick={() => handleGeneratePV(meeting.id)}
                                className="text-primary-600 hover:text-primary-800"
                                title="Generer PV"
                              >
                                <DocumentArrowDownIcon className="h-5 w-5" />
                              </button>
                              {meeting.status !== 'APPROUVE' && (
                                <button
                                  onClick={() => handleApproveMeeting(meeting.id)}
                                  className="text-green-600 hover:text-green-800"
                                  title="Approuver"
                                >
                                  <CheckCircleIcon className="h-5 w-5" />
                                </button>
                              )}
                            </div>
                          </td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan={7} className="py-8 text-center text-gray-500">
                          Aucune reunion enregistree
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Reports Tab */}
          {activeTab === 'reports' && (
            <div>
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-lg font-semibold">Rapports de Gestion</h2>
              </div>

              <div className="card">
                <table className="min-w-full">
                  <thead>
                    <tr className="text-left text-xs text-gray-500 uppercase border-b">
                      <th className="pb-3">Exercice</th>
                      <th className="pb-3">Type</th>
                      <th className="pb-3">Date creation</th>
                      <th className="pb-3">Statut</th>
                      <th className="pb-3">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {reports.length > 0 ? (
                      reports.map((report) => (
                        <tr key={report.id} className="hover:bg-gray-50">
                          <td className="py-3 font-medium">{report.fiscal_year_name}</td>
                          <td className="py-3">{report.report_type}</td>
                          <td className="py-3">{formatDate(report.created_at)}</td>
                          <td className="py-3">
                            <span className={`px-2 py-1 rounded-full text-xs ${getStatusBadge(report.status)}`}>
                              {report.status}
                            </span>
                          </td>
                          <td className="py-3">
                            <button className="text-primary-600 hover:text-primary-800">
                              <DocumentArrowDownIcon className="h-5 w-5" />
                            </button>
                          </td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan={5} className="py-8 text-center text-gray-500">
                          Aucun rapport de gestion
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Officers Tab */}
          {activeTab === 'officers' && (
            <div>
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-lg font-semibold">Mandataires Sociaux</h2>
                <button
                  onClick={() => setShowOfficerModal(true)}
                  className="btn-primary flex items-center"
                >
                  <PlusIcon className="h-5 w-5 mr-1" />
                  Nouveau Mandataire
                </button>
              </div>

              <div className="card">
                <table className="min-w-full">
                  <thead>
                    <tr className="text-left text-xs text-gray-500 uppercase border-b">
                      <th className="pb-3">Nom</th>
                      <th className="pb-3">Type</th>
                      <th className="pb-3">Fonction</th>
                      <th className="pb-3">Debut mandat</th>
                      <th className="pb-3">Fin mandat</th>
                      <th className="pb-3">Statut</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {officers.length > 0 ? (
                      officers.map((officer) => (
                        <tr key={officer.id} className="hover:bg-gray-50">
                          <td className="py-3 font-medium">{officer.name}</td>
                          <td className="py-3">
                            {officer.person_type === 'NATURAL' ? 'Personne physique' : 'Personne morale'}
                          </td>
                          <td className="py-3">{getFunctionLabel(officer.function_type)}</td>
                          <td className="py-3">{formatDate(officer.start_date)}</td>
                          <td className="py-3">{officer.end_date ? formatDate(officer.end_date) : '-'}</td>
                          <td className="py-3">
                            <span className={`px-2 py-1 rounded-full text-xs ${
                              officer.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                            }`}>
                              {officer.is_active ? 'Actif' : 'Termine'}
                            </span>
                          </td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan={6} className="py-8 text-center text-gray-500">
                          Aucun mandataire enregistre
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Publications Tab */}
          {activeTab === 'publications' && (
            <div>
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-lg font-semibold">Publications au Moniteur Belge</h2>
              </div>

              <div className="card">
                <table className="min-w-full">
                  <thead>
                    <tr className="text-left text-xs text-gray-500 uppercase border-b">
                      <th className="pb-3">Type</th>
                      <th className="pb-3">Date publication</th>
                      <th className="pb-3">Reference</th>
                      <th className="pb-3">Statut</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {publications.length > 0 ? (
                      publications.map((pub) => (
                        <tr key={pub.id} className="hover:bg-gray-50">
                          <td className="py-3 font-medium">{pub.publication_type}</td>
                          <td className="py-3">{pub.publication_date ? formatDate(pub.publication_date) : '-'}</td>
                          <td className="py-3 font-mono">{pub.reference_number || '-'}</td>
                          <td className="py-3">
                            <span className={`px-2 py-1 rounded-full text-xs ${getStatusBadge(pub.status)}`}>
                              {pub.status}
                            </span>
                          </td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan={4} className="py-8 text-center text-gray-500">
                          Aucune publication
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* UBO Tab */}
          {activeTab === 'ubo' && (
            <div>
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-lg font-semibold">Registre UBO (Beneficiaires Effectifs)</h2>
              </div>

              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4">
                <p className="text-yellow-800 text-sm">
                  <strong>Attention:</strong> Le registre UBO doit etre declare au SPF Finances annuellement.
                  Toute modification doit etre signalee dans le mois.
                </p>
              </div>

              <div className="card">
                <table className="min-w-full">
                  <thead>
                    <tr className="text-left text-xs text-gray-500 uppercase border-b">
                      <th className="pb-3">Nom</th>
                      <th className="pb-3">Type</th>
                      <th className="pb-3">Nationalite</th>
                      <th className="pb-3">% Detention</th>
                      <th className="pb-3">Type controle</th>
                      <th className="pb-3">Declare SPF</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {uboEntries.length > 0 ? (
                      uboEntries.map((ubo) => (
                        <tr key={ubo.id} className="hover:bg-gray-50">
                          <td className="py-3 font-medium">{ubo.name}</td>
                          <td className="py-3">
                            {ubo.person_type === 'NATURAL' ? 'Personne physique' : 'Personne morale'}
                          </td>
                          <td className="py-3">{ubo.nationality}</td>
                          <td className="py-3">{ubo.ownership_percentage}%</td>
                          <td className="py-3">{ubo.control_type}</td>
                          <td className="py-3">
                            {ubo.declared_to_spf ? (
                              <CheckCircleIcon className="h-5 w-5 text-green-500" />
                            ) : (
                              <ClockIcon className="h-5 w-5 text-yellow-500" />
                            )}
                          </td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan={6} className="py-8 text-center text-gray-500">
                          Aucun beneficiaire effectif enregistre
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}

      {/* Meeting Modal */}
      {showMeetingModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-lg">
            <h3 className="text-lg font-semibold mb-4">Nouvelle Reunion</h3>
            <form onSubmit={handleCreateMeeting}>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Type de reunion
                  </label>
                  <select
                    value={meetingForm.meeting_type}
                    onChange={(e) => setMeetingForm({ ...meetingForm, meeting_type: e.target.value })}
                    className="input-field"
                  >
                    <option value="AG_ORDINAIRE">Assemblee Generale Ordinaire</option>
                    <option value="AG_EXTRAORDINAIRE">Assemblee Generale Extraordinaire</option>
                    <option value="CA">Conseil d'Administration</option>
                    <option value="COMITE_DIRECTION">Comite de Direction</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Date
                  </label>
                  <input
                    type="datetime-local"
                    value={meetingForm.meeting_date}
                    onChange={(e) => setMeetingForm({ ...meetingForm, meeting_date: e.target.value })}
                    className="input-field"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Lieu
                  </label>
                  <input
                    type="text"
                    value={meetingForm.location}
                    onChange={(e) => setMeetingForm({ ...meetingForm, location: e.target.value })}
                    className="input-field"
                    placeholder="Siege social, Teams, etc."
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Ordre du jour
                  </label>
                  <textarea
                    value={meetingForm.agenda}
                    onChange={(e) => setMeetingForm({ ...meetingForm, agenda: e.target.value })}
                    className="input-field"
                    rows={4}
                    placeholder="Points a l'ordre du jour..."
                  />
                </div>
              </div>

              <div className="flex justify-end space-x-3 mt-6">
                <button
                  type="button"
                  onClick={() => setShowMeetingModal(false)}
                  className="btn-secondary"
                >
                  Annuler
                </button>
                <button type="submit" className="btn-primary">
                  Creer
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Officer Modal */}
      {showOfficerModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-lg">
            <h3 className="text-lg font-semibold mb-4">Nouveau Mandataire</h3>
            <form onSubmit={handleCreateOfficer}>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Type de personne
                  </label>
                  <select
                    value={officerForm.person_type}
                    onChange={(e) => setOfficerForm({ ...officerForm, person_type: e.target.value })}
                    className="input-field"
                  >
                    <option value="NATURAL">Personne physique</option>
                    <option value="LEGAL">Personne morale</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Nom complet
                  </label>
                  <input
                    type="text"
                    value={officerForm.name}
                    onChange={(e) => setOfficerForm({ ...officerForm, name: e.target.value })}
                    className="input-field"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Fonction
                  </label>
                  <select
                    value={officerForm.function_type}
                    onChange={(e) => setOfficerForm({ ...officerForm, function_type: e.target.value })}
                    className="input-field"
                  >
                    <option value="ADMINISTRATEUR">Administrateur</option>
                    <option value="ADMINISTRATEUR_DELEGUE">Administrateur Delegue</option>
                    <option value="GERANT">Gerant</option>
                    <option value="PRESIDENT">President</option>
                    <option value="SECRETAIRE">Secretaire</option>
                    <option value="COMMISSAIRE">Commissaire</option>
                  </select>
                </div>

                {officerForm.person_type === 'NATURAL' ? (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Numero national
                    </label>
                    <input
                      type="text"
                      value={officerForm.national_number}
                      onChange={(e) => setOfficerForm({ ...officerForm, national_number: e.target.value })}
                      className="input-field"
                      placeholder="XX.XX.XX-XXX.XX"
                    />
                  </div>
                ) : (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Numero d'entreprise
                    </label>
                    <input
                      type="text"
                      value={officerForm.company_number}
                      onChange={(e) => setOfficerForm({ ...officerForm, company_number: e.target.value })}
                      className="input-field"
                      placeholder="BE 0XXX.XXX.XXX"
                    />
                  </div>
                )}

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Date debut mandat
                  </label>
                  <input
                    type="date"
                    value={officerForm.start_date}
                    onChange={(e) => setOfficerForm({ ...officerForm, start_date: e.target.value })}
                    className="input-field"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Adresse
                  </label>
                  <input
                    type="text"
                    value={officerForm.address}
                    onChange={(e) => setOfficerForm({ ...officerForm, address: e.target.value })}
                    className="input-field"
                  />
                </div>
              </div>

              <div className="flex justify-end space-x-3 mt-6">
                <button
                  type="button"
                  onClick={() => setShowOfficerModal(false)}
                  className="btn-secondary"
                >
                  Annuler
                </button>
                <button type="submit" className="btn-primary">
                  Creer
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
