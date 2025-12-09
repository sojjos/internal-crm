import { useEffect, useState, useRef } from 'react'
import { integrationsApi } from '../services/api'
import {
  CloudArrowUpIcon,
  DocumentArrowUpIcon,
  CogIcon,
  LinkIcon,
  DocumentTextIcon,
  BanknotesIcon,
  PlusIcon,
} from '@heroicons/react/24/outline'

interface IntegrationConfig {
  id: number
  integration_type: string
  name: string
  is_active: boolean
  last_sync: string | null
  status: string
}

interface BelcotaxDeclaration {
  id: number
  year: number
  declaration_type: string
  status: string
  fiches_count: number
  total_amount: number
  submitted_at: string | null
}

interface AccountingImport {
  id: number
  source_system: string
  file_name: string
  status: string
  entries_count: number
  processed_count: number
  imported_at: string
}

interface CodaImport {
  id: number
  file_name: string
  bank_account: string
  statement_date: string
  movements_count: number
  total_credit: number
  total_debit: number
  status: string
}

export default function Integrations() {
  const [activeTab, setActiveTab] = useState<'config' | 'belcotax' | 'imports' | 'coda'>('config')
  const [integrations, setIntegrations] = useState<IntegrationConfig[]>([])
  const [belcotaxDeclarations, setBelcotaxDeclarations] = useState<BelcotaxDeclaration[]>([])
  const [accountingImports, setAccountingImports] = useState<AccountingImport[]>([])
  const [codaImports, setCodaImports] = useState<CodaImport[]>([])
  const [loading, setLoading] = useState(true)
  const [showConfigModal, setShowConfigModal] = useState(false)
  const [showBelcotaxModal, setShowBelcotaxModal] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const codaFileInputRef = useRef<HTMLInputElement>(null)

  // Config form
  const [configForm, setConfigForm] = useState({
    integration_type: 'CASEWARE',
    name: '',
    api_url: '',
    api_key: '',
    username: '',
    password: '',
  })

  // Belcotax form
  const [belcotaxForm, setBelcotaxForm] = useState({
    year: new Date().getFullYear() - 1,
    declaration_type: '281.10',
  })

  useEffect(() => {
    loadData()
  }, [activeTab])

  const loadData = async () => {
    setLoading(true)
    try {
      switch (activeTab) {
        case 'config':
          const configRes = await integrationsApi.config.list()
          setIntegrations(configRes.data)
          break
        case 'belcotax':
          const belcotaxRes = await integrationsApi.belcotax.declarations.list()
          setBelcotaxDeclarations(belcotaxRes.data)
          break
        case 'imports':
          const importsRes = await integrationsApi.imports.list()
          setAccountingImports(importsRes.data)
          break
        case 'coda':
          const codaRes = await integrationsApi.coda.list()
          setCodaImports(codaRes.data)
          break
      }
    } catch (error) {
      console.error('Failed to load data', error)
    } finally {
      setLoading(false)
    }
  }

  const handleCreateConfig = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await integrationsApi.config.create(configForm)
      setShowConfigModal(false)
      setConfigForm({
        integration_type: 'CASEWARE',
        name: '',
        api_url: '',
        api_key: '',
        username: '',
        password: '',
      })
      loadData()
    } catch (error) {
      console.error('Failed to create config', error)
    }
  }

  const handleTestConnection = async (id: number) => {
    try {
      const res = await integrationsApi.config.test(id)
      if (res.data.success) {
        alert('Connexion reussie!')
      } else {
        alert('Echec de connexion: ' + res.data.message)
      }
    } catch (error) {
      alert('Erreur lors du test de connexion')
    }
  }

  const handleToggleActive = async (id: number, isActive: boolean) => {
    try {
      if (isActive) {
        await integrationsApi.config.activate(id)
      } else {
        await integrationsApi.config.update(id, { is_active: false })
      }
      loadData()
    } catch (error) {
      console.error('Failed to toggle integration', error)
    }
  }

  const handleCreateBelcotax = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await integrationsApi.belcotax.declarations.create(belcotaxForm)
      setShowBelcotaxModal(false)
      setBelcotaxForm({ year: new Date().getFullYear() - 1, declaration_type: '281.10' })
      loadData()
    } catch (error) {
      console.error('Failed to create declaration', error)
    }
  }

  const handleGenerateBelcotaxXml = async (id: number) => {
    try {
      const response = await integrationsApi.belcotax.declarations.generateXml(id)
      const blob = new Blob([response.data], { type: 'application/xml' })
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `belcotax_${id}.xml`
      a.click()
      window.URL.revokeObjectURL(url)
    } catch (error) {
      console.error('Failed to generate XML', error)
      alert('Erreur lors de la generation XML')
    }
  }

  const handleImportFile = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    try {
      await integrationsApi.imports.upload('CSV', file)
      loadData()
      alert('Fichier importe avec succes')
    } catch (error) {
      console.error('Failed to import file', error)
      alert('Erreur lors de l\'import')
    }
  }

  const handleCodaUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    try {
      await integrationsApi.coda.upload(file)
      loadData()
      alert('Fichier CODA importe avec succes')
    } catch (error) {
      console.error('Failed to import CODA', error)
      alert('Erreur lors de l\'import CODA')
    }
  }

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return '-'
    return new Date(dateStr).toLocaleDateString('fr-BE')
  }

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('fr-BE', {
      style: 'currency',
      currency: 'EUR',
    }).format(amount)
  }

  const getStatusBadge = (status: string) => {
    const styles: Record<string, string> = {
      ACTIVE: 'bg-green-100 text-green-800',
      ACTIF: 'bg-green-100 text-green-800',
      INACTIVE: 'bg-gray-100 text-gray-800',
      DRAFT: 'bg-gray-100 text-gray-800',
      BROUILLON: 'bg-gray-100 text-gray-800',
      PENDING: 'bg-yellow-100 text-yellow-800',
      EN_ATTENTE: 'bg-yellow-100 text-yellow-800',
      SUBMITTED: 'bg-blue-100 text-blue-800',
      SOUMIS: 'bg-blue-100 text-blue-800',
      COMPLETED: 'bg-green-100 text-green-800',
      TERMINE: 'bg-green-100 text-green-800',
      ERROR: 'bg-red-100 text-red-800',
      ERREUR: 'bg-red-100 text-red-800',
      PROCESSED: 'bg-green-100 text-green-800',
      TRAITE: 'bg-green-100 text-green-800',
    }
    return styles[status] || 'bg-gray-100 text-gray-800'
  }

  const getIntegrationIcon = (type: string) => {
    switch (type) {
      case 'CASEWARE':
        return CloudArrowUpIcon
      case 'BELCOTAX':
        return DocumentTextIcon
      case 'ACCOUNTING':
        return BanknotesIcon
      default:
        return CogIcon
    }
  }

  const tabs = [
    { id: 'config', label: 'Configuration', icon: CogIcon },
    { id: 'belcotax', label: 'Belcotaxonweb', icon: DocumentTextIcon },
    { id: 'imports', label: 'Import Comptable', icon: DocumentArrowUpIcon },
    { id: 'coda', label: 'CODA Bancaire', icon: BanknotesIcon },
  ]

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="page-title mb-0">Integrations</h1>
          <p className="text-gray-600">Connexions externes et imports de donnees</p>
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
          {/* Config Tab */}
          {activeTab === 'config' && (
            <div>
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-lg font-semibold">Integrations Configurees</h2>
                <button
                  onClick={() => setShowConfigModal(true)}
                  className="btn-primary flex items-center"
                >
                  <PlusIcon className="h-5 w-5 mr-1" />
                  Nouvelle Integration
                </button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {integrations.length > 0 ? (
                  integrations.map((integration) => {
                    const Icon = getIntegrationIcon(integration.integration_type)
                    return (
                      <div key={integration.id} className="card">
                        <div className="flex items-start justify-between">
                          <div className="flex items-center">
                            <div className={`p-3 rounded-lg ${
                              integration.is_active ? 'bg-green-100' : 'bg-gray-100'
                            }`}>
                              <Icon className={`h-6 w-6 ${
                                integration.is_active ? 'text-green-600' : 'text-gray-500'
                              }`} />
                            </div>
                            <div className="ml-3">
                              <h3 className="font-medium">{integration.name}</h3>
                              <p className="text-sm text-gray-500">{integration.integration_type}</p>
                            </div>
                          </div>
                          <span className={`px-2 py-1 rounded-full text-xs ${getStatusBadge(integration.status)}`}>
                            {integration.is_active ? 'Actif' : 'Inactif'}
                          </span>
                        </div>

                        <div className="mt-4 pt-4 border-t">
                          <p className="text-sm text-gray-500">
                            Derniere sync: {integration.last_sync ? formatDate(integration.last_sync) : 'Jamais'}
                          </p>
                          <div className="flex space-x-2 mt-3">
                            <button
                              onClick={() => handleTestConnection(integration.id)}
                              className="btn-secondary text-sm flex items-center"
                            >
                              <LinkIcon className="h-4 w-4 mr-1" />
                              Tester
                            </button>
                            <button
                              onClick={() => handleToggleActive(integration.id, !integration.is_active)}
                              className={`text-sm px-3 py-1 rounded ${
                                integration.is_active
                                  ? 'bg-red-100 text-red-700 hover:bg-red-200'
                                  : 'bg-green-100 text-green-700 hover:bg-green-200'
                              }`}
                            >
                              {integration.is_active ? 'Desactiver' : 'Activer'}
                            </button>
                          </div>
                        </div>
                      </div>
                    )
                  })
                ) : (
                  <div className="col-span-full text-center py-8 text-gray-500">
                    Aucune integration configuree
                  </div>
                )}

                {/* Quick Add Cards */}
                <div
                  onClick={() => {
                    setConfigForm({ ...configForm, integration_type: 'CASEWARE', name: 'Caseware Cloud' })
                    setShowConfigModal(true)
                  }}
                  className="card border-2 border-dashed border-gray-300 hover:border-primary-400 cursor-pointer"
                >
                  <div className="flex items-center justify-center h-full py-8">
                    <div className="text-center">
                      <CloudArrowUpIcon className="h-12 w-12 text-gray-400 mx-auto mb-2" />
                      <p className="font-medium text-gray-600">Ajouter Caseware Cloud</p>
                    </div>
                  </div>
                </div>

                <div
                  onClick={() => {
                    setConfigForm({ ...configForm, integration_type: 'ACCOUNTING', name: 'Import Winbooks' })
                    setShowConfigModal(true)
                  }}
                  className="card border-2 border-dashed border-gray-300 hover:border-primary-400 cursor-pointer"
                >
                  <div className="flex items-center justify-center h-full py-8">
                    <div className="text-center">
                      <DocumentArrowUpIcon className="h-12 w-12 text-gray-400 mx-auto mb-2" />
                      <p className="font-medium text-gray-600">Connecter Winbooks</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Belcotax Tab */}
          {activeTab === 'belcotax' && (
            <div>
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-lg font-semibold">Declarations Belcotaxonweb</h2>
                <button
                  onClick={() => setShowBelcotaxModal(true)}
                  className="btn-primary flex items-center"
                >
                  <PlusIcon className="h-5 w-5 mr-1" />
                  Nouvelle Declaration
                </button>
              </div>

              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
                <p className="text-blue-800 text-sm">
                  <strong>Rappel:</strong> Les fiches fiscales doivent etre soumises avant le 1er mars
                  de l'annee suivante via Belcotaxonweb.
                </p>
              </div>

              <div className="card">
                <table className="min-w-full">
                  <thead>
                    <tr className="text-left text-xs text-gray-500 uppercase border-b">
                      <th className="pb-3">Annee</th>
                      <th className="pb-3">Type</th>
                      <th className="pb-3">Fiches</th>
                      <th className="pb-3">Montant total</th>
                      <th className="pb-3">Statut</th>
                      <th className="pb-3">Soumis le</th>
                      <th className="pb-3">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {belcotaxDeclarations.length > 0 ? (
                      belcotaxDeclarations.map((decl) => (
                        <tr key={decl.id} className="hover:bg-gray-50">
                          <td className="py-3 font-medium">{decl.year}</td>
                          <td className="py-3">{decl.declaration_type}</td>
                          <td className="py-3">{decl.fiches_count}</td>
                          <td className="py-3">{formatCurrency(decl.total_amount)}</td>
                          <td className="py-3">
                            <span className={`px-2 py-1 rounded-full text-xs ${getStatusBadge(decl.status)}`}>
                              {decl.status}
                            </span>
                          </td>
                          <td className="py-3">{formatDate(decl.submitted_at)}</td>
                          <td className="py-3">
                            <div className="flex space-x-2">
                              <button
                                onClick={() => handleGenerateBelcotaxXml(decl.id)}
                                className="text-primary-600 hover:text-primary-800"
                                title="Generer XML"
                              >
                                <DocumentArrowUpIcon className="h-5 w-5" />
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan={7} className="py-8 text-center text-gray-500">
                          Aucune declaration Belcotax
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>

              {/* Fiche Types Info */}
              <div className="mt-6 grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="card bg-gray-50">
                  <h4 className="font-medium mb-2">281.10</h4>
                  <p className="text-sm text-gray-600">Remunerations des travailleurs</p>
                </div>
                <div className="card bg-gray-50">
                  <h4 className="font-medium mb-2">281.20</h4>
                  <p className="text-sm text-gray-600">Remunerations des dirigeants</p>
                </div>
                <div className="card bg-gray-50">
                  <h4 className="font-medium mb-2">281.30</h4>
                  <p className="text-sm text-gray-600">Honoraires et commissions</p>
                </div>
                <div className="card bg-gray-50">
                  <h4 className="font-medium mb-2">281.50</h4>
                  <p className="text-sm text-gray-600">Pensions et rentes</p>
                </div>
              </div>
            </div>
          )}

          {/* Imports Tab */}
          {activeTab === 'imports' && (
            <div>
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-lg font-semibold">Imports Comptables</h2>
                <div className="flex space-x-2">
                  <input
                    type="file"
                    ref={fileInputRef}
                    onChange={handleImportFile}
                    accept=".csv,.txt,.xml"
                    className="hidden"
                  />
                  <button
                    onClick={() => fileInputRef.current?.click()}
                    className="btn-primary flex items-center"
                  >
                    <DocumentArrowUpIcon className="h-5 w-5 mr-1" />
                    Importer Fichier
                  </button>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                <div className="card text-center p-6 hover:bg-gray-50 cursor-pointer" onClick={() => fileInputRef.current?.click()}>
                  <DocumentArrowUpIcon className="h-10 w-10 text-blue-500 mx-auto mb-2" />
                  <h4 className="font-medium">Winbooks</h4>
                  <p className="text-sm text-gray-500">Format TXT/CSV</p>
                </div>
                <div className="card text-center p-6 hover:bg-gray-50 cursor-pointer" onClick={() => fileInputRef.current?.click()}>
                  <DocumentArrowUpIcon className="h-10 w-10 text-green-500 mx-auto mb-2" />
                  <h4 className="font-medium">BOB 50</h4>
                  <p className="text-sm text-gray-500">Export standard</p>
                </div>
                <div className="card text-center p-6 hover:bg-gray-50 cursor-pointer" onClick={() => fileInputRef.current?.click()}>
                  <DocumentArrowUpIcon className="h-10 w-10 text-purple-500 mx-auto mb-2" />
                  <h4 className="font-medium">Exact Online</h4>
                  <p className="text-sm text-gray-500">XML Export</p>
                </div>
              </div>

              <div className="card">
                <h3 className="font-medium mb-4">Historique des imports</h3>
                <table className="min-w-full">
                  <thead>
                    <tr className="text-left text-xs text-gray-500 uppercase border-b">
                      <th className="pb-3">Fichier</th>
                      <th className="pb-3">Source</th>
                      <th className="pb-3">Ecritures</th>
                      <th className="pb-3">Traitees</th>
                      <th className="pb-3">Date</th>
                      <th className="pb-3">Statut</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {accountingImports.length > 0 ? (
                      accountingImports.map((imp) => (
                        <tr key={imp.id} className="hover:bg-gray-50">
                          <td className="py-3 font-mono text-sm">{imp.file_name}</td>
                          <td className="py-3">{imp.source_system}</td>
                          <td className="py-3">{imp.entries_count}</td>
                          <td className="py-3">{imp.processed_count}</td>
                          <td className="py-3">{formatDate(imp.imported_at)}</td>
                          <td className="py-3">
                            <span className={`px-2 py-1 rounded-full text-xs ${getStatusBadge(imp.status)}`}>
                              {imp.status}
                            </span>
                          </td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan={6} className="py-8 text-center text-gray-500">
                          Aucun import effectue
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* CODA Tab */}
          {activeTab === 'coda' && (
            <div>
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-lg font-semibold">Import CODA Bancaire</h2>
                <div className="flex space-x-2">
                  <input
                    type="file"
                    ref={codaFileInputRef}
                    onChange={handleCodaUpload}
                    accept=".cod,.coda"
                    className="hidden"
                  />
                  <button
                    onClick={() => codaFileInputRef.current?.click()}
                    className="btn-primary flex items-center"
                  >
                    <DocumentArrowUpIcon className="h-5 w-5 mr-1" />
                    Importer CODA
                  </button>
                </div>
              </div>

              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4">
                <p className="text-yellow-800 text-sm">
                  <strong>CODA:</strong> Format standard belge pour l'echange de donnees bancaires.
                  Importez vos fichiers CODA pour automatiser le rapprochement bancaire.
                </p>
              </div>

              <div className="card">
                <h3 className="font-medium mb-4">Fichiers CODA importes</h3>
                <table className="min-w-full">
                  <thead>
                    <tr className="text-left text-xs text-gray-500 uppercase border-b">
                      <th className="pb-3">Fichier</th>
                      <th className="pb-3">Compte</th>
                      <th className="pb-3">Date releve</th>
                      <th className="pb-3">Mouvements</th>
                      <th className="pb-3">Credit</th>
                      <th className="pb-3">Debit</th>
                      <th className="pb-3">Statut</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {codaImports.length > 0 ? (
                      codaImports.map((coda) => (
                        <tr key={coda.id} className="hover:bg-gray-50">
                          <td className="py-3 font-mono text-sm">{coda.file_name}</td>
                          <td className="py-3">{coda.bank_account}</td>
                          <td className="py-3">{formatDate(coda.statement_date)}</td>
                          <td className="py-3">{coda.movements_count}</td>
                          <td className="py-3 text-green-600">{formatCurrency(coda.total_credit)}</td>
                          <td className="py-3 text-red-600">{formatCurrency(coda.total_debit)}</td>
                          <td className="py-3">
                            <span className={`px-2 py-1 rounded-full text-xs ${getStatusBadge(coda.status)}`}>
                              {coda.status}
                            </span>
                          </td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan={7} className="py-8 text-center text-gray-500">
                          Aucun fichier CODA importe
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

      {/* Config Modal */}
      {showConfigModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-lg">
            <h3 className="text-lg font-semibold mb-4">Nouvelle Integration</h3>
            <form onSubmit={handleCreateConfig}>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Type d'integration
                  </label>
                  <select
                    value={configForm.integration_type}
                    onChange={(e) => setConfigForm({ ...configForm, integration_type: e.target.value })}
                    className="input-field"
                  >
                    <option value="CASEWARE">Caseware Cloud</option>
                    <option value="ACCOUNTING">Logiciel comptable</option>
                    <option value="BANK">Banque</option>
                    <option value="OTHER">Autre</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Nom
                  </label>
                  <input
                    type="text"
                    value={configForm.name}
                    onChange={(e) => setConfigForm({ ...configForm, name: e.target.value })}
                    className="input-field"
                    placeholder="Ex: Caseware Production"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    URL API
                  </label>
                  <input
                    type="url"
                    value={configForm.api_url}
                    onChange={(e) => setConfigForm({ ...configForm, api_url: e.target.value })}
                    className="input-field"
                    placeholder="https://api.example.com"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Cle API
                  </label>
                  <input
                    type="password"
                    value={configForm.api_key}
                    onChange={(e) => setConfigForm({ ...configForm, api_key: e.target.value })}
                    className="input-field"
                    placeholder="Votre cle API"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Utilisateur
                    </label>
                    <input
                      type="text"
                      value={configForm.username}
                      onChange={(e) => setConfigForm({ ...configForm, username: e.target.value })}
                      className="input-field"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Mot de passe
                    </label>
                    <input
                      type="password"
                      value={configForm.password}
                      onChange={(e) => setConfigForm({ ...configForm, password: e.target.value })}
                      className="input-field"
                    />
                  </div>
                </div>
              </div>

              <div className="flex justify-end space-x-3 mt-6">
                <button
                  type="button"
                  onClick={() => setShowConfigModal(false)}
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

      {/* Belcotax Modal */}
      {showBelcotaxModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold mb-4">Nouvelle Declaration Belcotax</h3>
            <form onSubmit={handleCreateBelcotax}>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Annee fiscale
                  </label>
                  <input
                    type="number"
                    value={belcotaxForm.year}
                    onChange={(e) => setBelcotaxForm({ ...belcotaxForm, year: parseInt(e.target.value) })}
                    className="input-field"
                    min={2020}
                    max={new Date().getFullYear()}
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Type de fiche
                  </label>
                  <select
                    value={belcotaxForm.declaration_type}
                    onChange={(e) => setBelcotaxForm({ ...belcotaxForm, declaration_type: e.target.value })}
                    className="input-field"
                  >
                    <option value="281.10">281.10 - Remunerations travailleurs</option>
                    <option value="281.20">281.20 - Remunerations dirigeants</option>
                    <option value="281.30">281.30 - Honoraires et commissions</option>
                    <option value="281.50">281.50 - Pensions et rentes</option>
                  </select>
                </div>
              </div>

              <div className="flex justify-end space-x-3 mt-6">
                <button
                  type="button"
                  onClick={() => setShowBelcotaxModal(false)}
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
