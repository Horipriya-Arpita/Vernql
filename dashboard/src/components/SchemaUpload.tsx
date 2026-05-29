'use client'

import { useState } from 'react'
import { apiClient } from '@/lib/api-client'
import { Upload, FileText, Terminal, AlertCircle } from 'lucide-react'
import toast from 'react-hot-toast'

interface SchemaUploadProps {
  onUploadSuccess: () => void
}

type UploadMethod = 'file' | 'text'
type SchemaFormat = 'sql_ddl' | 'prisma'

const FORMAT_LABELS: Record<SchemaFormat, string> = {
  sql_ddl: 'SQL DDL',
  prisma:  'Prisma ORM',
}

const ACCEPTED_EXTENSIONS: Record<SchemaFormat, string[]> = {
  sql_ddl: ['.sql', '.ddl'],
  prisma:  ['.prisma'],
}

const inputClass =
  'w-full px-4 py-2.5 border border-slate-200 dark:border-slate-600 rounded-xl bg-white dark:bg-slate-700/50 text-slate-900 dark:text-white placeholder:text-slate-400 dark:placeholder:text-slate-500 focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition text-[0.9375rem]'

export default function SchemaUpload({ onUploadSuccess }: SchemaUploadProps) {
  const [activeTab, setActiveTab]       = useState<UploadMethod>('file')
  const [schemaFormat, setSchemaFormat] = useState<SchemaFormat>('sql_ddl')
  const [name, setName]                 = useState('')
  const [dbType, setDbType]             = useState<'postgresql' | 'mysql'>('postgresql')
  const [schemaFile, setSchemaFile]     = useState<File | null>(null)
  const [schemaText, setSchemaText]     = useState('')
  const [loading, setLoading]           = useState(false)
  const [error, setError]               = useState('')
  const [dragActive, setDragActive]     = useState(false)

  const acceptedExtensions = ACCEPTED_EXTENSIONS[schemaFormat]
  const isFileAccepted = (file: File) => acceptedExtensions.some(ext => file.name.endsWith(ext))

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault(); e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') setDragActive(true)
    else if (e.type === 'dragleave') setDragActive(false)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault(); e.stopPropagation()
    setDragActive(false)
    if (e.dataTransfer.files?.[0]) {
      const file = e.dataTransfer.files[0]
      if (isFileAccepted(file)) { setSchemaFile(file); setError('') }
      else setError(`Please upload a ${acceptedExtensions.join(' or ')} file`)
    }
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.[0]) {
      const file = e.target.files[0]
      if (isFileAccepted(file)) { setSchemaFile(file); setError('') }
      else setError(`Please upload a ${acceptedExtensions.join(' or ')} file`)
    }
  }

  const handleFormatChange = (fmt: SchemaFormat) => {
    setSchemaFormat(fmt); setSchemaFile(null); setSchemaText(''); setError('')
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault(); setError('')
    if (!name.trim()) { setError('Please provide a name for this schema'); return }

    let content = ''
    if (activeTab === 'file') {
      if (!schemaFile) { setError(`Please select a ${acceptedExtensions.join(' or ')} file`); return }
      try { content = await schemaFile.text() } catch { setError('Failed to read file'); return }
    } else {
      if (!schemaText.trim()) { setError(`Please paste your ${FORMAT_LABELS[schemaFormat]} schema`); return }
      content = schemaText.trim()
    }

    try {
      setLoading(true)
      await apiClient.uploadSchema({
        name: name.trim(),
        schema_format: schemaFormat,
        db_type: dbType,
        sql_ddl: content,
      })
      toast.success('Schema uploaded and parsed successfully!')
      setName(''); setSchemaFile(null); setSchemaText('')
      onUploadSuccess()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to upload schema')
    } finally {
      setLoading(false)
    }
  }

  const getExportCommand = () => {
    if (schemaFormat === 'prisma') return null
    return dbType === 'postgresql'
      ? 'pg_dump --schema-only your_database > schema.sql'
      : 'mysqldump --no-data your_database > schema.sql'
  }

  const getPlaceholder = () => schemaFormat === 'prisma'
    ? `Paste your Prisma schema here...\n\nExample:\ngenerator client {\n  provider = "prisma-client-js"\n}\n\ndatasource db {\n  provider = "postgresql"\n}\n\nmodel User {\n  id        String   @id @default(cuid())\n  email     String   @unique\n  name      String\n  createdAt DateTime @default(now())\n\n  posts Post[]\n}`
    : `Paste your SQL DDL statements here...\n\nExample:\nCREATE TABLE users (\n  id SERIAL PRIMARY KEY,\n  email VARCHAR(255) NOT NULL,\n  created_at TIMESTAMP DEFAULT NOW()\n);\n\nCREATE TABLE orders (\n  id SERIAL PRIMARY KEY,\n  user_id INTEGER REFERENCES users(id),\n  total DECIMAL(10,2)\n);`

  const exportCommand = getExportCommand()

  // Shared radio label style
  const radioLabel = 'flex items-center gap-2 cursor-pointer text-sm text-slate-700 dark:text-slate-300'

  return (
    <div className="bg-white dark:bg-slate-800/70 rounded-2xl border border-slate-100 dark:border-slate-700/50 p-6">

      {/* ── Header ── */}
      <div className="mb-5">
        <h2 className="text-lg font-semibold text-slate-900 dark:text-white">Upload Database Schema</h2>
        <p className="text-sm text-slate-500 dark:text-slate-400 mt-0.5">
          Upload your schema structure only — we never access your database
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-5">

        {/* ── Schema Format ── */}
        <div>
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
            Schema Format
          </label>
          <div className="flex gap-5">
            {(Object.keys(FORMAT_LABELS) as SchemaFormat[]).map(fmt => (
              <label key={fmt} className={radioLabel}>
                <input
                  type="radio" name="schemaFormat" value={fmt}
                  checked={schemaFormat === fmt}
                  onChange={() => handleFormatChange(fmt)}
                  className="accent-blue-600"
                />
                {FORMAT_LABELS[fmt]}
              </label>
            ))}
          </div>
          {schemaFormat === 'prisma' && (
            <p className="mt-2 text-xs text-blue-700 dark:text-blue-300 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800/40 rounded-lg px-3 py-2">
              Prisma schemas are supported directly — paste your{' '}
              <code className="bg-blue-100 dark:bg-blue-800/40 px-1 rounded">.prisma</code> file as-is.
              The database type is detected automatically from the{' '}
              <code className="bg-blue-100 dark:bg-blue-800/40 px-1 rounded">datasource</code> block.
            </p>
          )}
        </div>

        {/* ── Schema Name ── */}
        <div>
          <label htmlFor="schema-name" className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">
            Schema Name
          </label>
          <input
            type="text" id="schema-name" value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g., Production Database, E-commerce DB"
            className={inputClass}
          />
        </div>

        {/* ── Database Type ── */}
        <div>
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
            Database Type
            {schemaFormat === 'prisma' && (
              <span className="ml-2 text-xs text-slate-400 dark:text-slate-500 font-normal">
                (fallback — auto-detected from datasource block)
              </span>
            )}
          </label>
          <div className="flex gap-5">
            {(['postgresql', 'mysql'] as const).map(db => (
              <label key={db} className={radioLabel}>
                <input
                  type="radio" name="dbType" value={db}
                  checked={dbType === db}
                  onChange={() => setDbType(db)}
                  className="accent-blue-600"
                />
                {db === 'postgresql' ? 'PostgreSQL' : 'MySQL'}
              </label>
            ))}
          </div>
        </div>

        {/* ── Upload Method Tabs ── */}
        <div>
          <div className="border-b border-slate-200 dark:border-slate-700">
            <nav className="flex gap-6">
              {([['file', Upload, 'Upload File'], ['text', FileText, 'Paste Schema']] as const).map(([tab, Icon, label]) => (
                <button
                  key={tab} type="button" onClick={() => setActiveTab(tab)}
                  className={`flex items-center gap-1.5 py-2.5 border-b-2 text-sm font-medium transition-colors ${
                    activeTab === tab
                      ? 'border-blue-600 text-blue-600 dark:text-blue-400 dark:border-blue-400'
                      : 'border-transparent text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-300 hover:border-slate-300 dark:hover:border-slate-600'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  {label}
                </button>
              ))}
            </nav>
          </div>

          <div className="mt-4">

            {/* File Upload Tab */}
            {activeTab === 'file' && (
              <div className="space-y-4">
                {/* Drop zone */}
                <div
                  onDragEnter={handleDrag} onDragLeave={handleDrag}
                  onDragOver={handleDrag} onDrop={handleDrop}
                  className={`border-2 border-dashed rounded-xl p-8 text-center transition-colors ${
                    dragActive
                      ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/15'
                      : 'border-slate-300 dark:border-slate-600 hover:border-slate-400 dark:hover:border-slate-500 hover:bg-slate-50 dark:hover:bg-slate-700/20'
                  }`}
                >
                  <input
                    key={schemaFormat} type="file" id="file-upload"
                    accept={acceptedExtensions.join(',')}
                    onChange={handleFileChange} className="hidden"
                  />
                  <label htmlFor="file-upload" className="cursor-pointer">
                    <Upload className="w-12 h-12 mx-auto text-slate-400 dark:text-slate-500 mb-3" />
                    {schemaFile ? (
                      <div>
                        <p className="text-sm font-medium text-slate-900 dark:text-white">{schemaFile.name}</p>
                        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                          {(schemaFile.size / 1024).toFixed(2)} KB
                        </p>
                      </div>
                    ) : (
                      <div>
                        <p className="text-sm font-medium text-slate-900 dark:text-slate-200">
                          Drop your {acceptedExtensions.join(' / ')} file here, or click to browse
                        </p>
                        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                          {acceptedExtensions.join(' or ')} files only
                        </p>
                      </div>
                    )}
                  </label>
                </div>

                {/* Export command — SQL DDL only */}
                {exportCommand && (
                  <div className="bg-blue-50 dark:bg-blue-900/15 border border-blue-200 dark:border-blue-800/40 rounded-xl p-4">
                    <div className="flex items-start gap-3">
                      <Terminal className="w-5 h-5 text-blue-600 dark:text-blue-400 mt-0.5 flex-shrink-0" />
                      <div>
                        <h4 className="text-sm font-semibold text-blue-900 dark:text-blue-200 mb-1.5">
                          How to export your schema
                        </h4>
                        <p className="text-xs text-blue-800 dark:text-blue-300 mb-2">
                          Run this command in your terminal:
                        </p>
                        <code className="block bg-white dark:bg-slate-800 text-xs p-2.5 rounded-lg border border-blue-200 dark:border-blue-800/40 font-mono text-blue-900 dark:text-blue-200">
                          {exportCommand}
                        </code>
                        <ul className="text-xs text-blue-700 dark:text-blue-300 mt-2.5 space-y-0.5">
                          <li>✅ Exports only your schema structure (tables, columns)</li>
                          <li>✅ No actual data is included</li>
                          <li>✅ We never access your database directly</li>
                        </ul>
                      </div>
                    </div>
                  </div>
                )}

                {/* Prisma instructions */}
                {schemaFormat === 'prisma' && (
                  <div className="bg-violet-50 dark:bg-violet-900/15 border border-violet-200 dark:border-violet-800/40 rounded-xl p-4">
                    <div className="flex items-start gap-3">
                      <FileText className="w-5 h-5 text-violet-600 dark:text-violet-400 mt-0.5 flex-shrink-0" />
                      <div>
                        <h4 className="text-sm font-semibold text-violet-900 dark:text-violet-200 mb-1">
                          Upload your Prisma schema file
                        </h4>
                        <p className="text-xs text-violet-800 dark:text-violet-300">
                          Find your{' '}
                          <code className="bg-white dark:bg-slate-800 px-1 rounded">schema.prisma</code>
                          {' '}file (usually at{' '}
                          <code className="bg-white dark:bg-slate-800 px-1 rounded">prisma/schema.prisma</code>)
                          and upload it directly — no conversion needed.
                        </p>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Paste Schema Tab */}
            {activeTab === 'text' && (
              <div className="space-y-3">
                <textarea
                  value={schemaText}
                  onChange={(e) => setSchemaText(e.target.value)}
                  placeholder={getPlaceholder()}
                  rows={14}
                  className="w-full px-4 py-3 border border-slate-200 dark:border-slate-600 rounded-xl bg-white dark:bg-slate-700/50 text-slate-900 dark:text-slate-100 placeholder:text-slate-400 dark:placeholder:text-slate-500 focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition font-mono text-sm resize-none"
                />
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  {schemaFormat === 'prisma'
                    ? 'Paste the full content of your .prisma file including generator, datasource, model, and enum blocks.'
                    : 'Paste CREATE TABLE statements and other DDL from your database schema. Only structure is needed — no INSERT statements or data.'}
                </p>
              </div>
            )}
          </div>
        </div>

        {/* ── Error ── */}
        {error && (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800/40 text-red-700 dark:text-red-400 px-4 py-3 rounded-xl flex items-start gap-3">
            <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
            <span className="text-sm">{error}</span>
          </div>
        )}

        {/* ── Submit ── */}
        <button
          type="submit" disabled={loading}
          className="w-full bg-blue-600 hover:bg-blue-700 text-white py-2.5 px-4 rounded-xl font-semibold text-sm shadow-blue-sm disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
        >
          {loading ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-2 border-white/30 border-t-white" />
              Parsing Schema…
            </>
          ) : (
            <>
              <Upload className="w-4 h-4" />
              Parse and Upload Schema
            </>
          )}
        </button>
      </form>

      {/* ── Privacy notice ── */}
      <div className="mt-5 p-4 bg-green-50 dark:bg-green-900/15 border border-green-200 dark:border-green-800/40 rounded-xl">
        <h4 className="text-sm font-semibold text-green-900 dark:text-green-300 mb-2">Privacy-First Design</h4>
        <ul className="text-xs text-green-800 dark:text-green-400 space-y-1">
          <li>✅ We NEVER access your database directly</li>
          <li>✅ We NEVER store your actual data</li>
          <li>✅ We ONLY parse your schema structure (table/column names)</li>
          <li>✅ You run all SQL queries on your own infrastructure</li>
        </ul>
      </div>

    </div>
  )
}
