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

  // Poll every 3 s while background enrichment is in progress
  useEffect(() => {
    const status = schema?.enrichment_status
    const isEnriching = schema !== null && (status === 'pending' || status === 'running')

    if (!isEnriching) {
      if (pollRef.current) { clearInterval(pollRef.current); pollRef.current = null }
      return
    }
    if (pollRef.current) return

    pollRef.current = setInterval(async () => {
      try {
        const updated = await apiClient.getSchema(schemaId)
        setSchema(updated)
        if (updated.enrichment_status === 'complete') {
          clearInterval(pollRef.current!); pollRef.current = null
          toast.success('AI enrichment complete!')
        } else if (updated.enrichment_status === 'failed') {
          clearInterval(pollRef.current!); pollRef.current = null
          toast.error('AI enrichment failed. You can retry using the button above.')
        }
      } catch { /* silent */ }
    }, 3000)

    return () => { if (pollRef.current) { clearInterval(pollRef.current); pollRef.current = null } }
  }, [schema?.enrichment_status, schemaId])

  const handleEnrich = async () => {
    if (!schema) return
    const t = toast.loading('Enriching schema with AI…')
    try {
      setEnriching(true)
      await apiClient.enrichSchema(schema.id)
      await loadSchema()
      toast.success('Schema enriched successfully!', { id: t })
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to enrich schema', { id: t })
    } finally { setEnriching(false) }
  }

  const handleDelete = async () => {
    if (!schema || !confirm('Are you sure you want to delete this schema? This action cannot be undone.')) return
    const t = toast.loading('Deleting schema…')
    try {
      await apiClient.deleteSchema(schema.id)
      toast.success('Schema deleted successfully!', { id: t })
      router.push('/dashboard/schemas')
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to delete schema', { id: t })
    }
  }

  const handleSaveSchemaDescription = async (text: string) => {
    const result = await apiClient.updateSchemaDescription(schemaId, text)
    setSchema(prev => prev ? {
      ...prev,
      enriched_description: result.enriched_description,
      description_source: (result as any).description_source ?? 'user',
    } : prev)
    toast.success('Schema description updated')
  }

  const handleSaveTableDescription = (tableId: string) => async (text: string) => {
    const result = await apiClient.updateTableDescription(schemaId, tableId, text)
    setSchema(prev => !prev ? prev : {
      ...prev,
      tables: prev.tables.map(t =>
        t.id === tableId
          ? { ...t, enriched_description: result.enriched_description, description_source: result.description_source }
          : t
      ),
    })
    toast.success('Table description updated')
  }

  const handleSaveColumnDescription = (tableId: string, columnId: string) => async (text: string) => {
    const result = await apiClient.updateColumnDescription(schemaId, tableId, columnId, text)
    setSchema(prev => !prev ? prev : {
      ...prev,
      tables: prev.tables.map(t =>
        t.id === tableId
          ? {
              ...t,
              columns: t.columns.map(c =>
                c.id === columnId
                  ? { ...c, enriched_description: result.enriched_description, description_source: result.description_source }
                  : c
              ),
            }
          : t
      ),
    })
  }

  if (!isAuthenticated) return <ApiKeyInput />

  return (
    <DashboardLayout>
      <div>
        {/* ── Back link ── */}
        <div className="mb-6">
          <Link
            href="/dashboard/schemas"
            className="inline-flex items-center gap-1.5 text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 text-sm font-medium transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Schemas
          </Link>
        </div>

        {loading ? (
          <LoadingSkeleton />
        ) : schema ? (
          <div className="space-y-5">

            {/* ── Schema header card ── */}
            <div className="bg-white dark:bg-slate-800/70 rounded-2xl border border-slate-100 dark:border-slate-700/50 p-6">
              <div className="flex items-start justify-between gap-4 mb-4">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-3 mb-2.5">
                    <Database className="w-8 h-8 text-blue-600 dark:text-blue-400 flex-shrink-0" />
                    <h1 className="text-3xl font-bold text-slate-900 dark:text-white tracking-tight truncate">
                      {schema.name}
                    </h1>
                  </div>

                  {/* Metadata badges */}
                  <div className="flex items-center flex-wrap gap-2 text-sm">
                    <span className="px-2.5 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300 rounded-full font-medium text-xs">
                      {schema.db_type.toUpperCase()}
                    </span>
                    <span className="flex items-center gap-1 text-slate-500 dark:text-slate-400">
                      <Table2 className="w-4 h-4" />
                      {schema.tables.length} tables
                    </span>
                    <span className={`px-2.5 py-1 rounded-full text-xs font-medium flex items-center gap-1 ${
                      schema.enriched_description
                        ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300'
                        : 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300'
                    }`}>
                      {schema.enriched_description
                        ? <><Sparkles className="w-3 h-3" /> Enriched</>
                        : <><AlertCircle className="w-3 h-3" /> Not Enriched</>}
                    </span>
                  </div>

                  {/* Schema ID */}
                  <div className="flex items-center gap-2 mt-2.5">
                    <span className="text-xs text-slate-500 dark:text-slate-400 font-medium">Schema ID:</span>
                    <code className="font-mono text-xs text-slate-600 dark:text-slate-400 bg-slate-100 dark:bg-slate-700 px-2 py-0.5 rounded select-all">
                      {schemaId}
                    </code>
                    <button
                      onClick={handleCopyId}
                      className="text-slate-400 dark:text-slate-500 hover:text-slate-600 dark:hover:text-slate-300 transition-colors"
                      title="Copy schema ID"
                    >
                      {copiedId
                        ? <Check className="w-3.5 h-3.5 text-green-500" />
                        : <Copy className="w-3.5 h-3.5" />}
                    </button>
                  </div>
                </div>

                {/* Action buttons */}
                <div className="flex gap-2.5 flex-shrink-0">
                  <button
                    onClick={handleEnrich}
                    disabled={enriching}
                    className="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-xl font-medium text-sm shadow-blue-sm disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    <Sparkles className="w-4 h-4" />
                    {enriching ? 'Enriching…' : schema.enriched_description ? 'Re-enrich' : 'Enrich with AI'}
                  </button>
                  <button
                    onClick={handleDelete}
                    className="inline-flex items-center gap-2 bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-xl font-medium text-sm transition-colors"
                  >
                    <Trash2 className="w-4 h-4" />
                    Delete
                  </button>
                </div>
              </div>

              {/* Background enrichment status */}
              {(schema.enrichment_status === 'pending' || schema.enrichment_status === 'running') && (
                <div className="mt-4 flex items-center gap-3 px-4 py-3 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800/40 rounded-xl text-sm text-amber-800 dark:text-amber-300">
                  <svg className="animate-spin h-4 w-4 text-amber-600 dark:text-amber-400 flex-shrink-0" viewBox="0 0 24 24" fill="none">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
                  </svg>
                  AI is generating descriptions for your schema in the background. This page will update automatically.
                </div>
              )}
              {schema.enrichment_status === 'failed' && (
                <div className="mt-4 px-4 py-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800/40 rounded-xl text-sm">
                  <div className="flex items-center gap-2 font-medium text-red-800 dark:text-red-300 mb-1">
                    <AlertCircle className="w-4 h-4 flex-shrink-0" />
                    AI enrichment failed
                  </div>
                  {schema.enrichment_error && (
                    <p className="text-xs text-red-600 dark:text-red-400 mt-1 font-mono">{schema.enrichment_error}</p>
                  )}
                  <p className="mt-1.5 text-xs text-red-700 dark:text-red-400">Use the &ldquo;Re-enrich&rdquo; button above to try again.</p>
                </div>
              )}

              {/* Schema-level description */}
              <div className="mt-4 p-4 bg-blue-50 dark:bg-blue-900/15 border border-blue-200 dark:border-blue-800/30 rounded-xl">
                <p className="text-xs font-semibold text-blue-700 dark:text-blue-400 mb-2 uppercase tracking-wide">
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

            {/* ── Tables card ── */}
            <div className="bg-white dark:bg-slate-800/70 rounded-2xl border border-slate-100 dark:border-slate-700/50">
              <div className="px-6 py-4 border-b border-slate-100 dark:border-slate-700/50">
                <h2 className="text-lg font-semibold text-slate-900 dark:text-white flex items-center gap-2">
                  <Table2 className="w-5 h-5 text-slate-500 dark:text-slate-400" />
                  Tables ({schema.tables.length})
                </h2>
              </div>

              <div className="divide-y divide-slate-100 dark:divide-slate-700/50">
                {schema.tables.map((table) => (
                  <div key={table.id} className="px-6 py-5">

                    {/* Table name + description */}
                    <div className="flex items-start justify-between gap-4 mb-3">
                      <div className="flex-1 min-w-0">
                        <h3 className="text-base font-semibold text-slate-900 dark:text-white flex items-center gap-2 mb-1.5">
                          <Table2 className="w-4.5 h-4.5 text-blue-600 dark:text-blue-400 flex-shrink-0" />
                          {table.name}
                        </h3>
                        <div className="ml-6">
                          <EditableDescription
                            description={table.enriched_description}
                            source={table.description_source}
                            onSave={handleSaveTableDescription(table.id)}
                            placeholder="No table description — click to add one"
                          />
                        </div>
                      </div>
                      <span className="text-sm text-slate-400 dark:text-slate-500 flex-shrink-0 mt-0.5">
                        {table.columns.length} columns
                      </span>
                    </div>

                    {/* Columns table */}
                    <div className="mt-3 rounded-xl overflow-hidden border border-slate-100 dark:border-slate-700/50 ml-6">
                      <table className="min-w-full divide-y divide-slate-100 dark:divide-slate-700/50">
                        <thead className="bg-slate-50 dark:bg-slate-700/40">
                          <tr>
                            <th className="px-3 py-2.5 text-left text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide w-40">
                              Column
                            </th>
                            <th className="px-3 py-2.5 text-left text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide w-36">
                              Type
                            </th>
                            <th className="px-3 py-2.5 text-left text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide">
                              Description
                              <span className="ml-2 normal-case font-normal text-slate-400 dark:text-slate-500">
                                (click to edit)
                              </span>
                            </th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100 dark:divide-slate-700/50 bg-white dark:bg-transparent">
                          {table.columns.map((column) => (
                            <tr key={column.id} className="hover:bg-slate-50 dark:hover:bg-slate-700/20 transition-colors">
                              <td className="px-3 py-2.5 text-sm font-medium text-slate-900 dark:text-slate-100 align-top">
                                <div className="flex flex-wrap gap-1 items-center">
                                  {column.name}
                                  {column.is_primary_key && (
                                    <span className="text-xs bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 px-1.5 py-0.5 rounded-md">
                                      PK
                                    </span>
                                  )}
                                  {column.is_foreign_key && (
                                    <span className="text-xs bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 px-1.5 py-0.5 rounded-md">
                                      FK
                                    </span>
                                  )}
                                </div>
                              </td>
                              <td className="px-3 py-2.5 text-sm text-slate-500 dark:text-slate-400 align-top font-mono">
                                {column.data_type}
                                {!column.is_nullable && (
                                  <span className="block text-xs text-slate-400 dark:text-slate-500">NOT NULL</span>
                                )}
                              </td>
                              <td className="px-3 py-2.5 align-top">
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

                    {/* Foreign key relationships */}
                    {table.columns.some(c => c.is_foreign_key) && (
                      <div className="mt-3 ml-6">
                        <h4 className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide mb-2">
                          Foreign Keys
                        </h4>
                        <div className="space-y-1">
                          {table.columns.filter(c => c.is_foreign_key).map((column) => (
                            <div key={column.id} className="text-sm text-slate-600 dark:text-slate-400 flex items-center gap-2 flex-wrap">
                              <span className="text-blue-500 dark:text-blue-400">→</span>
                              <code className="bg-slate-100 dark:bg-slate-700 px-2 py-0.5 rounded-md text-xs text-slate-700 dark:text-slate-300">
                                {column.name}
                              </code>
                              <span className="text-slate-400 dark:text-slate-500">→</span>
                              <code className="bg-slate-100 dark:bg-slate-700 px-2 py-0.5 rounded-md text-xs text-slate-700 dark:text-slate-300">
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
          <div className="text-center py-14">
            <Database className="w-14 h-14 text-slate-300 dark:text-slate-600 mx-auto mb-4" />
            <div className="text-slate-500 dark:text-slate-400">Schema not found</div>
          </div>
        )}
      </div>
    </DashboardLayout>
  )
}

function LoadingSkeleton() {
  return (
    <div className="space-y-5 animate-pulse">
      <div className="bg-white dark:bg-slate-800/70 rounded-2xl border border-slate-100 dark:border-slate-700/50 p-6">
        <div className="flex items-start justify-between gap-4 mb-4">
          <div className="flex-1">
            <div className="h-8 bg-slate-200 dark:bg-slate-700 rounded-xl w-1/3 mb-3" />
            <div className="flex gap-2">
              <div className="h-6 bg-slate-200 dark:bg-slate-700 rounded-full w-20" />
              <div className="h-6 bg-slate-200 dark:bg-slate-700 rounded-full w-20" />
              <div className="h-6 bg-slate-200 dark:bg-slate-700 rounded-full w-28" />
            </div>
          </div>
          <div className="flex gap-2.5">
            <div className="h-9 bg-slate-200 dark:bg-slate-700 rounded-xl w-36" />
            <div className="h-9 bg-slate-200 dark:bg-slate-700 rounded-xl w-24" />
          </div>
        </div>
        <div className="h-16 bg-slate-100 dark:bg-slate-700/40 rounded-xl mt-4" />
      </div>
      <div className="bg-white dark:bg-slate-800/70 rounded-2xl border border-slate-100 dark:border-slate-700/50">
        <div className="px-6 py-4 border-b border-slate-100 dark:border-slate-700/50">
          <div className="h-6 bg-slate-200 dark:bg-slate-700 rounded-xl w-32" />
        </div>
        <div className="px-6 py-5 space-y-6">
          {[1, 2, 3].map(i => (
            <div key={i}>
              <div className="h-5 bg-slate-200 dark:bg-slate-700 rounded-xl w-48 mb-3" />
              <div className="h-40 bg-slate-100 dark:bg-slate-700/40 rounded-xl" />
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
