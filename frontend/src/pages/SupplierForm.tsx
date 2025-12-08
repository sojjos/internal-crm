import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { suppliersApi } from '../services/api'
import toast from 'react-hot-toast'

interface SupplierFormData {
  name: string
  contact_name: string
  address_street: string
  address_city: string
  address_postal_code: string
  address_country: string
  vat_number: string
  email: string
  phone: string
  supplier_type: string
  notes: string
}

export default function SupplierForm() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const isEdit = Boolean(id)

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<SupplierFormData>({
    defaultValues: {
      address_country: 'Belgique',
    },
  })

  useEffect(() => {
    if (isEdit) {
      loadSupplier()
    }
  }, [id])

  const loadSupplier = async () => {
    try {
      const response = await suppliersApi.get(Number(id))
      reset(response.data)
    } catch (error) {
      toast.error('Erreur lors du chargement du fournisseur')
      navigate('/suppliers')
    }
  }

  const onSubmit = async (data: SupplierFormData) => {
    setLoading(true)
    try {
      if (isEdit) {
        await suppliersApi.update(Number(id), data)
        toast.success('Fournisseur mis à jour')
      } else {
        await suppliersApi.create(data)
        toast.success('Fournisseur créé')
      }
      navigate('/suppliers')
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Erreur lors de la sauvegarde')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <h1 className="page-title">
        {isEdit ? 'Modifier le fournisseur' : 'Nouveau fournisseur'}
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
            <label className="label">Type de fournisseur</label>
            <select {...register('supplier_type')} className="input">
              <option value="">-- Sélectionner --</option>
              <option value="materials">Matériaux</option>
              <option value="services">Services</option>
              <option value="fuel">Carburant</option>
              <option value="office">Fournitures bureau</option>
              <option value="other">Autre</option>
            </select>
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
            <label className="label">Numéro de TVA</label>
            <input {...register('vat_number')} className="input" />
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

          <div className="md:col-span-2">
            <label className="label">Notes internes</label>
            <textarea {...register('notes')} className="input" rows={3} />
          </div>
        </div>

        <div className="flex justify-end gap-4 mt-6 pt-6 border-t">
          <button
            type="button"
            onClick={() => navigate('/suppliers')}
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
