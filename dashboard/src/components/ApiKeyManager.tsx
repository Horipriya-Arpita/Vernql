'use client'

import { useState, useEffect } from 'react'
import { apiClient } from '@/lib/api-client'
import type { APIKeyResponse } from '@/lib/types'
import { Key, Trash2, Clock, AlertCircle, CheckCircle2, Copy, Check } from 'lucide-react'
import toast from 'react-hot-toast'
import { useAuth } from '@/contexts/AuthContext'

export default function ApiKeyManager() {
  const { apiKey: activeApiKey, setApiKey } = useAuth()
  const [keys, setKeys] = useState<APIKeyResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [showNewKeyForm, setShowNewKeyForm] = useState(false)
  const [newKeyName, setNewKeyName] = useState('')
  const [expiresInDays, setExpiresInDays] = useState<string>('')
  const [rateLimitPerMinute, setRateLimitPerMinute] = useState<string>('60')
  const [rateLimitPerHour, setRateLimitPerHour] = useState<string>('1000')
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [generatedKey, setGeneratedKey] = useState('')
  const [creatingKey, setCreatingKey] = useState(false)
  const [includeInactive, setIncludeInactive] = useState(false)

  useEffect(() => {
    loadApiKeys()
  }, [includeInactive])

  const loadApiKeys = async () => {
    try {
      setLoading(true)
      const response = await apiClient.listApiKeys(includeInactive)
      setKeys(response.keys)
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to load API keys')
    } finally {
      setLoading(false)
    }
  }

  const handleCreateKey = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!newKeyName.trim()) {
      toast.error('Please provide a name for the API key')
      return
    }

    try {
      setCreatingKey(true)

      // Build optional fields
      const expiresAt = expiresInDays
        ? new Date(Date.now() + Number(expiresInDays) * 86_400_000).toISOString()
        : undefined
      const rpmOverride = rateLimitPerMinute !== '' ? Number(rateLimitPerMinute) : undefined
      const rphOverride = rateLimitPerHour !== '' ? Number(rateLimitPerHour) : undefined

      const response = await apiClient.createApiKey({
        name: newKeyName.trim(),
        expires_at: expiresAt,
        rate_limit_per_minute: rpmOverride,
        rate_limit_per_hour: rphOverride,
      })

      setGeneratedKey(response.api_key)
      setNewKeyName('')
      setExpiresInDays('')
      setRateLimitPerMinute('60')
      setRateLimitPerHour('1000')
      setShowAdvanced(false)
      setShowNewKeyForm(false)

      // Reload the keys list
      await loadApiKeys()

      // Auto-activate if user has no active API key (first-time setup)
      if (!activeApiKey) {
        setApiKey(response.api_key)
        toast.success('API key created and activated! You can now use all dashboard features.')
      } else {
        toast.success('API key created successfully! Click "Use This Key" to activate it.')
      }
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to create API key')
    } finally {
      setCreatingKey(false)
    }
  }

  const handleCopyKey = (key: string) => {
    navigator.clipboard.writeText(key)
    toast.success('API key copied to clipboard!')
  }

  const handleRevokeKey = async (keyId: string, keyName: string | null) => {
    if (!confirm(`Are you sure you want to revoke the API key "${keyName || keyId}"? This action cannot be undone.`)) {
      return
    }

    try {
      await apiClient.revokeApiKey(keyId)
      toast.success('API key revoked successfully')
      await loadApiKeys()
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to revoke API key')
    }
  }

  const handleCloseGeneratedKey = () => {
    setGeneratedKey('')
  }

  const handleUseThisKey = () => {
    if (generatedKey) {
      setApiKey(generatedKey)
      toast.success('API key activated! All API requests will now use this key.')
      setGeneratedKey('')
    }
  }

  return (
    <div className="space-y-6">
      {/* Currently Active Key Status */}
      {activeApiKey && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <CheckCircle2 className="w-5 h-5 text-blue-600 mr-3" />
              <div>
                <h3 className="text-sm font-semibold text-blue-900">Active API Key Configured</h3>
                <p className="text-xs text-blue-700 mt-1">
                  All API requests are currently authenticated with your active API key.
                </p>
              </div>
            </div>
            <button
              onClick={() => {
                if (confirm('Are you sure you want to deactivate your current API key? You will need to activate another key to use the dashboard.')) {
                  setApiKey('')
                  toast.success('API key deactivated')
                }
              }}
              className="text-blue-700 hover:text-blue-900 text-sm font-medium px-3 py-1 rounded hover:bg-blue-100 transition-colors"
            >
              Deactivate
            </button>
          </div>
        </div>
      )}

      {/* Generated Key Display Modal */}
      {generatedKey && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-6">
          <div className="flex items-start justify-between mb-3">
            <div className="flex items-center">
              <CheckCircle2 className="w-6 h-6 text-green-600 mr-3" />
              <div>
                <h3 className="text-lg font-semibold text-green-900">API Key Created!</h3>
                <p className="text-sm text-green-700 mt-1">
                  Make sure to copy this key now. You won't be able to see it again.
                </p>
              </div>
            </div>
            <button
              onClick={handleCloseGeneratedKey}
              className="text-green-700 hover:text-green-900 text-xl font-bold"
            >
              ×
            </button>
          </div>

          <div className="bg-white rounded border border-green-300 p-3 font-mono text-sm break-all mb-3">
            {generatedKey}
          </div>

          <div className="flex gap-3">
            <button
              onClick={() => handleCopyKey(generatedKey)}
              className="bg-green-600 text-white py-2 px-4 rounded-lg hover:bg-green-700 transition-colors font-medium inline-flex items-center"
            >
              <Copy className="w-4 h-4 mr-2" />
              Copy to Clipboard
            </button>

            {activeApiKey && (
              <button
                onClick={handleUseThisKey}
                className="bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 transition-colors font-medium inline-flex items-center"
              >
                <Check className="w-4 h-4 mr-2" />
                Use This Key
              </button>
            )}
          </div>
        </div>
      )}

      {/* Create New Key Section */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-gray-900 flex items-center">
            <Key className="w-6 h-6 mr-2 text-blue-600" />
            API Keys
          </h2>
          <button
            onClick={() => setShowNewKeyForm(!showNewKeyForm)}
            className="bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 transition-colors font-medium text-sm"
          >
            {showNewKeyForm ? 'Cancel' : '+ Create New Key'}
          </button>
        </div>

        {showNewKeyForm && (
          <form onSubmit={handleCreateKey} className="mb-6 p-4 bg-gray-50 rounded-lg">
            <div className="space-y-4">
              <div>
                <label htmlFor="keyName" className="block text-sm font-medium text-gray-700 mb-2">
                  Key Name (for your reference)
                </label>
                <input
                  type="text"
                  id="keyName"
                  value={newKeyName}
                  onChange={(e) => setNewKeyName(e.target.value)}
                  placeholder="e.g., Production Server, Development, Widget Integration"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  autoFocus
                />
              </div>

              {/* Advanced options toggle */}
              <button
                type="button"
                onClick={() => setShowAdvanced((v) => !v)}
                className="text-sm text-blue-600 hover:text-blue-800 font-medium"
              >
                {showAdvanced ? '▲ Hide advanced options' : '▼ Advanced options (expiry, rate limits)'}
              </button>

              {showAdvanced && (
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-2 border-t border-gray-200">
                  <div>
                    <label htmlFor="expiresInDays" className="block text-sm font-medium text-gray-700 mb-1">
                      Expires in (days)
                    </label>
                    <input
                      type="number"
                      id="expiresInDays"
                      value={expiresInDays}
                      onChange={(e) => setExpiresInDays(e.target.value)}
                      placeholder="Never"
                      min={1}
                      max={3650}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                    <p className="text-xs text-gray-400 mt-1">Leave blank for no expiry</p>
                  </div>
                  <div>
                    <label htmlFor="rpmLimit" className="block text-sm font-medium text-gray-700 mb-1">
                      Requests / minute
                    </label>
                    <input
                      type="number"
                      id="rpmLimit"
                      value={rateLimitPerMinute}
                      onChange={(e) => setRateLimitPerMinute(e.target.value)}
                      min={1}
                      max={10000}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>
                  <div>
                    <label htmlFor="rphLimit" className="block text-sm font-medium text-gray-700 mb-1">
                      Requests / hour
                    </label>
                    <input
                      type="number"
                      id="rphLimit"
                      value={rateLimitPerHour}
                      onChange={(e) => setRateLimitPerHour(e.target.value)}
                      min={1}
                      max={100000}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>
                </div>
              )}

              <button
                type="submit"
                disabled={creatingKey || !newKeyName.trim()}
                className="bg-blue-600 text-white py-2 px-6 rounded-lg hover:bg-blue-700 transition-colors font-medium disabled:bg-gray-400 disabled:cursor-not-allowed"
              >
                {creatingKey ? 'Creating...' : 'Generate API Key'}
              </button>
            </div>
          </form>
        )}

        {/* Filter Toggle */}
        <div className="mb-4">
          <label className="flex items-center space-x-2 text-sm text-gray-700 cursor-pointer">
            <input
              type="checkbox"
              checked={includeInactive}
              onChange={(e) => setIncludeInactive(e.target.checked)}
              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <span>Show revoked keys</span>
          </label>
        </div>

        {/* API Keys List */}
        {loading ? (
          <div className="text-center py-8">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <p className="text-gray-500 mt-2">Loading API keys...</p>
          </div>
        ) : keys.length === 0 ? (
          <div className="text-center py-12 bg-gray-50 rounded-lg">
            <Key className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-500 mb-2">
              {includeInactive ? 'No API keys found' : 'No active API keys'}
            </p>
            <p className="text-sm text-gray-400">Create your first API key to get started!</p>
          </div>
        ) : (
          <div className="space-y-3">
            {keys.map((key) => (
              <div
                key={key.id}
                className={`border rounded-lg p-4 ${
                  key.is_active ? 'border-gray-200 bg-white' : 'border-gray-300 bg-gray-50'
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3 mb-2">
                      <h3 className="text-lg font-medium text-gray-900">
                        {key.name || 'Unnamed Key'}
                      </h3>
                      <span
                        className={`px-2 py-1 rounded text-xs font-medium ${
                          key.is_active
                            ? 'bg-green-100 text-green-800'
                            : 'bg-gray-200 text-gray-700'
                        }`}
                      >
                        {key.is_active ? 'Active' : 'Revoked'}
                      </span>
                    </div>

                    <div className="space-y-1 text-sm text-gray-600">
                      <div className="flex items-center">
                        <Clock className="w-4 h-4 mr-2" />
                        <span>Created: {new Date(key.created_at).toLocaleDateString()}</span>
                      </div>

                      {key.last_used_at && (
                        <div className="flex items-center">
                          <CheckCircle2 className="w-4 h-4 mr-2" />
                          <span>Last used: {new Date(key.last_used_at).toLocaleDateString()}</span>
                        </div>
                      )}

                      {key.expires_at && (
                        <div className="flex items-center">
                          <AlertCircle className="w-4 h-4 mr-2" />
                          <span>Expires: {new Date(key.expires_at).toLocaleDateString()}</span>
                        </div>
                      )}

                      <div className="font-mono text-xs text-gray-400 mt-2">
                        ID: {key.id}
                      </div>
                    </div>
                  </div>

                  {key.is_active && (
                    <button
                      onClick={() => handleRevokeKey(key.id, key.name)}
                      className="ml-4 text-red-600 hover:text-red-800 hover:bg-red-50 p-2 rounded transition-colors"
                      title="Revoke this API key"
                    >
                      <Trash2 className="w-5 h-5" />
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* API Key Information */}
      <div className="bg-blue-50 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-3">How API Keys Work in This Dashboard</h3>
        <div className="space-y-3 text-sm text-gray-700">
          <p className="font-medium">Dashboard Usage (Automatic):</p>
          <ul className="list-disc list-inside space-y-1 ml-2 mb-4">
            <li>When you create your first API key, it's automatically activated</li>
            <li>The dashboard automatically includes it in all API requests</li>
            <li>You can deactivate or switch keys anytime using the controls above</li>
            <li>Your active key is securely stored and persists across sessions</li>
          </ul>

          <p className="font-medium">External API Usage (Manual):</p>
          <p className="mb-2">Include your API key in the request header:</p>
          <pre className="bg-white p-3 rounded border border-blue-200 overflow-x-auto mb-3">
            <code>X-API-Key: your_api_key_here</code>
          </pre>

          <p className="mb-2">Example with curl:</p>
          <pre className="bg-white p-3 rounded border border-blue-200 overflow-x-auto mb-3">
            <code>{`curl -X POST http://localhost:8000/v1/queries \\
  -H "X-API-Key: your_api_key_here" \\
  -H "Content-Type: application/json" \\
  -d '{"query": "Show all users", "schema_id": "schema-id"}'`}</code>
          </pre>

          <p className="font-medium">Security Best Practices:</p>
          <ul className="list-disc list-inside space-y-1 ml-2">
            <li>Copy your API key immediately - it's only shown once at creation</li>
            <li>Never commit keys to version control</li>
            <li>Use environment variables in your applications</li>
            <li>Rotate keys regularly and revoke old ones</li>
            <li>Create separate keys for different environments (dev/staging/prod)</li>
          </ul>
        </div>
      </div>

      {/* Integration Code Snippets */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Integration Examples</h3>

        <div className="space-y-4">
          {/* Python Example */}
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-2">Python</h4>
            <pre className="bg-gray-50 p-4 rounded border border-gray-200 overflow-x-auto text-sm">
              <code>{`import requests

API_KEY = "your_api_key_here"
BASE_URL = "http://localhost:8000"

response = requests.post(
    f"{BASE_URL}/v1/queries",
    headers={"X-API-Key": API_KEY},
    json={
        "query": "Show all users",
        "schema_id": "your-schema-id"
    }
)

result = response.json()
print(result["generated_sql"])`}</code>
            </pre>
          </div>

          {/* JavaScript Example */}
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-2">JavaScript (Node.js)</h4>
            <pre className="bg-gray-50 p-4 rounded border border-gray-200 overflow-x-auto text-sm">
              <code>{`const axios = require('axios');

const API_KEY = 'your_api_key_here';
const BASE_URL = 'http://localhost:8000';

async function generateSQL(query, schemaId) {
  const response = await axios.post(
    \`\${BASE_URL}/v1/queries\`,
    {
      query: query,
      schema_id: schemaId
    },
    {
      headers: { 'X-API-Key': API_KEY }
    }
  );

  return response.data.generated_sql;
}`}</code>
            </pre>
          </div>
        </div>
      </div>
    </div>
  )
}
