import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { usersApi, authApi } from '../services/api'
import toast from 'react-hot-toast'

interface UserFormData {
  email: string
  first_name: string
  last_name: string
  phone: string
  password: string
}

export default function UserForm() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const isEdit = Boolean(id)

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<UserFormData>()

  useEffect(() => {
    if (isEdit) {
      loadUser()
    }
  }, [id])

  const loadUser = async () => {
    try {
      const response = await usersApi.get(Number(id))
      reset(response.data)
    } catch (error) {
      toast.error("Erreur lors du chargement de l'utilisateur")
      navigate('/users')
    }
  }

  const onSubmit = async (data: UserFormData) => {
    setLoading(true)
    try {
      if (isEdit) {
        // Don't send password if empty
        const updateData = { ...data }
        if (!updateData.password) {
          delete (updateData as any).password
        }
        await usersApi.update(Number(id), updateData)
        toast.success('Utilisateur mis à jour')
      } else {
        await authApi.register(data)
        toast.success('Utilisateur créé')
      }
      navigate('/users')
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Erreur lors de la sauvegarde')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <h1 className="page-title">
        {isEdit ? "Modifier l'utilisateur" : 'Nouveau gérant'}
      </h1>

      <form onSubmit={handleSubmit(onSubmit)} className="card max-w-xl">
        <div className="space-y-6">
          <div>
            <label className="label">Email *</label>
            <input
              type="email"
              {...register('email', { required: 'Ce champ est requis' })}
              className="input"
            />
            {errors.email && (
              <p className="text-red-500 text-sm mt-1">{errors.email.message}</p>
            )}
          </div>

          <div className="grid grid-cols-2 gap-4">
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
          </div>

          <div>
            <label className="label">Téléphone</label>
            <input {...register('phone')} className="input" />
          </div>

          <div>
            <label className="label">
              Mot de passe {isEdit ? '(laisser vide pour ne pas changer)' : '*'}
            </label>
            <input
              type="password"
              {...register('password', {
                required: isEdit ? false : 'Ce champ est requis',
                minLength: isEdit
                  ? undefined
                  : { value: 8, message: 'Minimum 8 caractères' },
              })}
              className="input"
            />
            {errors.password && (
              <p className="text-red-500 text-sm mt-1">{errors.password.message}</p>
            )}
          </div>
        </div>

        <div className="flex justify-end gap-4 mt-6 pt-6 border-t">
          <button
            type="button"
            onClick={() => navigate('/users')}
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
