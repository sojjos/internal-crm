import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { collaboratorsApi } from '../services/api'
import { PlusIcon, PencilIcon, TrashIcon } from '@heroicons/react/24/outline'
import toast from 'react-hot-toast'

interface Collaborator {
  id: number
  first_name: string
  last_name: string
  email: string | null
  contract_type: string
  manager_type: string | null
  is_active: boolean
}

const contractLabels: Record<string, string> = {
  cdi: 'CDI',
  cdd: 'CDD',
  freelance: 'Freelance',
  intern: 'Stagiaire',
  manager: 'Contrat gérant',
}

export default function Collaborators() {
  const [collaborators, setCollaborators] = useState<Collaborator[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')

  useEffect(() => {
    loadCollaborators()
  }, [])

  const loadCollaborators = async () => {
    try {
      const response = await collaboratorsApi.list({ is_active: true })
      setCollaborators(response.data)
    } catch (error) {
      toast.error('Erreur lors du chargement des collaborateurs')
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (id: number) => {
    if (!confirm('Êtes-vous sûr de vouloir désactiver ce collaborateur ?')) return

    try {
      await collaboratorsApi.delete(id)
      toast.success('Collaborateur désactivé')
      loadCollaborators()
    } catch (error) {
      toast.error('Erreur lors de la désactivation')
    }
  }

  const filteredCollaborators = collaborators.filter(
    (collab) =>
      collab.first_name.toLowerCase().includes(search.toLowerCase()) ||
      collab.last_name.toLowerCase().includes(search.toLowerCase()) ||
      collab.email?.toLowerCase().includes(search.toLowerCase())
  )

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="page-title mb-0">Collaborateurs</h1>
        <Link to="/collaborators/new" className="btn-primary flex items-center">
          <PlusIcon className="h-5 w-5 mr-1" />
          Nouveau collaborateur
        </Link>
      </div>

      <div className="card">
        <div className="mb-4">
          <input
            type="text"
            placeholder="Rechercher un collaborateur..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="input max-w-md"
          />
        </div>

        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead>
              <tr>
                <th className="table-header px-6 py-3">Nom</th>
                <th className="table-header px-6 py-3">Email</th>
                <th className="table-header px-6 py-3">Type de contrat</th>
                <th className="table-header px-6 py-3">Actions</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredCollaborators.map((collab) => (
                <tr key={collab.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap font-medium">
                    {collab.first_name} {collab.last_name}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-gray-500">
                    {collab.email || '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="px-2 py-1 text-xs font-medium rounded-full bg-gray-100">
                      {contractLabels[collab.contract_type] || collab.contract_type}
                    </span>
                    {collab.manager_type && (
                      <span className="ml-2 text-sm text-gray-500">
                        ({collab.manager_type})
                      </span>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <Link
                      to={`/collaborators/${collab.id}`}
                      className="text-primary-600 hover:text-primary-800 mr-3"
                    >
                      <PencilIcon className="h-5 w-5 inline" />
                    </Link>
                    <button
                      onClick={() => handleDelete(collab.id)}
                      className="text-red-600 hover:text-red-800"
                    >
                      <TrashIcon className="h-5 w-5 inline" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {filteredCollaborators.length === 0 && (
            <p className="text-center py-8 text-gray-500">
              Aucun collaborateur trouvé
            </p>
          )}
        </div>
      </div>
    </div>
  )
}
