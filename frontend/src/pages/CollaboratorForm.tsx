import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { collaboratorsApi } from '../services/api'
import toast from 'react-hot-toast'

interface CollaboratorFormData {
  first_name: string
  last_name: string
  email: string
  phone: string
  address_street: string
  address_city: string
  address_postal_code: string
  address_country: string
  contract_type: string
  manager_type: string
  start_date: string
  end_date: string
  gross_salary: number | null
  hourly_rate: number | null
  iban: string
  notes: string
  create_user_account: boolean
  user_password: string
}

export default function CollaboratorForm() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const isEdit = Boolean(id)

  const {
    register,
    handleSubmit,
    watch,
    reset,
    formState: { errors },
  } = useForm<CollaboratorFormData>({
    defaultValues: {
      address_country: 'Belgique',
      contract_type: 'cdi',
      create_user_account: false,
      user_password: '',
    },
  })

  const contractType = watch('contract_type')
  const createUserAccount = watch('create_user_account')

  useEffect(() => {
    if (isEdit) {
      loadCollaborator()
    }
  }, [id])

  const loadCollaborator = async () => {
    try {
      const response = await collaboratorsApi.get(Number(id))
      reset(response.data)
    } catch (error) {
      toast.error('Erreur lors du chargement du collaborateur')
      navigate('/collaborators')
    }
  }

  const onSubmit = async (data: CollaboratorFormData) => {
    setLoading(true)
    try {
      if (isEdit) {
        await collaboratorsApi.update(Number(id), data)
        toast.success('Collaborateur mis à jour')
      } else {
        await collaboratorsApi.create(data)
        toast.success('Collaborateur créé')
      }
      navigate('/collaborators')
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Erreur lors de la sauvegarde')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <h1 className="page-title">
        {isEdit ? 'Modifier le collaborateur' : 'Nouveau collaborateur'}
      </h1>

      <form onSubmit={handleSubmit(onSubmit)} className="card max-w-3xl">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="label">Prénom *</label>
            <input
              {...register('first_name', { required: 'Ce champ est requis' })}
              className="input"
            />
            {errors.first_name && (
              <p className="text-red-500 text-sm mt-1">
                {errors.first_name.message}
              </p>
            )}
          </div>

          <div>
            <label className="label">Nom *</label>
            <input
              {...register('last_name', { required: 'Ce champ est requis' })}
              className="input"
            />
            {errors.last_name && (
              <p className="text-red-500 text-sm mt-1">
                {errors.last_name.message}
              </p>
            )}
          </div>

          <div>
            <label className="label">Email</label>
            <input type="email" {...register('email')} className="input" />
          </div>

          <div>
            <label className="label">Téléphone</label>
            <input {...register('phone')} className="input" />
          </div>

          <div>
            <label className="label">Type de contrat</label>
            <select {...register('contract_type')} className="input">
              <option value="cdi">CDI</option>
              <option value="cdd">CDD</option>
              <option value="freelance">Freelance / Indépendant</option>
              <option value="intern">Stagiaire</option>
              <option value="manager">Contrat gérant</option>
            </select>
          </div>

          {contractType === 'manager' && (
            <div>
              <label className="label">Type de gérant</label>
              <input
                {...register('manager_type')}
                className="input"
                placeholder="Ex: gérant actif, administrateur..."
              />
            </div>
          )}

          <div>
            <label className="label">Date d'entrée</label>
            <input type="date" {...register('start_date')} className="input" />
          </div>

          <div>
            <label className="label">Date de sortie</label>
            <input type="date" {...register('end_date')} className="input" />
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
            <label className="label">Salaire brut mensuel (info)</label>
            <input
              type="number"
              step="0.01"
              {...register('gross_salary', { valueAsNumber: true })}
              className="input"
            />
          </div>

          <div>
            <label className="label">Taux horaire (info)</label>
            <input
              type="number"
              step="0.01"
              {...register('hourly_rate', { valueAsNumber: true })}
              className="input"
            />
          </div>

          <div>
            <label className="label">IBAN</label>
            <input {...register('iban')} className="input font-mono" />
          </div>

          <div className="md:col-span-2">
            <label className="label">Notes internes</label>
            <textarea {...register('notes')} className="input" rows={3} />
          </div>

          {/* Section compte utilisateur - uniquement lors de la création */}
          {!isEdit && (
            <div className="md:col-span-2 border-t pt-4 mt-2">
              <h3 className="text-lg font-medium mb-4">Accès au système</h3>

              <div className="flex items-center mb-4">
                <input
                  type="checkbox"
                  id="create_user_account"
                  {...register('create_user_account')}
                  className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                />
                <label htmlFor="create_user_account" className="ml-2 text-sm text-gray-700">
                  Créer un compte utilisateur pour ce collaborateur
                </label>
              </div>

              {createUserAccount && (
                <div className="ml-6 space-y-4">
                  <p className="text-sm text-gray-500">
                    L'email du collaborateur sera utilisé comme identifiant de connexion.
                  </p>
                  <div>
                    <label className="label">Mot de passe (optionnel)</label>
                    <input
                      type="password"
                      {...register('user_password')}
                      className="input"
                      placeholder="Laissez vide pour 'changeme123'"
                    />
                    <p className="text-xs text-gray-500 mt-1">
                      Si laissé vide, le mot de passe par défaut sera "changeme123"
                    </p>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        <div className="flex justify-end gap-4 mt-6 pt-6 border-t">
          <button
            type="button"
            onClick={() => navigate('/collaborators')}
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
