import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { clientsApi } from '../services/api'
import toast from 'react-hot-toast'

interface ClientFormData {
  name: string
  contact_name: string
  address_street: string
  address_city: string
  address_postal_code: string
  address_country: string
  vat_number: string
  is_business: boolean
  email: string
  phone: string
  preferred_send_method: string
  peppol_id: string
  custom_payment_terms: number | null
  notes: string
}

export default function ClientForm() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const isEdit = Boolean(id)

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<ClientFormData>({
    defaultValues: {
      address_country: 'Belgique',
      is_business: true,
      preferred_send_method: 'email',
    },
  })

  useEffect(() => {
    if (isEdit) {
      loadClient()
    }
  }, [id])

  const loadClient = async () => {
    try {
      const response = await clientsApi.get(Number(id))
      reset(response.data)
    } catch (error) {
      toast.error('Erreur lors du chargement du client')
      navigate('/clients')
    }
  }

  const onSubmit = async (data: ClientFormData) => {
    setLoading(true)
    try {
      if (isEdit) {
        await clientsApi.update(Number(id), data)
        toast.success('Client mis à jour')
      } else {
        await clientsApi.create(data)
        toast.success('Client créé')
      }
      navigate('/clients')
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Erreur lors de la sauvegarde')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <h1 className="page-title">
        {isEdit ? 'Modifier le client' : 'Nouveau client'}
      </h1>

      <form onSubmit={handleSubmit(onSubmit)} className="card max-w-3xl">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="md:col-span-2">
            <label className="label">Nom / Raison sociale *</label>
            <input
              {...register('name', { required: 'Ce champ est requis' })}
              className="input"
            />
            {errors.name && (
              <p className="text-red-500 text-sm mt-1">{errors.name.message}</p>
            )}
          </div>

          <div>
            <label className="label">Personne de contact</label>
            <input {...register('contact_name')} className="input" />
          </div>

          <div>
            <label className="label">Email de facturation</label>
            <input type="email" {...register('email')} className="input" />
          </div>

          <div>
            <label className="label">Téléphone</label>
            <input {...register('phone')} className="input" />
          </div>

          <div>
            <label className="label">Numéro de TVA</label>
            <input {...register('vat_number')} className="input" placeholder="BE0123456789" />
          </div>

          <div className="md:col-span-2">
            <label className="label">Adresse</label>
            <input {...register('address_street')} className="input" placeholder="Rue et numéro" />
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
            <label className="label">Mode d'envoi préféré</label>
            <select {...register('preferred_send_method')} className="input">
              <option value="email">Email</option>
              <option value="peppol">Peppol</option>
            </select>
          </div>

          <div>
            <label className="label">ID Peppol</label>
            <input {...register('peppol_id')} className="input" placeholder="Pour e-facturation" />
          </div>

          <div>
            <label className="label">Délai de paiement (jours)</label>
            <input
              type="number"
              {...register('custom_payment_terms', { valueAsNumber: true })}
              className="input"
              placeholder="Laisser vide pour utiliser la valeur par défaut"
            />
          </div>

          <div className="md:col-span-2">
            <label className="label">Notes internes</label>
            <textarea {...register('notes')} className="input" rows={3} />
          </div>

          <div className="md:col-span-2">
            <label className="flex items-center">
              <input
                type="checkbox"
                {...register('is_business')}
                className="rounded border-gray-300 text-primary-600 mr-2"
              />
              <span>Client professionnel (B2B)</span>
            </label>
          </div>
        </div>

        <div className="flex justify-end gap-4 mt-6 pt-6 border-t">
          <button
            type="button"
            onClick={() => navigate('/clients')}
            className="btn-secondary"
          >
            Annuler
          </button>
          <button type="submit" disabled={loading} className="btn-primary">
            {loading ? 'Enregistrement...' : 'Enregistrer'}
          </button>
        </div>
      </form>
    </div>
  )
}
