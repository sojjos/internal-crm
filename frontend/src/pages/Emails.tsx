import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { emailsApi } from '../services/api'
import toast from 'react-hot-toast'
import {
  EnvelopeIcon,
  PaperAirplaneIcon,
  TrashIcon,
  StarIcon,
  ArrowPathIcon,
  PencilSquareIcon,
  InboxIcon,
  PaperClipIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  Cog6ToothIcon,
} from '@heroicons/react/24/outline'
import { StarIcon as StarIconSolid } from '@heroicons/react/24/solid'

interface EmailAccount {
  id: number
  name: string
  email_address: string
  account_type: string
  is_default: boolean
}

interface Email {
  id: number
  account_id: number
  subject: string | null
  from_address: string
  from_name: string | null
  to_addresses: string[]
  snippet: string | null
  date_sent: string | null
  is_read: boolean
  is_starred: boolean
  has_attachments: boolean
}

interface FolderCount {
  folder: string
  total: number
  unread: number
}

const folders = [
  { name: 'INBOX', label: 'Boîte de réception', icon: InboxIcon },
  { name: 'Sent', label: 'Envoyés', icon: PaperAirplaneIcon },
  { name: 'Drafts', label: 'Brouillons', icon: PencilSquareIcon },
  { name: 'Trash', label: 'Corbeille', icon: TrashIcon },
]

export default function Emails() {
  const [accounts, setAccounts] = useState<EmailAccount[]>([])
  const [selectedAccount, setSelectedAccount] = useState<EmailAccount | null>(null)
  const [selectedFolder, setSelectedFolder] = useState('INBOX')
  const [emails, setEmails] = useState<Email[]>([])
  const [folderCounts, setFolderCounts] = useState<FolderCount[]>([])
  const [selectedEmail, setSelectedEmail] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [syncing, setSyncing] = useState(false)
  const [page, setPage] = useState(1)
  const [totalEmails, setTotalEmails] = useState(0)
  const perPage = 25

  useEffect(() => {
    loadAccounts()
  }, [])

  useEffect(() => {
    if (selectedAccount) {
      loadEmails()
      loadFolderCounts()
    }
  }, [selectedAccount, selectedFolder, page])

  const loadAccounts = async () => {
    try {
      const response = await emailsApi.accounts.list()
      setAccounts(response.data)
      if (response.data.length > 0) {
        const defaultAccount = response.data.find((a: EmailAccount) => a.is_default) || response.data[0]
        setSelectedAccount(defaultAccount)
      }
    } catch (error) {
      console.error('Failed to load accounts', error)
    } finally {
      setLoading(false)
    }
  }

  const loadEmails = async () => {
    if (!selectedAccount) return

    try {
      const response = await emailsApi.list({
        account_id: selectedAccount.id,
        folder: selectedFolder,
        page,
        per_page: perPage,
      })
      setEmails(response.data.emails)
      setTotalEmails(response.data.total)
    } catch (error) {
      console.error('Failed to load emails', error)
    }
  }

  const loadFolderCounts = async () => {
    if (!selectedAccount) return

    try {
      const response = await emailsApi.folders(selectedAccount.id)
      setFolderCounts(response.data)
    } catch (error) {
      console.error('Failed to load folder counts', error)
    }
  }

  const syncEmails = async () => {
    if (!selectedAccount) return

    setSyncing(true)
    try {
      await emailsApi.sync(selectedAccount.id, selectedFolder)
      toast.success('Synchronisation démarrée')
      // Reload after a short delay
      setTimeout(() => {
        loadEmails()
        loadFolderCounts()
      }, 2000)
    } catch (error) {
      toast.error('Erreur de synchronisation')
    } finally {
      setSyncing(false)
    }
  }

  const loadEmailDetail = async (emailId: number) => {
    try {
      const response = await emailsApi.get(emailId)
      setSelectedEmail(response.data)
      // Mark as read in list
      setEmails(emails.map(e => e.id === emailId ? { ...e, is_read: true } : e))
    } catch (error) {
      toast.error('Erreur de chargement')
    }
  }

  const toggleStar = async (e: React.MouseEvent, emailId: number) => {
    e.stopPropagation()
    try {
      const response = await emailsApi.star(emailId)
      setEmails(emails.map(email =>
        email.id === emailId ? { ...email, is_starred: response.data.is_starred } : email
      ))
    } catch (error) {
      toast.error('Erreur')
    }
  }

  const deleteEmail = async (emailId: number) => {
    try {
      await emailsApi.delete(emailId)
      setEmails(emails.filter(e => e.id !== emailId))
      if (selectedEmail?.id === emailId) {
        setSelectedEmail(null)
      }
      toast.success('Email supprimé')
    } catch (error) {
      toast.error('Erreur de suppression')
    }
  }

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return ''
    const date = new Date(dateStr)
    const today = new Date()
    if (date.toDateString() === today.toDateString()) {
      return date.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })
    }
    return date.toLocaleDateString('fr-FR', { day: '2-digit', month: 'short' })
  }

  const getFolderCount = (folderName: string): number => {
    const folder = folderCounts.find(f => f.folder === folderName)
    return folder?.unread || 0
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  if (accounts.length === 0) {
    return (
      <div className="text-center py-12">
        <EnvelopeIcon className="mx-auto h-12 w-12 text-gray-400" />
        <h3 className="mt-2 text-lg font-semibold text-gray-900">Aucun compte email</h3>
        <p className="mt-1 text-gray-500">
          Configurez un compte email pour commencer à utiliser la messagerie.
        </p>
        <div className="mt-6">
          <Link to="/emails/settings" className="btn-primary">
            Configurer un compte
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="h-[calc(100vh-10rem)]">
      <div className="flex justify-between items-center mb-4">
        <h1 className="page-title">Messagerie</h1>
        <div className="flex gap-2">
          <Link to="/emails/settings" className="btn-secondary flex items-center gap-2">
            <Cog6ToothIcon className="h-5 w-5" />
            Paramètres
          </Link>
          <Link to="/emails/compose" className="btn-primary flex items-center gap-2">
            <PencilSquareIcon className="h-5 w-5" />
            Nouveau message
          </Link>
        </div>
      </div>

      <div className="flex h-full gap-4">
        {/* Sidebar */}
        <div className="w-64 flex-shrink-0">
          {/* Account selector */}
          <select
            value={selectedAccount?.id || ''}
            onChange={(e) => {
              const account = accounts.find(a => a.id === Number(e.target.value))
              setSelectedAccount(account || null)
            }}
            className="input mb-4 w-full"
          >
            {accounts.map(account => (
              <option key={account.id} value={account.id}>
                {account.name} ({account.email_address})
              </option>
            ))}
          </select>

          {/* Folders */}
          <nav className="space-y-1">
            {folders.map(folder => {
              const count = getFolderCount(folder.name)
              const isSelected = selectedFolder === folder.name
              return (
                <button
                  key={folder.name}
                  onClick={() => {
                    setSelectedFolder(folder.name)
                    setPage(1)
                    setSelectedEmail(null)
                  }}
                  className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-sm ${
                    isSelected
                      ? 'bg-primary-100 text-primary-700'
                      : 'text-gray-700 hover:bg-gray-100'
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <folder.icon className="h-5 w-5" />
                    {folder.label}
                  </div>
                  {count > 0 && (
                    <span className="bg-primary-600 text-white text-xs px-2 py-0.5 rounded-full">
                      {count}
                    </span>
                  )}
                </button>
              )
            })}
          </nav>

          {/* Sync button */}
          <button
            onClick={syncEmails}
            disabled={syncing}
            className="mt-4 w-full flex items-center justify-center gap-2 px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-lg disabled:opacity-50"
          >
            <ArrowPathIcon className={`h-5 w-5 ${syncing ? 'animate-spin' : ''}`} />
            {syncing ? 'Synchronisation...' : 'Synchroniser'}
          </button>
        </div>

        {/* Email list */}
        <div className="w-96 flex-shrink-0 bg-white rounded-lg shadow overflow-hidden flex flex-col">
          <div className="flex-1 overflow-y-auto">
            {emails.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                Aucun email dans ce dossier
              </div>
            ) : (
              <ul className="divide-y divide-gray-200">
                {emails.map(email => (
                  <li
                    key={email.id}
                    onClick={() => loadEmailDetail(email.id)}
                    className={`px-4 py-3 cursor-pointer hover:bg-gray-50 ${
                      !email.is_read ? 'bg-blue-50' : ''
                    } ${selectedEmail?.id === email.id ? 'bg-primary-50' : ''}`}
                  >
                    <div className="flex items-start gap-2">
                      <button
                        onClick={(e) => toggleStar(e, email.id)}
                        className="mt-1 flex-shrink-0"
                      >
                        {email.is_starred ? (
                          <StarIconSolid className="h-5 w-5 text-yellow-400" />
                        ) : (
                          <StarIcon className="h-5 w-5 text-gray-400 hover:text-yellow-400" />
                        )}
                      </button>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between">
                          <span className={`text-sm truncate ${!email.is_read ? 'font-semibold' : ''}`}>
                            {email.from_name || email.from_address}
                          </span>
                          <span className="text-xs text-gray-500 flex-shrink-0 ml-2">
                            {formatDate(email.date_sent)}
                          </span>
                        </div>
                        <div className="flex items-center gap-1">
                          <p className={`text-sm truncate ${!email.is_read ? 'font-medium' : 'text-gray-900'}`}>
                            {email.subject || '(Sans objet)'}
                          </p>
                          {email.has_attachments && (
                            <PaperClipIcon className="h-4 w-4 text-gray-400 flex-shrink-0" />
                          )}
                        </div>
                        <p className="text-xs text-gray-500 truncate">{email.snippet}</p>
                      </div>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>

          {/* Pagination */}
          {totalEmails > perPage && (
            <div className="border-t px-4 py-2 flex items-center justify-between">
              <span className="text-sm text-gray-500">
                {((page - 1) * perPage) + 1}-{Math.min(page * perPage, totalEmails)} sur {totalEmails}
              </span>
              <div className="flex gap-1">
                <button
                  onClick={() => setPage(p => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="p-1 rounded hover:bg-gray-100 disabled:opacity-50"
                >
                  <ChevronLeftIcon className="h-5 w-5" />
                </button>
                <button
                  onClick={() => setPage(p => p + 1)}
                  disabled={page * perPage >= totalEmails}
                  className="p-1 rounded hover:bg-gray-100 disabled:opacity-50"
                >
                  <ChevronRightIcon className="h-5 w-5" />
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Email detail */}
        <div className="flex-1 bg-white rounded-lg shadow overflow-hidden">
          {selectedEmail ? (
            <div className="h-full flex flex-col">
              {/* Header */}
              <div className="border-b px-6 py-4">
                <div className="flex items-start justify-between">
                  <h2 className="text-lg font-semibold">
                    {selectedEmail.subject || '(Sans objet)'}
                  </h2>
                  <button
                    onClick={() => deleteEmail(selectedEmail.id)}
                    className="text-red-500 hover:text-red-700"
                  >
                    <TrashIcon className="h-5 w-5" />
                  </button>
                </div>
                <div className="mt-2 text-sm">
                  <div className="flex items-center gap-2">
                    <span className="font-medium">
                      {selectedEmail.from_name || selectedEmail.from_address}
                    </span>
                    <span className="text-gray-500">
                      &lt;{selectedEmail.from_address}&gt;
                    </span>
                  </div>
                  <div className="text-gray-500">
                    À: {selectedEmail.to_addresses?.join(', ')}
                  </div>
                  {selectedEmail.cc_addresses?.length > 0 && (
                    <div className="text-gray-500">
                      Cc: {selectedEmail.cc_addresses.join(', ')}
                    </div>
                  )}
                  <div className="text-gray-500">
                    {selectedEmail.date_sent && new Date(selectedEmail.date_sent).toLocaleString('fr-FR')}
                  </div>
                </div>
              </div>

              {/* Body */}
              <div className="flex-1 overflow-y-auto px-6 py-4">
                {selectedEmail.body_html ? (
                  <div
                    className="prose max-w-none"
                    dangerouslySetInnerHTML={{ __html: selectedEmail.body_html }}
                  />
                ) : (
                  <pre className="whitespace-pre-wrap font-sans">
                    {selectedEmail.body_text}
                  </pre>
                )}
              </div>

              {/* Attachments */}
              {selectedEmail.attachments?.length > 0 && (
                <div className="border-t px-6 py-3">
                  <h4 className="text-sm font-medium mb-2">Pièces jointes</h4>
                  <div className="flex flex-wrap gap-2">
                    {selectedEmail.attachments.map((att: any, idx: number) => (
                      <div
                        key={idx}
                        className="flex items-center gap-2 px-3 py-2 bg-gray-100 rounded text-sm"
                      >
                        <PaperClipIcon className="h-4 w-4" />
                        {att.name}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Actions */}
              <div className="border-t px-6 py-3 flex gap-2">
                <Link
                  to={`/emails/compose?reply=${selectedEmail.id}`}
                  className="btn-primary text-sm"
                >
                  Répondre
                </Link>
                <Link
                  to={`/emails/compose?forward=${selectedEmail.id}`}
                  className="btn-secondary text-sm"
                >
                  Transférer
                </Link>
              </div>
            </div>
          ) : (
            <div className="h-full flex items-center justify-center text-gray-500">
              <div className="text-center">
                <EnvelopeIcon className="mx-auto h-12 w-12 text-gray-400" />
                <p className="mt-2">Sélectionnez un email pour le lire</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
