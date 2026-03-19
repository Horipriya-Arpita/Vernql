'use client'

import { useAuth } from '@/contexts/AuthContext'
import ApiKeyInput from '@/components/ApiKeyInput'
import DashboardLayout from '@/components/DashboardLayout'
import SchemaUpload from '@/components/SchemaUpload'
import { useState, useEffect } from 'react'
import { apiClient } from '@/lib/api-client'
import type { Schema } from '@/lib/types'
import Link from 'next/link'

export default function SchemasPage() {
  const { isAuthenticated } = useAuth()
  const [schemas, setSchemas] = useState<Schema[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    if (isAuthenticated) {
      loadSchemas()
    }
  }, [isAuthenticated])

  const loadSchemas = async () => {
    try {
      setLoading(true)
      const response = await apiClient.listSchemas()
      setSchemas(response.schemas)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load schemas')
    } finally {
      setLoading(false)
    }
  }

  if (!isAuthenticated) {
    return <ApiKeyInput />
  }

  return (
    <DashboardLayout>
      <div className="px-4 py-8">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Database Schemas</h1>
        </div>

        {/* Upload Section */}
        <div className="mb-8">
          <SchemaUpload onUploadSuccess={loadSchemas} />
        </div>

        {/* Schemas List */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-xl font-semibold text-gray-900">Your Schemas</h2>
          </div>

          {loading ? (
            <div className="px-6 py-8 text-center text-gray-500">Loading schemas...</div>
          ) : error ? (
            <div className="px-6 py-8 text-center text-red-600">{error}</div>
          ) : schemas.length === 0 ? (
            <div className="px-6 py-8 text-center text-gray-500">
              No schemas uploaded yet. Upload your first schema above!
            </div>
          ) : (
            <div className="divide-y divide-gray-200">
              {schemas.map((schema) => (
                <Link
                  key={schema.id}
                  href={`/dashboard/schemas/${schema.id}`}
                  className="block px-6 py-4 hover:bg-gray-50 transition-colors"
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-lg font-medium text-gray-900">{schema.name}</h3>
                      <p className="text-sm text-gray-500 mt-1">
                        {schema.db_type.toUpperCase()} • {schema.table_count} tables
                      </p>
                    </div>
                    <div className="text-right">
                      <span
                        className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
                          schema.is_enriched
                            ? 'bg-green-100 text-green-800'
                            : 'bg-yellow-100 text-yellow-800'
                        }`}
                      >
                        {schema.is_enriched ? 'Enriched' : 'Not Enriched'}
                      </span>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>
      </div>
    </DashboardLayout>
  )
}
