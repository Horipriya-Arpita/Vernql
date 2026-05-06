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
  prisma: 'Prisma ORM',
}

const ACCEPTED_EXTENSIONS: Record<SchemaFormat, string[]> = {
  sql_ddl: ['.sql', '.ddl'],
  prisma: ['.prisma'],
}

export default function SchemaUpload({ onUploadSuccess }: SchemaUploadProps) {
  const [activeTab, setActiveTab] = useState<UploadMethod>('file')
  const [schemaFormat, setSchemaFormat] = useState<SchemaFormat>('sql_ddl')
  const [name, setName] = useState('')
  const [dbType, setDbType] = useState<'postgresql' | 'mysql'>('postgresql')
  const [schemaFile, setSchemaFile] = useState<File | null>(null)
  const [schemaText, setSchemaText] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [dragActive, setDragActive] = useState(false)

  const acceptedExtensions = ACCEPTED_EXTENSIONS[schemaFormat]

  const isFileAccepted = (file: File) =>
    acceptedExtensions.some((ext) => file.name.endsWith(ext))

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') setDragActive(true)
    else if (e.type === 'dragleave') setDragActive(false)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0]
      if (isFileAccepted(file)) {
        setSchemaFile(file)
        setError('')
      } else {
        setError(`Please upload a ${acceptedExtensions.join(' or ')} file`)
      }
    }
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0]
      if (isFileAccepted(file)) {
        setSchemaFile(file)
        setError('')
      } else {
        setError(`Please upload a ${acceptedExtensions.join(' or ')} file`)
      }
    }
  }

  const handleFormatChange = (fmt: SchemaFormat) => {
    setSchemaFormat(fmt)
    // Clear file selection when format changes — old file is the wrong type
    setSchemaFile(null)
    setSchemaText('')
    setError('')
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    if (!name.trim()) {
      setError('Please provide a name for this schema')
      return
    }

    let content = ''
    if (activeTab === 'file') {
      if (!schemaFile) {
        setError(`Please select a ${acceptedExtensions.join(' or ')} file`)
        return
      }
      try {
        content = await schemaFile.text()
      } catch {
        setError('Failed to read file')
        return
      }
    } else {
      if (!schemaText.trim()) {
        setError(`Please paste your ${FORMAT_LABELS[schemaFormat]} schema`)
        return
      }
      content = schemaText.trim()
    }

    try {
      setLoading(true)
      await apiClient.uploadSchema({
        name: name.trim(),
        schema_format: schemaFormat,
        // db_type is sent for sql_ddl; for prisma the backend reads it from
        // the datasource block so we pass the UI selection as a fallback only.
        db_type: dbType,
        sql_ddl: content,
      })

      toast.success('Schema uploaded and parsed successfully!')
      setName('')
      setSchemaFile(null)
      setSchemaText('')
      onUploadSuccess()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to upload schema')
    } finally {
      setLoading(false)
    }
  }

  // -----------------------------------------------------------------------
  // Instruction helpers
  // -----------------------------------------------------------------------

  const getExportCommand = () => {
    if (schemaFormat === 'prisma') return null
    return dbType === 'postgresql'
      ? 'pg_dump --schema-only your_database > schema.sql'
      : 'mysqldump --no-data your_database > schema.sql'
  }

  const getPlaceholder = () => {
    if (schemaFormat === 'prisma') {
      return `Paste your Prisma schema here...\n\nExample:\ngenerator client {\n  provider = "prisma-client-js"\n}\n\ndatasource db {\n  provider = "postgresql"\n}\n\nmodel User {\n  id        String   @id @default(cuid())\n  email     String   @unique\n  name      String\n  createdAt DateTime @default(now())\n\n  posts Post[]\n}\n\nmodel Post {\n  id       String @id @default(cuid())\n  title    String\n  authorId String\n  author   User   @relation(fields: [authorId], references: [id])\n}`
    }
    return `Paste your SQL DDL statements here...\n\nExample:\nCREATE TABLE users (\n  id SERIAL PRIMARY KEY,\n  email VARCHAR(255) NOT NULL,\n  created_at TIMESTAMP DEFAULT NOW()\n);\n\nCREATE TABLE orders (\n  id SERIAL PRIMARY KEY,\n  user_id INTEGER REFERENCES users(id),\n  total DECIMAL(10,2)\n);`
  }

  const exportCommand = getExportCommand()

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-xl font-semibold text-gray-900">Upload Database Schema</h2>
          <p className="text-sm text-gray-600 mt-1">
            Upload your schema structure only — we never access your database
          </p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">

        {/* Schema Format Selector */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Schema Format
          </label>
          <div className="flex gap-4">
            {(Object.keys(FORMAT_LABELS) as SchemaFormat[]).map((fmt) => (
              <label key={fmt} className="flex items-center cursor-pointer">
                <input
                  type="radio"
                  name="schemaFormat"
                  value={fmt}
                  checked={schemaFormat === fmt}
                  onChange={() => handleFormatChange(fmt)}
                  className="mr-2"
                />
                <span className="text-sm text-gray-700">{FORMAT_LABELS[fmt]}</span>
              </label>
            ))}
          </div>
          {schemaFormat === 'prisma' && (
            <p className="mt-2 text-xs text-blue-700 bg-blue-50 border border-blue-200 rounded px-3 py-2">
              Prisma schemas are supported directly — paste your <code>.prisma</code> file as-is.
              The database type is detected automatically from the <code>datasource</code> block.
            </p>
          )}
        </div>

        {/* Schema Name */}
        <div>
          <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-2">
            Schema Name
          </label>
          <input
            type="text"
            id="name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g., Production Database, E-commerce DB"
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>

        {/* Database Type — shown for sql_ddl; acts as fallback for prisma */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Database Type
            {schemaFormat === 'prisma' && (
              <span className="ml-2 text-xs text-gray-400 font-normal">
                (fallback — auto-detected from datasource block)
              </span>
            )}
          </label>
          <div className="flex gap-4">
            <label className="flex items-center cursor-pointer">
              <input
                type="radio"
                name="dbType"
                value="postgresql"
                checked={dbType === 'postgresql'}
                onChange={() => setDbType('postgresql')}
                className="mr-2"
              />
              <span className="text-sm text-gray-700">PostgreSQL</span>
            </label>
            <label className="flex items-center cursor-pointer">
              <input
                type="radio"
                name="dbType"
                value="mysql"
                checked={dbType === 'mysql'}
                onChange={() => setDbType('mysql')}
                className="mr-2"
              />
              <span className="text-sm text-gray-700">MySQL</span>
            </label>
          </div>
        </div>

        {/* Upload Method Tabs */}
        <div>
          <div className="border-b border-gray-200">
            <nav className="flex -mb-px space-x-8">
              <button
                type="button"
                onClick={() => setActiveTab('file')}
                className={`py-2 px-1 border-b-2 font-medium text-sm transition-colors ${
                  activeTab === 'file'
                    ? 'border-blue-600 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <Upload className="w-4 h-4 inline mr-2" />
                Upload File
              </button>
              <button
                type="button"
                onClick={() => setActiveTab('text')}
                className={`py-2 px-1 border-b-2 font-medium text-sm transition-colors ${
                  activeTab === 'text'
                    ? 'border-blue-600 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <FileText className="w-4 h-4 inline mr-2" />
                Paste Schema
              </button>
            </nav>
          </div>

          <div className="mt-4">
            {/* File Upload Tab */}
            {activeTab === 'file' && (
              <div className="space-y-4">
                <div
                  onDragEnter={handleDrag}
                  onDragLeave={handleDrag}
                  onDragOver={handleDrag}
                  onDrop={handleDrop}
                  className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
                    dragActive
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-300 hover:border-gray-400'
                  }`}
                >
                  <input
                    key={schemaFormat}
                    type="file"
                    id="file-upload"
                    accept={acceptedExtensions.join(',')}
                    onChange={handleFileChange}
                    className="hidden"
                  />
                  <label htmlFor="file-upload" className="cursor-pointer">
                    <Upload className="w-12 h-12 mx-auto text-gray-400 mb-3" />
                    {schemaFile ? (
                      <div>
                        <p className="text-sm font-medium text-gray-900">{schemaFile.name}</p>
                        <p className="text-xs text-gray-500 mt-1">
                          {(schemaFile.size / 1024).toFixed(2)} KB
                        </p>
                      </div>
                    ) : (
                      <div>
                        <p className="text-sm font-medium text-gray-900">
                          Drop your {acceptedExtensions.join(' / ')} file here, or click to browse
                        </p>
                        <p className="text-xs text-gray-500 mt-1">
                          {acceptedExtensions.join(' or ')} files only
                        </p>
                      </div>
                    )}
                  </label>
                </div>

                {/* Export instructions — SQL DDL only */}
                {exportCommand && (
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <div className="flex items-start">
                      <Terminal className="w-5 h-5 text-blue-600 mt-0.5 mr-3 flex-shrink-0" />
                      <div>
                        <h4 className="text-sm font-semibold text-blue-900 mb-2">
                          How to export your schema
                        </h4>
                        <p className="text-xs text-blue-800 mb-2">
                          Run this command in your terminal:
                        </p>
                        <code className="block bg-white text-xs p-2 rounded border border-blue-300 font-mono text-blue-900">
                          {exportCommand}
                        </code>
                        <p className="text-xs text-blue-700 mt-2">
                          ✅ This exports only your schema structure (tables, columns)
                          <br />
                          ✅ No actual data is included
                          <br />
                          ✅ We never access your database directly
                        </p>
                      </div>
                    </div>
                  </div>
                )}

                {/* Prisma instructions */}
                {schemaFormat === 'prisma' && (
                  <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                    <div className="flex items-start">
                      <FileText className="w-5 h-5 text-purple-600 mt-0.5 mr-3 flex-shrink-0" />
                      <div>
                        <h4 className="text-sm font-semibold text-purple-900 mb-1">
                          Upload your Prisma schema file
                        </h4>
                        <p className="text-xs text-purple-800">
                          Find your <code className="bg-white px-1 rounded">schema.prisma</code> file
                          (usually at <code className="bg-white px-1 rounded">prisma/schema.prisma</code>)
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
              <div className="space-y-4">
                <textarea
                  value={schemaText}
                  onChange={(e) => setSchemaText(e.target.value)}
                  placeholder={getPlaceholder()}
                  rows={14}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono text-sm"
                />
                <p className="text-xs text-gray-600">
                  {schemaFormat === 'prisma'
                    ? 'Paste the full content of your .prisma file including generator, datasource, model, and enum blocks.'
                    : 'Paste CREATE TABLE statements and other DDL from your database schema. Only structure is needed — no INSERT statements or data.'}
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Error Display */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg flex items-start">
            <AlertCircle className="w-5 h-5 mr-2 flex-shrink-0 mt-0.5" />
            <span className="text-sm">{error}</span>
          </div>
        )}

        {/* Submit Button */}
        <button
          type="submit"
          disabled={loading}
          className="w-full bg-blue-600 text-white py-3 px-4 rounded-lg hover:bg-blue-700 transition-colors font-medium disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center justify-center"
        >
          {loading ? (
            <>
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2" />
              Parsing Schema...
            </>
          ) : (
            <>
              <Upload className="w-5 h-5 mr-2" />
              Parse and Upload Schema
            </>
          )}
        </button>
      </form>

      {/* Privacy Notice */}
      <div className="mt-6 p-4 bg-green-50 border border-green-200 rounded-lg">
        <h4 className="text-sm font-semibold text-green-900 mb-2">Privacy-First Design</h4>
        <ul className="text-xs text-green-800 space-y-1">
          <li>✅ We NEVER access your database directly</li>
          <li>✅ We NEVER store your actual data</li>
          <li>✅ We ONLY parse your schema structure (table/column names)</li>
          <li>✅ You run all SQL queries on your own infrastructure</li>
        </ul>
      </div>
    </div>
  )
}