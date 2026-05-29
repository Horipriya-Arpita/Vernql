'use client'

import { useAuth } from '@/contexts/AuthContext'
import ApiKeyInput from '@/components/ApiKeyInput'
import DashboardLayout from '@/components/DashboardLayout'
import SchemaUpload from '@/components/SchemaUpload'
import { useState } from 'react'
import { apiClient } from '@/lib/api-client'
import Link from 'next/link'
import useSWR from 'swr'
import toast from 'react-hot-toast'
import { Database, Search, Sparkles, AlertCircle, ChevronLeft, ChevronRight, Copy, Check } from 'lucide-react'

const ITEMS_PER_PAGE = 10

export default function SchemasPage() {
  const { isAuthenticated } = useAuth()
  const [searchQuery, setSearchQuery] = useState('')
  const [currentPage, setCurrentPage] = useState(1)
  const [activeOnly, setActiveOnly] = useState(true)
  const [copiedId, setCopiedId] = useState<string | null>(null)

  const handleCopyId = (e: React.MouseEvent, id: string) => {
    e.preventDefault()
    e.stopPropagation()
    navigator.clipboard.writeText(id)
    setCopiedId(id)
    setTimeout(() => setCopiedId(null), 2000)
  }

  const { data, error, isLoading, mutate } = useSWR(
    isAuthenticated ? ['schemas', activeOnly] : null,
    () => apiClient.listSchemas(activeOnly),
    {
      refreshInterval: 30000,
      revalidateOnFocus: true,
      onError: (err) => {
        toast.error(err instanceof Error ? err.message : 'Failed to load schemas')
      }
    }
  )

  const handleUploadSuccess = () => {
    mutate()
    toast.success('Schema uploaded successfully!')
  }

  if (!isAuthenticated) {
    return <ApiKeyInput />
  }

  const schemas = data?.schemas || []

  const filteredSchemas = schemas.filter(schema =>
    schema.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    schema.db_type.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const totalPages = Math.ceil(filteredSchemas.length / ITEMS_PER_PAGE)
  const startIndex = (currentPage - 1) * ITEMS_PER_PAGE
  const endIndex = startIndex + ITEMS_PER_PAGE
  const paginatedSchemas = filteredSchemas.slice(startIndex, endIndex)

  const handleSearch = (query: string) => {
    setSearchQuery(query)
    setCurrentPage(1)
  }

  return (
    <DashboardLayout>
      <div>
        {/* ── Header ── */}
        <div className="flex justify-between items-start mb-8">
          <div>
            <h1 className="text-4xl font-bold text-slate-900 dark:text-white tracking-tight flex items-center gap-3 mb-1.5">
              <Database className="w-9 h-9 text-blue-600 dark:text-blue-400" />
              Database Schemas
            </h1>
            <p className="text-slate-500 dark:text-slate-400 text-lg">
              Manage your database schemas and AI enrichment
            </p>
          </div>
          <div className="text-sm text-slate-500 dark:text-slate-400 pt-2">
            {schemas.length} {schemas.length === 1 ? 'schema' : 'schemas'}
          </div>
        </div>

        {/* ── Upload ── */}
        <div className="mb-8">
          <SchemaUpload onUploadSuccess={handleUploadSuccess} />
        </div>

        {/* ── Search & Filters ── */}
        <div className="mb-5 flex items-center gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400 pointer-events-none" />
            <input
              type="text"
              placeholder="Search schemas by name or database type…"
              value={searchQuery}
              onChange={(e) => handleSearch(e.target.value)}
              className="w-full pl-10 pr-4 py-2.5 border border-slate-200 dark:border-slate-600 rounded-xl bg-white dark:bg-slate-800 text-slate-900 dark:text-white placeholder:text-slate-400 dark:placeholder:text-slate-500 focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition text-[0.9375rem]"
            />
          </div>
          <label className="flex items-center gap-2 text-sm text-slate-700 dark:text-slate-300 cursor-pointer whitespace-nowrap">
            <input
              type="checkbox"
              checked={activeOnly}
              onChange={(e) => { setActiveOnly(e.target.checked); setCurrentPage(1) }}
              className="rounded border-slate-300 dark:border-slate-600 text-blue-600 focus:ring-blue-500"
            />
            Active only
          </label>
        </div>

        {/* ── Schema List ── */}
        <div className="bg-white dark:bg-slate-800/70 rounded-2xl border border-slate-100 dark:border-slate-700/50">
          <div className="px-6 py-4 border-b border-slate-100 dark:border-slate-700/50 flex items-center justify-between">
            <h2 className="text-lg font-semibold text-slate-900 dark:text-white">Your Schemas</h2>
            {searchQuery && (
              <span className="text-sm text-slate-500 dark:text-slate-400">
                {filteredSchemas.length} {filteredSchemas.length === 1 ? 'result' : 'results'}
              </span>
            )}
          </div>

          {isLoading ? (
            <LoadingSkeleton />
          ) : error ? (
            <div className="px-6 py-10 text-center">
              <AlertCircle className="w-12 h-12 text-red-400 mx-auto mb-3" />
              <p className="text-red-600 dark:text-red-400">Failed to load schemas</p>
            </div>
          ) : filteredSchemas.length === 0 ? (
            <div className="px-6 py-14 text-center">
              <Database className="w-14 h-14 text-slate-300 dark:text-slate-600 mx-auto mb-4" />
              <p className="text-slate-500 dark:text-slate-400 mb-1.5">
                {searchQuery ? 'No schemas match your search' : 'No schemas uploaded yet'}
              </p>
              {!searchQuery && (
                <p className="text-sm text-slate-400 dark:text-slate-500">
                  Upload your first schema above to get started!
                </p>
              )}
            </div>
          ) : (
            <>
              <div className="divide-y divide-slate-100 dark:divide-slate-700/50">
                {paginatedSchemas.map((schema) => (
                  <Link
                    key={schema.id}
                    href={`/dashboard/schemas/${schema.id}`}
                    className="block px-6 py-4 hover:bg-slate-50 dark:hover:bg-slate-700/30 transition-colors group"
                  >
                    <div className="flex items-center justify-between gap-4">
                      <div className="flex items-start gap-4 min-w-0">
                        <div className="mt-1 flex-shrink-0">
                          <Database className="w-5 h-5 text-blue-600 dark:text-blue-400 group-hover:text-blue-700 dark:group-hover:text-blue-300 transition-colors" />
                        </div>
                        <div className="min-w-0">
                          <h3 className="text-base font-medium text-slate-900 dark:text-white group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors truncate">
                            {schema.name}
                          </h3>
                          <div className="flex items-center gap-2.5 mt-1 flex-wrap">
                            <span className="text-sm font-medium text-slate-600 dark:text-slate-400">
                              {schema.db_type.toUpperCase()}
                            </span>
                            <span className="text-slate-300 dark:text-slate-600">•</span>
                            <span className="text-sm text-slate-500 dark:text-slate-400">
                              {schema.table_count} {schema.table_count === 1 ? 'table' : 'tables'}
                            </span>
                            <span className="text-slate-300 dark:text-slate-600">•</span>
                            <span className="text-sm text-slate-400 dark:text-slate-500">
                              {new Date(schema.created_at).toLocaleDateString()}
                            </span>
                          </div>
                          <div className="flex items-center gap-1.5 mt-1.5">
                            <code className="font-mono text-xs text-slate-400 dark:text-slate-500 select-all">
                              {schema.id}
                            </code>
                            <button
                              onClick={(e) => handleCopyId(e, schema.id)}
                              className="text-slate-400 dark:text-slate-500 hover:text-slate-600 dark:hover:text-slate-300 transition-colors flex-shrink-0"
                              title="Copy schema ID"
                            >
                              {copiedId === schema.id
                                ? <Check className="w-3 h-3 text-green-500" />
                                : <Copy className="w-3 h-3" />}
                            </button>
                          </div>
                          {schema.enriched_description && (
                            <p className="text-sm text-slate-600 dark:text-slate-400 mt-1.5 line-clamp-2">
                              {schema.enriched_description}
                            </p>
                          )}
                        </div>
                      </div>

                      <div className="text-right flex-shrink-0">
                        {schema.enrichment_status === 'failed' ? (
                          <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400">
                            <AlertCircle className="w-3 h-3 mr-1" />
                            Failed
                          </span>
                        ) : schema.enriched_description ? (
                          <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400">
                            <Sparkles className="w-3 h-3 mr-1" />
                            Enriched
                          </span>
                        ) : (schema.enrichment_status === 'pending' || schema.enrichment_status === 'running') ? (
                          <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400">
                            <svg className="animate-spin w-3 h-3 mr-1.5" viewBox="0 0 24 24" fill="none">
                              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
                            </svg>
                            Enriching…
                          </span>
                        ) : (
                          <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-400">
                            <AlertCircle className="w-3 h-3 mr-1" />
                            Not Enriched
                          </span>
                        )}
                      </div>
                    </div>
                  </Link>
                ))}
              </div>

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="px-6 py-4 border-t border-slate-100 dark:border-slate-700/50 flex items-center justify-between">
                  <div className="text-sm text-slate-500 dark:text-slate-400">
                    Showing {startIndex + 1}–{Math.min(endIndex, filteredSchemas.length)} of {filteredSchemas.length}
                  </div>
                  <div className="flex items-center gap-1.5">
                    <button
                      onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                      disabled={currentPage === 1}
                      className="inline-flex items-center px-3 py-1.5 border border-slate-200 dark:border-slate-600 rounded-lg text-sm font-medium text-slate-700 dark:text-slate-300 bg-white dark:bg-slate-800 hover:bg-slate-50 dark:hover:bg-slate-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                    >
                      <ChevronLeft className="w-4 h-4 mr-1" />
                      Previous
                    </button>
                    <div className="flex items-center gap-1">
                      {Array.from({ length: totalPages }, (_, i) => i + 1).map(page => (
                        <button
                          key={page}
                          onClick={() => setCurrentPage(page)}
                          className={`w-8 h-8 rounded-lg text-sm font-medium transition-colors ${
                            currentPage === page
                              ? 'bg-blue-600 text-white shadow-sm'
                              : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700'
                          }`}
                        >
                          {page}
                        </button>
                      ))}
                    </div>
                    <button
                      onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                      disabled={currentPage === totalPages}
                      className="inline-flex items-center px-3 py-1.5 border border-slate-200 dark:border-slate-600 rounded-lg text-sm font-medium text-slate-700 dark:text-slate-300 bg-white dark:bg-slate-800 hover:bg-slate-50 dark:hover:bg-slate-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                    >
                      Next
                      <ChevronRight className="w-4 h-4 ml-1" />
                    </button>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </DashboardLayout>
  )
}

function LoadingSkeleton() {
  return (
    <div className="divide-y divide-slate-100 dark:divide-slate-700/50">
      {[1, 2, 3].map((i) => (
        <div key={i} className="px-6 py-4 animate-pulse">
          <div className="flex items-center justify-between">
            <div className="flex items-start gap-4 flex-1">
              <div className="w-5 h-5 bg-slate-200 dark:bg-slate-700 rounded mt-1"></div>
              <div className="flex-1">
                <div className="h-5 bg-slate-200 dark:bg-slate-700 rounded w-1/3 mb-2"></div>
                <div className="h-4 bg-slate-200 dark:bg-slate-700 rounded w-1/2"></div>
              </div>
            </div>
            <div className="h-6 bg-slate-200 dark:bg-slate-700 rounded w-20"></div>
          </div>
        </div>
      ))}
    </div>
  )
}
