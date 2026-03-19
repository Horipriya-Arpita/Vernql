'use client'

import { useAuth } from '@/contexts/AuthContext'
import ApiKeyInput from '@/components/ApiKeyInput'
import DashboardLayout from '@/components/DashboardLayout'
import { useState, useEffect } from 'react'
import { apiClient } from '@/lib/api-client'
import type { SchemaDetail } from '@/lib/types'
import { useParams, useRouter } from 'next/navigation'
import Link from 'next/link'
import toast from 'react-hot-toast'
import { ArrowLeft, Database, Table2, Sparkles, Trash2, AlertCircle } from 'lucide-react'

export default function SchemaDetailPage() {
  const { isAuthenticated } = useAuth()
  const params = useParams()
  const router = useRouter()
  const schemaId = params?.id as string

  const [schema, setSchema] = useState<SchemaDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [enriching, setEnriching] = useState(false)

  useEffect(() => {
    if (isAuthenticated && schemaId) {
      loadSchema()
    }
  }, [isAuthenticated, schemaId])

  const loadSchema = async () => {
    try {
      setLoading(true)
      const data = await apiClient.getSchema(schemaId)
      setSchema(data)
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to load schema')
    } finally {
      setLoading(false)
    }
  }

  const handleEnrich = async () => {
    if (!schema) return

    const enrichToast = toast.loading('Enriching schema with AI...')
    try {
      setEnriching(true)
      await apiClient.enrichSchema(schema.id)
      await loadSchema() // Reload to get enriched data
      toast.success('Schema enriched successfully!', { id: enrichToast })
    } catch (err) {
      toast.error(
        err instanceof Error ? err.message : 'Failed to enrich schema',
        { id: enrichToast }
      )
    } finally {
      setEnriching(false)
    }
  }

  const handleDelete = async () => {
    if (!schema || !confirm('Are you sure you want to delete this schema? This action cannot be undone.')) return

    const deleteToast = toast.loading('Deleting schema...')
    try {
      await apiClient.deleteSchema(schema.id)
      toast.success('Schema deleted successfully!', { id: deleteToast })
      router.push('/dashboard/schemas')
    } catch (err) {
      toast.error(
        err instanceof Error ? err.message : 'Failed to delete schema',
        { id: deleteToast }
      )
    }
  }

  if (!isAuthenticated) {
    return <ApiKeyInput />
  }

  return (
    <DashboardLayout>
      <div className="px-4 py-8">
        {/* Header */}
        <div className="mb-6">
          <Link
            href="/dashboard/schemas"
            className="inline-flex items-center text-blue-600 hover:text-blue-700 text-sm mb-2"
          >
            <ArrowLeft className="w-4 h-4 mr-1" />
            Back to Schemas
          </Link>
        </div>

        {loading ? (
          <LoadingSkeleton />
        ) : schema ? (
          <div className="space-y-6">
            {/* Schema Header */}
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-start justify-between mb-4">
                <div>
                  <div className="flex items-center space-x-3 mb-2">
                    <Database className="w-8 h-8 text-blue-600" />
                    <h1 className="text-3xl font-bold text-gray-900">{schema.name}</h1>
                  </div>
                  <div className="flex items-center space-x-4 text-sm text-gray-600">
                    <span className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full font-medium">
                      {schema.db_type.toUpperCase()}
                    </span>
                    <span className="flex items-center">
                      <Table2 className="w-4 h-4 mr-1" />
                      {schema.tables.length} tables
                    </span>
                    <span
                      className={`px-3 py-1 rounded-full font-medium flex items-center ${
                        schema.enriched_description
                          ? 'bg-green-100 text-green-800'
                          : 'bg-yellow-100 text-yellow-800'
                      }`}
                    >
                      {schema.enriched_description ? (
                        <>
                          <Sparkles className="w-3 h-3 mr-1" />
                          Enriched
                        </>
                      ) : (
                        <>
                          <AlertCircle className="w-3 h-3 mr-1" />
                          Not Enriched
                        </>
                      )}
                    </span>
                  </div>
                </div>
                <div className="flex space-x-3">
                  {!schema.enriched_description && (
                    <button
                      onClick={handleEnrich}
                      disabled={enriching}
                      className="inline-flex items-center bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
                    >
                      <Sparkles className="w-4 h-4 mr-2" />
                      {enriching ? 'Enriching...' : 'Enrich with AI'}
                    </button>
                  )}
                  <button
                    onClick={handleDelete}
                    className="inline-flex items-center bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition-colors"
                  >
                    <Trash2 className="w-4 h-4 mr-2" />
                    Delete
                  </button>
                </div>
              </div>

              {schema.enriched_description && (
                <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                  <p className="text-gray-700">{schema.enriched_description}</p>
                </div>
              )}
            </div>

            {/* Tables */}
            <div className="bg-white rounded-lg shadow">
              <div className="px-6 py-4 border-b border-gray-200">
                <h2 className="text-xl font-semibold text-gray-900 flex items-center">
                  <Table2 className="w-5 h-5 mr-2 text-gray-600" />
                  Tables ({schema.tables.length})
                </h2>
              </div>

              <div className="divide-y divide-gray-200">
                {schema.tables.map((table) => (
                  <div key={table.id} className="px-6 py-4">
                    <div className="flex items-start justify-between mb-2">
                      <div>
                        <h3 className="text-lg font-medium text-gray-900 flex items-center">
                          <Table2 className="w-5 h-5 mr-2 text-blue-600" />
                          {table.name}
                        </h3>
                        {table.enriched_description && (
                          <p className="text-sm text-gray-600 mt-1 ml-7">{table.enriched_description}</p>
                        )}
                      </div>
                      <span className="text-sm text-gray-500">{table.columns.length} columns</span>
                    </div>

                    {/* Columns */}
                    <div className="mt-4 bg-gray-50 rounded-lg p-4 ml-7">
                      <table className="min-w-full divide-y divide-gray-200">
                        <thead>
                          <tr>
                            <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                              Column
                            </th>
                            <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                              Type
                            </th>
                            <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                              Description
                            </th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-200">
                          {table.columns.map((column, idx) => (
                            <tr key={`${table.id}-${column.name}-${idx}`}>
                              <td className="px-3 py-2 text-sm font-medium text-gray-900">
                                {column.name}
                                {column.is_primary_key && (
                                  <span className="ml-2 text-xs bg-purple-100 text-purple-800 px-2 py-0.5 rounded">
                                    PK
                                  </span>
                                )}
                                {column.is_foreign_key && (
                                  <span className="ml-2 text-xs bg-blue-100 text-blue-800 px-2 py-0.5 rounded">
                                    FK
                                  </span>
                                )}
                              </td>
                              <td className="px-3 py-2 text-sm text-gray-600">
                                {column.data_type}
                                {column.is_nullable ? '' : ' NOT NULL'}
                              </td>
                              <td className="px-3 py-2 text-sm text-gray-600">
                                {column.enriched_description || <span className="text-gray-400">-</span>}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>

                    {/* Foreign Key Relationships */}
                    {table.columns.some(c => c.is_foreign_key) && (
                      <div className="mt-3 ml-7">
                        <h4 className="text-sm font-medium text-gray-700 mb-2">Foreign Keys:</h4>
                        <div className="space-y-1">
                          {table.columns
                            .filter(c => c.is_foreign_key)
                            .map((column, idx) => (
                              <div key={idx} className="text-sm text-gray-600 flex items-center">
                                <span className="text-blue-600 mr-2">→</span>
                                <code className="bg-gray-100 px-2 py-0.5 rounded text-xs">
                                  {column.name}
                                </code>
                                <span className="mx-2">→</span>
                                <code className="bg-gray-100 px-2 py-0.5 rounded text-xs">
                                  {column.foreign_key_table}.{column.foreign_key_column}
                                </code>
                              </div>
                            ))}
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        ) : (
          <div className="text-center py-12">
            <Database className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <div className="text-gray-500">Schema not found</div>
          </div>
        )}
      </div>
    </DashboardLayout>
  )
}

// Loading skeleton component
function LoadingSkeleton() {
  return (
    <div className="space-y-6 animate-pulse">
      {/* Header skeleton */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-start justify-between mb-4">
          <div className="flex-1">
            <div className="h-8 bg-gray-200 rounded w-1/3 mb-3"></div>
            <div className="flex space-x-4">
              <div className="h-6 bg-gray-200 rounded w-24"></div>
              <div className="h-6 bg-gray-200 rounded w-24"></div>
              <div className="h-6 bg-gray-200 rounded w-32"></div>
            </div>
          </div>
          <div className="flex space-x-3">
            <div className="h-10 bg-gray-200 rounded w-32"></div>
            <div className="h-10 bg-gray-200 rounded w-24"></div>
          </div>
        </div>
      </div>

      {/* Tables skeleton */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="h-6 bg-gray-200 rounded w-32"></div>
        </div>
        <div className="px-6 py-4 space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i}>
              <div className="h-5 bg-gray-200 rounded w-48 mb-2"></div>
              <div className="h-32 bg-gray-100 rounded"></div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
