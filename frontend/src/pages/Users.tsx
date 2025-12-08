import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { usersApi } from '../services/api'
import { useAuth } from '../context/AuthContext'
import { PlusIcon, PencilIcon, TrashIcon } from '@heroicons/react/24/outline'
import toast from 'react-hot-toast'

interface User {
  id: number
  email: string
  first_name: string
  last_name: string
  is_active: boolean
  last_login: string | null
}

export default function Users() {
  const [users, setUsers] = useState<User[]>([])
  const [loading, setLoading] = useState(true)
  const { user: currentUser } = useAuth()

  useEffect(() => {
    loadUsers()
  }, [])

  const loadUsers = async () => {
    try {
      const response = await usersApi.list()
      setUsers(response.data)
    } catch (error) {
      toast.error('Erreur lors du chargement des utilisateurs')
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (id: number) => {
    if (!confirm('Êtes-vous sûr de vouloir désactiver cet utilisateur ?')) return

    try {
      await usersApi.delete(id)
      toast.success('Utilisateur désactivé')
      loadUsers()
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Erreur')
    }
  }

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return 'Jamais'
    return new Date(dateStr).toLocaleString('fr-BE')
  }

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
        <h1 className="page-title mb-0">Utilisateurs (Gérants)</h1>
        <Link to="/users/new" className="btn-primary flex items-center">
          <PlusIcon className="h-5 w-5 mr-1" />
          Nouveau gérant
        </Link>
      </div>

      <div className="card">
        <p className="text-sm text-gray-500 mb-4">
          Tous les utilisateurs sont des gérants avec accès complet à l'application.
        </p>

        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead>
              <tr>
                <th className="table-header px-6 py-3">Nom</th>
                <th className="table-header px-6 py-3">Email</th>
                <th className="table-header px-6 py-3">Statut</th>
                <th className="table-header px-6 py-3">Dernière connexion</th>
                <th className="table-header px-6 py-3">Actions</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {users.map((user) => (
                <tr key={user.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap font-medium">
                    {user.first_name} {user.last_name}
                    {user.id === currentUser?.id && (
                      <span className="ml-2 text-xs text-primary-600">(vous)</span>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-gray-500">
                    {user.email}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span
                      className={`px-2 py-1 text-xs font-medium rounded-full ${
                        user.is_active
                          ? 'bg-green-100 text-green-800'
                          : 'bg-gray-100 text-gray-500'
                      }`}
                    >
                      {user.is_active ? 'Actif' : 'Inactif'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-gray-500 text-sm">
                    {formatDate(user.last_login)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <Link
                      to={`/users/${user.id}`}
                      className="text-primary-600 hover:text-primary-800 mr-3"
                    >
                      <PencilIcon className="h-5 w-5 inline" />
                    </Link>
                    {user.id !== currentUser?.id && (
                      <button
                        onClick={() => handleDelete(user.id)}
                        className="text-red-600 hover:text-red-800"
                      >
                        <TrashIcon className="h-5 w-5 inline" />
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
