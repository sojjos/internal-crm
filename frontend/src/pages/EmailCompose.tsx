import { useState, useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { emailsApi } from '../services/api'
import toast from 'react-hot-toast'
import {
  PaperAirplaneIcon,
  PaperClipIcon,
  XMarkIcon,
} from '@heroicons/react/24/outline'

interface EmailAccount {
  id: number
  name: string
  email_address: string
  signature_html: string | null
  signature_text: string | null
}

export default function EmailCompose() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const replyToId = searchParams.get('reply')
  const forwardId = searchParams.get('forward')

  const [accounts, setAccounts] = useState<EmailAccount[]>([])
  const [selectedAccount, setSelectedAccount] = useState<number | null>(null)
  const [to, setTo] = useState('')
  const [cc, setCc] = useState('')
  const [bcc, setBcc] = useState('')
  const [subject, setSubject] = useState('')
  const [bodyHtml, setBodyHtml] = useState('')
  const [bodyText, setBodyText] = useState('')
  const [attachments, setAttachments] = useState<File[]>([])
  const [requestReadReceipt, setRequestReadReceipt] = useState(false)
  const [sending, setSending] = useState(false)
  const [showBcc, setShowBcc] = useState(false)

  useEffect(() => {
    loadAccounts()
  }, [])

  useEffect(() => {
    if (replyToId || forwardId) {
      loadOriginalEmail(Number(replyToId || forwardId))
    }
  }, [replyToId, forwardId])

  const loadAccounts = async () => {
    try {
      const response = await emailsApi.accounts.list()
      setAccounts(response.data)
      if (response.data.length > 0) {
        const defaultAccount = response.data.find((a: EmailAccount) => a.is_default) || response.data[0]
        setSelectedAccount(defaultAccount.id)
      }
    } catch (error) {
      toast.error('Erreur de chargement des comptes')
    }
  }

  const loadOriginalEmail = async (emailId: number) => {
    try {
      const response = await emailsApi.get(emailId)
      const email = response.data

      if (replyToId) {
        // Reply mode
        setTo(email.from_address)
        setSubject(`Re: ${email.subject || ''}`)
        setBodyHtml(`
          <br><br>
          <div style="border-left: 2px solid #ccc; padding-left: 10px; margin-left: 10px;">
            <p>Le ${new Date(email.date_sent).toLocaleString('fr-FR')}, ${email.from_name || email.from_address} a écrit :</p>
            ${email.body_html || `<pre>${email.body_text}</pre>`}
          </div>
        `)
      } else if (forwardId) {
        // Forward mode
        setSubject(`Fwd: ${email.subject || ''}`)
        setBodyHtml(`
          <br><br>
          <div style="border-left: 2px solid #ccc; padding-left: 10px; margin-left: 10px;">
            <p>---------- Message transféré ----------</p>
            <p>De : ${email.from_name || email.from_address} &lt;${email.from_address}&gt;</p>
            <p>Date : ${new Date(email.date_sent).toLocaleString('fr-FR')}</p>
            <p>Objet : ${email.subject || '(Sans objet)'}</p>
            <p>À : ${email.to_addresses?.join(', ')}</p>
            <br>
            ${email.body_html || `<pre>${email.body_text}</pre>`}
          </div>
        `)
      }
    } catch (error) {
      toast.error('Erreur de chargement')
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!selectedAccount) {
      toast.error('Sélectionnez un compte')
      return
    }

    if (!to.trim()) {
      toast.error('Entrez au moins un destinataire')
      return
    }

    setSending(true)

    try {
      const formData = new FormData()
      formData.append('account_id', String(selectedAccount))
      formData.append('to', to)
      formData.append('subject', subject)

      if (cc.trim()) formData.append('cc', cc)
      if (bcc.trim()) formData.append('bcc', bcc)
      if (bodyText.trim()) formData.append('body_text', bodyText)
      if (bodyHtml.trim()) formData.append('body_html', bodyHtml)
      formData.append('request_read_receipt', String(requestReadReceipt))

      // Add attachments
      attachments.forEach(file => {
        formData.append('attachments', file)
      })

      await emailsApi.send(formData)
      toast.success('Email envoyé !')
      navigate('/emails')
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Erreur d\'envoi')
    } finally {
      setSending(false)
    }
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || [])
    setAttachments(prev => [...prev, ...files])
  }

  const removeAttachment = (index: number) => {
    setAttachments(prev => prev.filter((_, i) => i !== index))
  }

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  return (
    <div>
      <h1 className="page-title">Nouveau message</h1>

      <form onSubmit={handleSubmit} className="card max-w-4xl">
        {/* Account selector */}
        <div className="mb-4">
          <label className="label">De</label>
          <select
            value={selectedAccount || ''}
            onChange={(e) => setSelectedAccount(Number(e.target.value))}
            className="input"
            required
          >
            <option value="">Sélectionner un compte</option>
            {accounts.map(account => (
              <option key={account.id} value={account.id}>
                {account.name} &lt;{account.email_address}&gt;
              </option>
            ))}
          </select>
        </div>

        {/* Recipients */}
        <div className="mb-4">
          <div className="flex items-center justify-between">
            <label className="label">À</label>
            <button
              type="button"
              onClick={() => setShowBcc(!showBcc)}
              className="text-sm text-primary-600 hover:text-primary-700"
            >
              {showBcc ? 'Masquer Cci' : 'Afficher Cc/Cci'}
            </button>
          </div>
          <input
            type="text"
            value={to}
            onChange={(e) => setTo(e.target.value)}
            placeholder="email@exemple.com, autre@exemple.com"
            className="input"
            required
          />
        </div>

        {showBcc && (
          <>
            <div className="mb-4">
              <label className="label">Cc</label>
              <input
                type="text"
                value={cc}
                onChange={(e) => setCc(e.target.value)}
                placeholder="Copie carbone"
                className="input"
              />
            </div>

            <div className="mb-4">
              <label className="label">Cci</label>
              <input
                type="text"
                value={bcc}
                onChange={(e) => setBcc(e.target.value)}
                placeholder="Copie carbone invisible"
                className="input"
              />
            </div>
          </>
        )}

        {/* Subject */}
        <div className="mb-4">
          <label className="label">Objet</label>
          <input
            type="text"
            value={subject}
            onChange={(e) => setSubject(e.target.value)}
            placeholder="Objet du message"
            className="input"
          />
        </div>

        {/* Body */}
        <div className="mb-4">
          <label className="label">Message</label>
          <textarea
            value={bodyText}
            onChange={(e) => setBodyText(e.target.value)}
            rows={12}
            className="input font-mono text-sm"
            placeholder="Écrivez votre message..."
          />
        </div>

        {/* Attachments */}
        <div className="mb-4">
          <label className="label">Pièces jointes</label>
          <div className="border-2 border-dashed border-gray-300 rounded-lg p-4">
            <input
              type="file"
              multiple
              onChange={handleFileSelect}
              className="hidden"
              id="file-input"
            />
            <label
              htmlFor="file-input"
              className="cursor-pointer flex items-center justify-center gap-2 text-gray-500 hover:text-gray-700"
            >
              <PaperClipIcon className="h-5 w-5" />
              Cliquez pour ajouter des fichiers
            </label>
          </div>

          {attachments.length > 0 && (
            <ul className="mt-2 space-y-2">
              {attachments.map((file, index) => (
                <li
                  key={index}
                  className="flex items-center justify-between px-3 py-2 bg-gray-100 rounded"
                >
                  <div className="flex items-center gap-2">
                    <PaperClipIcon className="h-4 w-4 text-gray-500" />
                    <span className="text-sm">{file.name}</span>
                    <span className="text-xs text-gray-500">
                      ({formatFileSize(file.size)})
                    </span>
                  </div>
                  <button
                    type="button"
                    onClick={() => removeAttachment(index)}
                    className="text-gray-500 hover:text-red-500"
                  >
                    <XMarkIcon className="h-4 w-4" />
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* Options */}
        <div className="mb-6">
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={requestReadReceipt}
              onChange={(e) => setRequestReadReceipt(e.target.checked)}
              className="rounded border-gray-300"
            />
            <span className="text-sm text-gray-700">
              Demander un accusé de réception
            </span>
          </label>
        </div>

        {/* Actions */}
        <div className="flex justify-between items-center">
          <button
            type="button"
            onClick={() => navigate('/emails')}
            className="btn-secondary"
          >
            Annuler
          </button>

          <button
            type="submit"
            disabled={sending}
            className="btn-primary flex items-center gap-2 disabled:opacity-50"
          >
            <PaperAirplaneIcon className="h-5 w-5" />
            {sending ? 'Envoi en cours...' : 'Envoyer'}
          </button>
        </div>
      </form>
    </div>
  )
}
