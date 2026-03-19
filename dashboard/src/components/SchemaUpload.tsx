'use client'

import { useState } from 'react'
import { apiClient } from '@/lib/api-client'

interface SchemaUploadProps {
  onUploadSuccess: () => void
}

export default function SchemaUpload({ onUploadSuccess }: SchemaUploadProps) {
  const [name, setName] = useState('')
  const [connectionString, setConnectionString] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setSuccess('')

    if (!name.trim() || !connectionString.trim()) {
      setError('Please provide both name and database connection string')
      return
    }

    try {
      setLoading(true)
      await apiClient.uploadSchema({
        name: name.trim(),
        connection_string: connectionString.trim(),
        include_sample_data: true,
      })

      setSuccess('Schema uploaded successfully!')
      setName('')
      setConnectionString('')

      setTimeout(() => {
        setSuccess('')
        onUploadSuccess()
      }, 1500)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to upload schema')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-xl font-semibold text-gray-900 mb-4">Upload New Schema</h2>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-2">
            Schema Name
          </label>
          <input
            type="text"
            id="name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g., Production Database"
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>

        <div>
          <label htmlFor="connectionString" className="block text-sm font-medium text-gray-700 mb-2">
            Database Connection String
          </label>
          <input
            type="text"
            id="connectionString"
            value={connectionString}
            onChange={(e) => setConnectionString(e.target.value)}
            placeholder="postgresql://user:password@host:port/database"
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono text-sm"
          />
          <p className="mt-2 text-sm text-gray-500">
            Provide your database connection string. The system will connect to your database and automatically introspect the schema.
          </p>
          <div className="mt-2 text-xs text-gray-600 bg-gray-50 p-3 rounded border border-gray-200">
            <p className="font-semibold mb-1">Examples:</p>
            <p className="mb-1">PostgreSQL: <code className="bg-white px-1">postgresql://user:pass@localhost:5432/mydb</code></p>
            <p>MySQL: <code className="bg-white px-1">mysql://user:pass@localhost:3306/mydb</code></p>
          </div>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
            {error}
          </div>
        )}

        {success && (
          <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg">
            {success}
          </div>
        )}

        <button
          type="submit"
          disabled={loading}
          className="w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 transition-colors font-medium disabled:bg-gray-400 disabled:cursor-not-allowed"
        >
          {loading ? 'Uploading...' : 'Upload Schema'}
        </button>
      </form>
    </div>
  )
}
