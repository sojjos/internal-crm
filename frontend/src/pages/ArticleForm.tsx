import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { articlesApi } from '../services/api'
import toast from 'react-hot-toast'

interface ArticleFormData {
  code: string
  name: string
  description: string
  article_type: string
  billing_mode: string
  base_price: number
  default_vat_rate: number
  allow_price_modification: boolean
  allow_discount: boolean
}

export default function ArticleForm() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const isEdit = Boolean(id)

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<ArticleFormData>({
    defaultValues: {
      article_type: 'service',
      billing_mode: 'hour',
      default_vat_rate: 21,
      allow_price_modification: true,
      allow_discount: true,
    },
  })

  useEffect(() => {
    if (isEdit) {
      loadArticle()
    }
  }, [id])

  const loadArticle = async () => {
    try {
      const response = await articlesApi.get(Number(id))
      reset(response.data)
    } catch (error) {
      toast.error("Erreur lors du chargement de l'article")
      navigate('/articles')
    }
  }

  const onSubmit = async (data: ArticleFormData) => {
    setLoading(true)
    try {
      if (isEdit) {
        await articlesApi.update(Number(id), data)
        toast.success('Article mis à jour')
      } else {
        await articlesApi.create(data)
        toast.success('Article créé')
      }
      navigate('/articles')
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Erreur lors de la sauvegarde')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <h1 className="page-title">
        {isEdit ? "Modifier l'article" : 'Nouvel article'}
      </h1>

      <form onSubmit={handleSubmit(onSubmit)} className="card max-w-3xl">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="label">Code article *</label>
            <input
              {...register('code', { required: 'Ce champ est requis' })}
              className="input font-mono"
              placeholder="SERV-001"
            />
            {errors.code && (
              <p className="text-red-500 text-sm mt-1">{errors.code.message}</p>
            )}
          </div>

          <div>
            <label className="label">Nom *</label>
            <input
              {...register('name', { required: 'Ce champ est requis' })}
              className="input"
            />
            {errors.name && (
              <p className="text-red-500 text-sm mt-1">{errors.name.message}</p>
            )}
          </div>

          <div className="md:col-span-2">
            <label className="label">Description</label>
            <textarea {...register('description')} className="input" rows={3} />
          </div>

          <div>
            <label className="label">Type</label>
            <select {...register('article_type')} className="input">
              <option value="service">Service</option>
              <option value="product">Produit</option>
              <option value="expense">Frais</option>
            </select>
          </div>

          <div>
            <label className="label">Mode de facturation</label>
            <select {...register('billing_mode')} className="input">
              <option value="hour">À l'heure</option>
              <option value="day">À la journée</option>
              <option value="unit">À l'unité</option>
              <option value="km">Au kilomètre</option>
              <option value="flat">Forfait</option>
            </select>
          </div>

          <div>
            <label className="label">Prix de base (HTVA) *</label>
            <input
              type="number"
              step="0.01"
              {...register('base_price', {
                required: 'Ce champ est requis',
                valueAsNumber: true,
              })}
              className="input"
            />
            {errors.base_price && (
              <p className="text-red-500 text-sm mt-1">
                {errors.base_price.message}
              </p>
            )}
          </div>

          <div>
            <label className="label">Taux de TVA par défaut (%)</label>
            <select
              {...register('default_vat_rate', { valueAsNumber: true })}
              className="input"
            >
              <option value={21}>21%</option>
              <option value={12}>12%</option>
              <option value={6}>6%</option>
              <option value={0}>0%</option>
            </select>
          </div>

          <div className="md:col-span-2 space-y-3">
            <label className="flex items-center">
              <input
                type="checkbox"
                {...register('allow_price_modification')}
                className="rounded border-gray-300 text-primary-600 mr-2"
              />
              <span>Autoriser la modification du prix sur la facture</span>
            </label>

            <label className="flex items-center">
              <input
                type="checkbox"
                {...register('allow_discount')}
                className="rounded border-gray-300 text-primary-600 mr-2"
              />
              <span>Autoriser les remises</span>
            </label>
          </div>
        </div>

        <div className="flex justify-end gap-4 mt-6 pt-6 border-t">
          <button
            type="button"
            onClick={() => navigate('/articles')}
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
