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

  // SWR data fetching with auto-revalidation
  const { data, error, isLoading, mutate } = useSWR(
    isAuthenticated ? ['schemas', activeOnly] : null,
    () => apiClient.listSchemas(activeOnly),
    {
      refreshInterval: 30000, // Refresh every 30 seconds
      revalidateOnFocus: true,
      onError: (err) => {
        toast.error(err instanceof Error ? err.message : 'Failed to load schemas')
      }
    }
  )

  const handleUploadSuccess = () => {
    mutate() // Revalidate data after upload
    toast.success('Schema uploaded successfully!')
  }

  if (!isAuthenticated) {
    return <ApiKeyInput />
  }

  const schemas = data?.schemas || []

  // Filter schemas based on search query
  const filteredSchemas = schemas.filter(schema =>
    schema.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    schema.db_type.toLowerCase().includes(searchQuery.toLowerCase())
  )

  // Pagination
  const totalPages = Math.ceil(filteredSchemas.length / ITEMS_PER_PAGE)
  const startIndex = (currentPage - 1) * ITEMS_PER_PAGE
  const endIndex = startIndex + ITEMS_PER_PAGE
  const paginatedSchemas = filteredSchemas.slice(startIndex, endIndex)

  // Reset to page 1 when search changes
  const handleSearch = (query: string) => {
    setSearchQuery(query)
    setCurrentPage(1)
  }

  return (
    <DashboardLayout>
      <div className="px-4 py-8">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 flex items-center">
              <Database className="w-8 h-8 mr-3 text-blue-600" />
              Database Schemas
            </h1>
            <p className="text-gray-600 mt-2">
              Manage your database schemas and AI enrichment
            </p>
          </div>
          <div className="text-sm text-gray-500">
            {schemas.length} {schemas.length === 1 ? 'schema' : 'schemas'}
          </div>
        </div>

        {/* Upload Section */}
        <div className="mb-8">
          <SchemaUpload onUploadSuccess={handleUploadSuccess} />
        </div>

        {/* Search and Filters */}
        <div className="mb-6 flex items-center space-x-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search schemas by name or database type..."
              value={searchQuery}
              onChange={(e) => handleSearch(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          <label className="flex items-center space-x-2 text-sm text-gray-700 cursor-pointer">
            <input
              type="checkbox"
              checked={activeOnly}
              onChange={(e) => {
                setActiveOnly(e.target.checked)
                setCurrentPage(1)
              }}
              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <span>Active only</span>
          </label>
        </div>

        {/* Schemas List */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
            <h2 className="text-xl font-semibold text-gray-900">Your Schemas</h2>
            {searchQuery && (
              <span className="text-sm text-gray-500">
                {filteredSchemas.length} {filteredSchemas.length === 1 ? 'result' : 'results'}
              </span>
            )}
          </div>

          {isLoading ? (
            <LoadingSkeleton />
          ) : error ? (
            <div className="px-6 py-8 text-center">
              <AlertCircle className="w-12 h-12 text-red-400 mx-auto mb-3" />
              <p className="text-red-600">Failed to load schemas</p>
            </div>
          ) : filteredSchemas.length === 0 ? (
            <div className="px-6 py-12 text-center">
              <Database className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-500 mb-2">
                {searchQuery ? 'No schemas match your search' : 'No schemas uploaded yet'}
              </p>
              {!searchQuery && (
                <p className="text-sm text-gray-400">Upload your first schema above to get started!</p>
              )}
            </div>
          ) : (
            <>
              <div className="divide-y divide-gray-200">
                {paginatedSchemas.map((schema) => (
                  <Link
                    key={schema.id}
                    href={`/dashboard/schemas/${schema.id}`}
                    className="block px-6 py-4 hover:bg-gray-50 transition-colors group"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-start space-x-4">
                        <div className="mt-1">
                          <Database className="w-6 h-6 text-blue-600 group-hover:text-blue-700" />
                        </div>
                        <div>
                          <h3 className="text-lg font-medium text-gray-900 group-hover:text-blue-600">
                            {schema.name}
                          </h3>
                          <div className="flex items-center space-x-3 mt-1">
                            <span className="text-sm text-gray-500">
                              <span className="font-medium">{schema.db_type.toUpperCase()}</span>
                            </span>
                            <span className="text-gray-300">•</span>
                            <span className="text-sm text-gray-500">
                              {schema.table_count} {schema.table_count === 1 ? 'table' : 'tables'}
                            </span>
                            <span className="text-gray-300">•</span>
                            <span className="text-sm text-gray-400">
                              {new Date(schema.created_at).toLocaleDateString()}
                            </span>
                          </div>
                          <div className="flex items-center gap-1.5 mt-2">
                            <code className="font-mono text-xs text-gray-400 select-all">
                              {schema.id}
                            </code>
                            <button
                              onClick={(e) => handleCopyId(e, schema.id)}
                              className="text-gray-400 hover:text-gray-600 transition-colors shrink-0"
                              title="Copy schema ID"
                            >
                              {copiedId === schema.id
                                ? <Check className="w-3 h-3 text-green-500" />
                                : <Copy className="w-3 h-3" />}
                            </button>
                          </div>
                          {schema.enriched_description && (
                            <p className="text-sm text-gray-600 mt-2 line-clamp-2">
                              {schema.enriched_description}
                            </p>
                          )}
                        </div>
                      </div>
                      <div className="text-right">
                        {schema.enrichment_status === 'failed' ? (
                          <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-red-100 text-red-800">
                            <AlertCircle className="w-3 h-3 mr-1" />
                            Enrichment Failed
                          </span>
                        ) : schema.enriched_description ? (
                          <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-800">
                            <Sparkles className="w-3 h-3 mr-1" />
                            Enriched
                          </span>
                        ) : (schema.enrichment_status === 'pending' || schema.enrichment_status === 'running') ? (
                          <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-amber-100 text-amber-800">
                            <svg className="animate-spin w-3 h-3 mr-1.5" viewBox="0 0 24 24" fill="none">
                              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
                            </svg>
                            Enriching…
                          </span>
                        ) : (
                          <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-yellow-100 text-yellow-800">
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
                <div className="px-6 py-4 border-t border-gray-200 flex items-center justify-between">
                  <div className="text-sm text-gray-500">
                    Showing {startIndex + 1}-{Math.min(endIndex, filteredSchemas.length)} of {filteredSchemas.length}
                  </div>
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                      disabled={currentPage === 1}
                      className="inline-flex items-center px-3 py-1 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <ChevronLeft className="w-4 h-4 mr-1" />
                      Previous
                    </button>
                    <div className="flex items-center space-x-1">
                      {Array.from({ length: totalPages }, (_, i) => i + 1).map(page => (
                        <button
                          key={page}
                          onClick={() => setCurrentPage(page)}
                          className={`px-3 py-1 rounded-md text-sm font-medium ${
                            currentPage === page
                              ? 'bg-blue-600 text-white'
                              : 'text-gray-700 hover:bg-gray-100'
                          }`}
                        >
                          {page}
                        </button>
                      ))}
                    </div>
                    <button
                      onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                      disabled={currentPage === totalPages}
                      className="inline-flex items-center px-3 py-1 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
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

// Loading skeleton
function LoadingSkeleton() {
  return (
    <div className="divide-y divide-gray-200">
      {[1, 2, 3].map((i) => (
        <div key={i} className="px-6 py-4 animate-pulse">
          <div className="flex items-center justify-between">
            <div className="flex items-start space-x-4 flex-1">
              <div className="w-6 h-6 bg-gray-200 rounded"></div>
              <div className="flex-1">
                <div className="h-5 bg-gray-200 rounded w-1/3 mb-2"></div>
                <div className="h-4 bg-gray-200 rounded w-1/2"></div>
              </div>
            </div>
            <div className="h-6 bg-gray-200 rounded w-24"></div>
          </div>
        </div>
      ))}
    </div>
  )
}
