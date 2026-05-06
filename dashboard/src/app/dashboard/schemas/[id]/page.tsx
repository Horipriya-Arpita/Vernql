'use client'

import { useAuth } from '@/contexts/AuthContext'
import ApiKeyInput from '@/components/ApiKeyInput'
import DashboardLayout from '@/components/DashboardLayout'
import EditableDescription from '@/components/EditableDescription'
import { useState, useEffect, useRef, useCallback } from 'react'
import { apiClient } from '@/lib/api-client'
import type { SchemaDetail } from '@/lib/types'
import { useParams, useRouter } from 'next/navigation'
import Link from 'next/link'
import toast from 'react-hot-toast'
import { ArrowLeft, Database, Table2, Sparkles, Trash2, AlertCircle, Copy, Check } from 'lucide-react'

export default function SchemaDetailPage() {
  const { isAuthenticated } = useAuth()
  const params = useParams()
  const router = useRouter()
  const schemaId = params?.id as string

  const [schema, setSchema] = useState<SchemaDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [enriching, setEnriching] = useState(false)
  const [copiedId, setCopiedId] = useState(false)
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const handleCopyId = () => {
    navigator.clipboard.writeText(schemaId)
    setCopiedId(true)
    setTimeout(() => setCopiedId(false), 2000)
  }

  const loadSchema = useCallback(async () => {
    try {
      setLoading(true)
      const data = await apiClient.getSchema(schemaId)
      setSchema(data)
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to load schema')
    } finally {
      setLoading(false)
    }
  }, [schemaId])

  useEffect(() => {
    if (isAuthenticated && schemaId) loadSchema()
  }, [isAuthenticated, schemaId, loadSchema])

  // Poll every 3 s while a background enrichment is in progress
  useEffect(() => {
    const status = schema?.enrichment_status
    const isEnriching = schema !== null && (status === 'pending' || status === 'running')

    if (!isEnriching) {
      if (pollRef.current) {
        clearInterval(pollRef.current)
        pollRef.current = null
      }
      return
    }

    if (pollRef.current) return  // already polling

    pollRef.current = setInterval(async () => {
      try {
        const updated = await apiClient.getSchema(schemaId)
        setSchema(updated)
        if (updated.enrichment_status === 'complete') {
          clearInterval(pollRef.current!)
          pollRef.current = null
          toast.success('AI enrichment complete!')
        } else if (updated.enrichment_status === 'failed') {
          clearInterval(pollRef.current!)
          pollRef.current = null
          toast.error('AI enrichment failed. You can retry using the button above.')
        }
      } catch {
        // silent — don't interrupt the user
      }
    }, 3000)

    return () => {
      if (pollRef.current) {
        clearInterval(pollRef.current)
        pollRef.current = null
      }
    }
  }, [schema?.enrichment_status, schemaId])

  const handleEnrich = async () => {
    if (!schema) return
    const enrichToast = toast.loading('Enriching schema with AI…')
    try {
      setEnriching(true)
      await apiClient.enrichSchema(schema.id)
      await loadSchema()
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
    if (
      !schema ||
      !confirm('Are you sure you want to delete this schema? This action cannot be undone.')
    )
      return
    const deleteToast = toast.loading('Deleting schema…')
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

  // -----------------------------------------------------------------------
  // Optimistic description updaters (avoid full reload on each inline save)
  // -----------------------------------------------------------------------

  const handleSaveSchemaDescription = async (text: string) => {
    const result = await apiClient.updateSchemaDescription(schemaId, text)
    setSchema((prev) =>
      prev
        ? {
            ...prev,
            enriched_description: result.enriched_description,
            description_source: (result as any).description_source ?? 'user',
          }
        : prev
    )
    toast.success('Schema description updated')
  }

  const handleSaveTableDescription = (tableId: string) => async (text: string) => {
    const result = await apiClient.updateTableDescription(schemaId, tableId, text)
    setSchema((prev) => {
      if (!prev) return prev
      return {
        ...prev,
        tables: prev.tables.map((t) =>
          t.id === tableId
            ? { ...t, enriched_description: result.enriched_description, description_source: result.description_source }
            : t
        ),
      }
    })
    toast.success('Table description updated')
  }

  const handleSaveColumnDescription =
    (tableId: string, columnId: string) => async (text: string) => {
      const result = await apiClient.updateColumnDescription(schemaId, tableId, columnId, text)
      setSchema((prev) => {
        if (!prev) return prev
        return {
          ...prev,
          tables: prev.tables.map((t) =>
            t.id === tableId
              ? {
                  ...t,
                  columns: t.columns.map((c) =>
                    c.id === columnId
                      ? {
                          ...c,
                          enriched_description: result.enriched_description,
                          description_source: result.description_source,
                        }
                      : c
                  ),
                }
              : t
          ),
        }
      })
    }

  if (!isAuthenticated) return <ApiKeyInput />

  return (
    <DashboardLayout>
      <div className="px-4 py-8">
        {/* Back link */}
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
                <div className="flex-1 min-w-0">
                  <div className="flex items-center space-x-3 mb-2">
                    <Database className="w-8 h-8 text-blue-600 shrink-0" />
                    <h1 className="text-3xl font-bold text-gray-900 truncate">{schema.name}</h1>
                  </div>
                  <div className="flex items-center flex-wrap gap-3 text-sm text-gray-600">
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
                  <div className="flex items-center gap-2 mt-2">
                    <span className="text-xs text-gray-500 font-medium">Schema ID:</span>
                    <code className="font-mono text-xs text-gray-600 bg-gray-100 px-2 py-0.5 rounded select-all">
                      {schemaId}
                    </code>
                    <button
                      onClick={handleCopyId}
                      className="text-gray-400 hover:text-gray-600 transition-colors"
                      title="Copy schema ID"
                    >
                      {copiedId
                        ? <Check className="w-3.5 h-3.5 text-green-500" />
                        : <Copy className="w-3.5 h-3.5" />}
                    </button>
                  </div>
                </div>

                <div className="flex space-x-3 ml-4 shrink-0">
                  <button
                    onClick={handleEnrich}
                    disabled={enriching}
                    className="inline-flex items-center bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed text-sm"
                  >
                    <Sparkles className="w-4 h-4 mr-2" />
                    {enriching ? 'Enriching…' : schema.enriched_description ? 'Re-enrich' : 'Enrich with AI'}
                  </button>
                  <button
                    onClick={handleDelete}
                    className="inline-flex items-center bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition-colors text-sm"
                  >
                    <Trash2 className="w-4 h-4 mr-2" />
                    Delete
                  </button>
                </div>
              </div>

              {/* Background enrichment status banner */}
              {(schema.enrichment_status === 'pending' || schema.enrichment_status === 'running') && (
                <div className="mt-4 flex items-center gap-3 px-4 py-3 bg-amber-50 border border-amber-200 rounded-lg text-sm text-amber-800">
                  <svg className="animate-spin h-4 w-4 text-amber-600 shrink-0" viewBox="0 0 24 24" fill="none">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
                  </svg>
                  AI is generating descriptions for your schema in the background. This page will update automatically.
                </div>
              )}
              {schema.enrichment_status === 'failed' && (
                <div className="mt-4 px-4 py-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-800">
                  <div className="flex items-center gap-2 font-medium mb-1">
                    <AlertCircle className="w-4 h-4 shrink-0" />
                    AI enrichment failed
                  </div>
                  {schema.enrichment_error && (
                    <p className="text-xs text-red-600 mt-1 font-mono">{schema.enrichment_error}</p>
                  )}
                  <p className="mt-2 text-xs text-red-700">Use the &ldquo;Re-enrich&rdquo; button above to try again.</p>
                </div>
              )}

              {/* Schema-level editable description */}
              <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <p className="text-xs font-medium text-blue-700 mb-2 uppercase tracking-wide">
                  Schema Description
                </p>
                <EditableDescription
                  description={schema.enriched_description}
                  source={(schema as any).description_source}
                  onSave={handleSaveSchemaDescription}
                  placeholder="No schema description yet — click to add one, or use Enrich with AI"
                />
              </div>
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
                  <div key={table.id} className="px-6 py-5">
                    {/* Table name + editable description */}
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex-1 min-w-0">
                        <h3 className="text-lg font-semibold text-gray-900 flex items-center mb-1">
                          <Table2 className="w-5 h-5 mr-2 text-blue-600 shrink-0" />
                          {table.name}
                        </h3>
                        <div className="ml-7">
                          <EditableDescription
                            description={table.enriched_description}
                            source={table.description_source}
                            onSave={handleSaveTableDescription(table.id)}
                            placeholder="No table description — click to add one"
                          />
                        </div>
                      </div>
                      <span className="ml-4 text-sm text-gray-400 shrink-0 mt-1">
                        {table.columns.length} columns
                      </span>
                    </div>

                    {/* Columns table */}
                    <div className="mt-3 bg-gray-50 rounded-lg overflow-hidden ml-7">
                      <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-100">
                          <tr>
                            <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wide w-40">
                              Column
                            </th>
                            <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wide w-36">
                              Type
                            </th>
                            <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wide">
                              Description
                              <span className="ml-2 normal-case font-normal text-gray-400">
                                (click to edit)
                              </span>
                            </th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-200 bg-white">
                          {table.columns.map((column) => (
                            <tr key={column.id} className="hover:bg-gray-50 transition-colors">
                              <td className="px-3 py-2 text-sm font-medium text-gray-900 align-top">
                                <div className="flex flex-wrap gap-1 items-center">
                                  {column.name}
                                  {column.is_primary_key && (
                                    <span className="text-xs bg-purple-100 text-purple-800 px-1.5 py-0.5 rounded">
                                      PK
                                    </span>
                                  )}
                                  {column.is_foreign_key && (
                                    <span className="text-xs bg-blue-100 text-blue-800 px-1.5 py-0.5 rounded">
                                      FK
                                    </span>
                                  )}
                                </div>
                              </td>
                              <td className="px-3 py-2 text-sm text-gray-500 align-top font-mono">
                                {column.data_type}
                                {!column.is_nullable && (
                                  <span className="block text-xs text-gray-400">NOT NULL</span>
                                )}
                              </td>
                              <td className="px-3 py-2 align-top">
                                <EditableDescription
                                  description={column.enriched_description}
                                  source={column.description_source}
                                  onSave={handleSaveColumnDescription(table.id, column.id)}
                                  placeholder="—"
                                  compact
                                />
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>

                    {/* Foreign Key Relationships */}
                    {table.columns.some((c) => c.is_foreign_key) && (
                      <div className="mt-3 ml-7">
                        <h4 className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">
                          Foreign Keys
                        </h4>
                        <div className="space-y-1">
                          {table.columns
                            .filter((c) => c.is_foreign_key)
                            .map((column) => (
                              <div
                                key={column.id}
                                className="text-sm text-gray-600 flex items-center gap-2"
                              >
                                <span className="text-blue-500">→</span>
                                <code className="bg-gray-100 px-2 py-0.5 rounded text-xs">
                                  {column.name}
                                </code>
                                <span className="text-gray-400">→</span>
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

function LoadingSkeleton() {
  return (
    <div className="space-y-6 animate-pulse">
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-start justify-between mb-4">
          <div className="flex-1">
            <div className="h-8 bg-gray-200 rounded w-1/3 mb-3" />
            <div className="flex gap-3">
              <div className="h-6 bg-gray-200 rounded w-24" />
              <div className="h-6 bg-gray-200 rounded w-24" />
              <div className="h-6 bg-gray-200 rounded w-32" />
            </div>
          </div>
          <div className="flex gap-3">
            <div className="h-10 bg-gray-200 rounded w-36" />
            <div className="h-10 bg-gray-200 rounded w-24" />
          </div>
        </div>
        <div className="h-16 bg-gray-100 rounded mt-4" />
      </div>
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="h-6 bg-gray-200 rounded w-32" />
        </div>
        <div className="px-6 py-4 space-y-6">
          {[1, 2, 3].map((i) => (
            <div key={i}>
              <div className="h-5 bg-gray-200 rounded w-48 mb-3" />
              <div className="h-40 bg-gray-100 rounded" />
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}