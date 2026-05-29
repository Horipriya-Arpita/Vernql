'use client'

import { useState, useEffect } from 'react'
import { apiClient } from '@/lib/api-client'
import type { APIKeyResponse } from '@/lib/types'
import { Key, Trash2, Clock, AlertCircle, CheckCircle2, Copy, Check } from 'lucide-react'
import toast from 'react-hot-toast'
import { useAuth } from '@/contexts/AuthContext'

const inputClass =
  'w-full px-4 py-2.5 border border-slate-200 dark:border-slate-600 rounded-xl bg-white dark:bg-slate-700/50 text-slate-900 dark:text-white placeholder:text-slate-400 dark:placeholder:text-slate-500 focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition text-[0.9375rem]'

const inputSmClass =
  'w-full px-3 py-2 border border-slate-200 dark:border-slate-600 rounded-xl bg-white dark:bg-slate-700/50 text-slate-900 dark:text-white placeholder:text-slate-400 dark:placeholder:text-slate-500 focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition text-sm'

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

  useEffect(() => { loadApiKeys() }, [includeInactive])

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
    if (!newKeyName.trim()) { toast.error('Please provide a name for the API key'); return }
    try {
      setCreatingKey(true)
      const expiresAt = expiresInDays
        ? new Date(Date.now() + Number(expiresInDays) * 86_400_000).toISOString()
        : undefined
      const response = await apiClient.createApiKey({
        name: newKeyName.trim(),
        expires_at: expiresAt,
        rate_limit_per_minute: rateLimitPerMinute !== '' ? Number(rateLimitPerMinute) : undefined,
        rate_limit_per_hour:   rateLimitPerHour   !== '' ? Number(rateLimitPerHour)   : undefined,
      })
      setGeneratedKey(response.api_key)
      setNewKeyName(''); setExpiresInDays(''); setRateLimitPerMinute('60'); setRateLimitPerHour('1000')
      setShowAdvanced(false); setShowNewKeyForm(false)
      await loadApiKeys()
      if (!activeApiKey) {
        setApiKey(response.api_key)
        toast.success('API key created and activated!')
      } else {
        toast.success('API key created! Click "Use This Key" to activate it.')
      }
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to create API key')
    } finally {
      setCreatingKey(false)
    }
  }

  const handleRevokeKey = async (keyId: string, keyName: string | null) => {
    if (!confirm(`Are you sure you want to revoke the API key "${keyName || keyId}"? This action cannot be undone.`)) return
    try {
      await apiClient.revokeApiKey(keyId)
      toast.success('API key revoked successfully')
      await loadApiKeys()
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to revoke API key')
    }
  }

  return (
    <div className="space-y-6">

      {/* ── Active key banner ── */}
      {activeApiKey && (
        <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800/50 rounded-2xl p-4 flex items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <CheckCircle2 className="w-5 h-5 text-blue-600 dark:text-blue-400 flex-shrink-0" />
            <div>
              <h3 className="text-sm font-semibold text-blue-900 dark:text-blue-200">Active API Key Configured</h3>
              <p className="text-xs text-blue-700 dark:text-blue-400 mt-0.5">
                All API requests are authenticated with your active API key.
              </p>
            </div>
          </div>
          <button
            onClick={() => {
              if (confirm('Deactivate your current API key?')) {
                setApiKey('')
                toast.success('API key deactivated')
              }
            }}
            className="text-blue-700 dark:text-blue-400 hover:text-blue-900 dark:hover:text-blue-200 text-sm font-medium px-3 py-1.5 rounded-lg hover:bg-blue-100 dark:hover:bg-blue-800/40 transition-colors flex-shrink-0"
          >
            Deactivate
          </button>
        </div>
      )}

      {/* ── Newly generated key ── */}
      {generatedKey && (
        <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800/50 rounded-2xl p-6">
          <div className="flex items-start justify-between mb-3">
            <div className="flex items-center gap-3">
              <CheckCircle2 className="w-6 h-6 text-green-600 dark:text-green-400" />
              <div>
                <h3 className="text-base font-semibold text-green-900 dark:text-green-200">API Key Created!</h3>
                <p className="text-sm text-green-700 dark:text-green-400 mt-0.5">
                  Copy this key now — you won&apos;t be able to see it again.
                </p>
              </div>
            </div>
            <button onClick={() => setGeneratedKey('')} className="text-green-700 dark:text-green-400 hover:text-green-900 text-xl leading-none">×</button>
          </div>
          <div className="bg-white dark:bg-slate-800 rounded-xl border border-green-200 dark:border-green-800/50 p-3 font-mono text-sm break-all text-slate-800 dark:text-slate-200 mb-4">
            {generatedKey}
          </div>
          <div className="flex gap-3">
            <button
              onClick={() => { navigator.clipboard.writeText(generatedKey); toast.success('Copied!') }}
              className="bg-green-600 hover:bg-green-700 text-white py-2 px-4 rounded-xl font-medium text-sm inline-flex items-center gap-2 transition-colors"
            >
              <Copy className="w-4 h-4" /> Copy to Clipboard
            </button>
            {activeApiKey && (
              <button
                onClick={() => { setApiKey(generatedKey); toast.success('API key activated!'); setGeneratedKey('') }}
                className="bg-blue-600 hover:bg-blue-700 text-white py-2 px-4 rounded-xl font-medium text-sm inline-flex items-center gap-2 transition-colors"
              >
                <Check className="w-4 h-4" /> Use This Key
              </button>
            )}
          </div>
        </div>
      )}

      {/* ── Keys list card ── */}
      <div className="bg-white dark:bg-slate-800/70 rounded-2xl border border-slate-100 dark:border-slate-700/50 p-6">
        <div className="flex items-center justify-between mb-5">
          <h2 className="text-lg font-semibold text-slate-900 dark:text-white flex items-center gap-2">
            <Key className="w-5 h-5 text-blue-600 dark:text-blue-400" />
            API Keys
          </h2>
          <button
            onClick={() => setShowNewKeyForm(!showNewKeyForm)}
            className="bg-blue-600 hover:bg-blue-700 text-white py-2 px-4 rounded-xl font-medium text-sm transition-colors shadow-blue-sm"
          >
            {showNewKeyForm ? 'Cancel' : '+ Create New Key'}
          </button>
        </div>

        {/* Create form */}
        {showNewKeyForm && (
          <form onSubmit={handleCreateKey} className="mb-6 p-5 bg-slate-50 dark:bg-slate-700/30 rounded-xl border border-slate-200 dark:border-slate-600/50 space-y-4">
            <div>
              <label htmlFor="keyName" className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">
                Key Name
              </label>
              <input
                type="text" id="keyName" value={newKeyName}
                onChange={(e) => setNewKeyName(e.target.value)}
                placeholder="e.g., Production Server, Development, Widget"
                className={inputClass} autoFocus
              />
            </div>

            <button
              type="button"
              onClick={() => setShowAdvanced(v => !v)}
              className="text-sm text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 font-medium"
            >
              {showAdvanced ? '▲ Hide advanced options' : '▼ Advanced options (expiry, rate limits)'}
            </button>

            {showAdvanced && (
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-3 border-t border-slate-200 dark:border-slate-600/50">
                <div>
                  <label htmlFor="expiresInDays" className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">
                    Expires in (days)
                  </label>
                  <input type="number" id="expiresInDays" value={expiresInDays}
                    onChange={(e) => setExpiresInDays(e.target.value)}
                    placeholder="Never" min={1} max={3650} className={inputSmClass} />
                  <p className="text-xs text-slate-400 dark:text-slate-500 mt-1">Leave blank for no expiry</p>
                </div>
                <div>
                  <label htmlFor="rpmLimit" className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">
                    Requests / minute
                  </label>
                  <input type="number" id="rpmLimit" value={rateLimitPerMinute}
                    onChange={(e) => setRateLimitPerMinute(e.target.value)}
                    min={1} max={10000} className={inputSmClass} />
                </div>
                <div>
                  <label htmlFor="rphLimit" className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">
                    Requests / hour
                  </label>
                  <input type="number" id="rphLimit" value={rateLimitPerHour}
                    onChange={(e) => setRateLimitPerHour(e.target.value)}
                    min={1} max={100000} className={inputSmClass} />
                </div>
              </div>
            )}

            <button
              type="submit" disabled={creatingKey || !newKeyName.trim()}
              className="bg-blue-600 hover:bg-blue-700 text-white py-2.5 px-6 rounded-xl font-semibold text-sm shadow-blue-sm disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {creatingKey ? 'Creating…' : 'Generate API Key'}
            </button>
          </form>
        )}

        {/* Filter toggle */}
        <div className="mb-4">
          <label className="flex items-center gap-2 text-sm text-slate-700 dark:text-slate-300 cursor-pointer">
            <input
              type="checkbox" checked={includeInactive}
              onChange={(e) => setIncludeInactive(e.target.checked)}
              className="rounded border-slate-300 dark:border-slate-600 text-blue-600 focus:ring-blue-500"
            />
            Show revoked keys
          </label>
        </div>

        {/* List */}
        {loading ? (
          <div className="text-center py-10">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
            <p className="text-slate-500 dark:text-slate-400 mt-3 text-sm">Loading API keys…</p>
          </div>
        ) : keys.length === 0 ? (
          <div className="text-center py-14 bg-slate-50 dark:bg-slate-700/20 rounded-xl">
            <Key className="w-14 h-14 text-slate-300 dark:text-slate-600 mx-auto mb-4" />
            <p className="text-slate-500 dark:text-slate-400 mb-1">
              {includeInactive ? 'No API keys found' : 'No active API keys'}
            </p>
            <p className="text-sm text-slate-400 dark:text-slate-500">Create your first API key to get started!</p>
          </div>
        ) : (
          <div className="space-y-3">
            {keys.map((key) => (
              <div key={key.id}
                className={`border rounded-xl p-4 transition-colors ${
                  key.is_active
                    ? 'border-slate-200 dark:border-slate-600/50 bg-white dark:bg-slate-700/20'
                    : 'border-slate-200 dark:border-slate-700/50 bg-slate-50 dark:bg-slate-700/10'
                }`}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2.5 mb-2 flex-wrap">
                      <h3 className="text-base font-medium text-slate-900 dark:text-white">
                        {key.name || 'Unnamed Key'}
                      </h3>
                      <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        key.is_active
                          ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400'
                          : 'bg-slate-200 dark:bg-slate-700 text-slate-600 dark:text-slate-400'
                      }`}>
                        {key.is_active ? 'Active' : 'Revoked'}
                      </span>
                    </div>
                    <div className="space-y-1 text-sm text-slate-500 dark:text-slate-400">
                      <div className="flex items-center gap-1.5">
                        <Clock className="w-3.5 h-3.5" />
                        <span>Created: {new Date(key.created_at).toLocaleDateString()}</span>
                      </div>
                      {key.last_used_at && (
                        <div className="flex items-center gap-1.5">
                          <CheckCircle2 className="w-3.5 h-3.5" />
                          <span>Last used: {new Date(key.last_used_at).toLocaleDateString()}</span>
                        </div>
                      )}
                      {key.expires_at && (
                        <div className="flex items-center gap-1.5">
                          <AlertCircle className="w-3.5 h-3.5" />
                          <span>Expires: {new Date(key.expires_at).toLocaleDateString()}</span>
                        </div>
                      )}
                      <div className="font-mono text-xs text-slate-400 dark:text-slate-500 mt-1.5">
                        ID: {key.id}
                      </div>
                    </div>
                  </div>
                  {key.is_active && (
                    <button
                      onClick={() => handleRevokeKey(key.id, key.name)}
                      className="text-red-500 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300 hover:bg-red-50 dark:hover:bg-red-900/20 p-2 rounded-lg transition-colors flex-shrink-0"
                      title="Revoke this API key"
                    >
                      <Trash2 className="w-4.5 h-4.5" />
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* ── How API keys work ── */}
      <div className="bg-blue-50 dark:bg-blue-900/15 border border-blue-100 dark:border-blue-800/30 rounded-2xl p-6">
        <h3 className="text-base font-semibold text-slate-900 dark:text-white mb-3">How API Keys Work</h3>
        <div className="space-y-3 text-sm text-slate-700 dark:text-slate-300">
          <p className="font-medium text-slate-800 dark:text-slate-200">Dashboard Usage (Automatic):</p>
          <ul className="list-disc list-inside space-y-1 ml-2 mb-4 text-slate-600 dark:text-slate-400">
            <li>When you create your first API key, it&apos;s automatically activated</li>
            <li>The dashboard includes it in all API requests automatically</li>
            <li>You can deactivate or switch keys anytime using the controls above</li>
          </ul>
          <p className="font-medium text-slate-800 dark:text-slate-200">External API Usage:</p>
          <p className="mb-2 text-slate-600 dark:text-slate-400">Include your API key in the request header:</p>
          <pre className="bg-white dark:bg-slate-800 p-3 rounded-xl border border-blue-200 dark:border-blue-800/40 overflow-x-auto text-xs text-slate-700 dark:text-slate-300 mb-3">
            <code>X-API-Key: your_api_key_here</code>
          </pre>
          <p className="font-medium text-slate-800 dark:text-slate-200 mt-2">Security Best Practices:</p>
          <ul className="list-disc list-inside space-y-1 ml-2 text-slate-600 dark:text-slate-400">
            <li>Copy your API key immediately — it&apos;s only shown once at creation</li>
            <li>Never commit keys to version control</li>
            <li>Use environment variables in your applications</li>
            <li>Rotate keys regularly and revoke old ones</li>
          </ul>
        </div>
      </div>

      {/* ── Integration Examples ── */}
      <div className="bg-white dark:bg-slate-800/70 rounded-2xl border border-slate-100 dark:border-slate-700/50 p-6">
        <h3 className="text-base font-semibold text-slate-900 dark:text-white mb-5">Integration Examples</h3>
        <div className="space-y-5">
          <div>
            <h4 className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">Python</h4>
            <pre className="bg-slate-900 dark:bg-slate-950 text-slate-100 p-4 rounded-xl overflow-x-auto text-xs leading-relaxed border border-slate-800">
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
print(response.json()["generated_sql"])`}</code>
            </pre>
          </div>
          <div>
            <h4 className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">JavaScript (Node.js)</h4>
            <pre className="bg-slate-900 dark:bg-slate-950 text-slate-100 p-4 rounded-xl overflow-x-auto text-xs leading-relaxed border border-slate-800">
              <code>{`const axios = require('axios');

const API_KEY = 'your_api_key_here';
const BASE_URL = 'http://localhost:8000';

async function generateSQL(query, schemaId) {
  const { data } = await axios.post(
    \`\${BASE_URL}/v1/queries\`,
    { query, schema_id: schemaId },
    { headers: { 'X-API-Key': API_KEY } }
  );
  return data.generated_sql;
}`}</code>
            </pre>
          </div>
        </div>
      </div>

    </div>
  )
}
