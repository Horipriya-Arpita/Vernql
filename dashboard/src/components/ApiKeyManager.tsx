'use client'

import { useState } from 'react'

export default function ApiKeyManager() {
  const [showNewKey, setShowNewKey] = useState(false)
  const [newKeyName, setNewKeyName] = useState('')
  const [generatedKey, setGeneratedKey] = useState('')
  const [copied, setCopied] = useState(false)

  const handleGenerateKey = () => {
    if (!newKeyName.trim()) {
      return
    }

    // Generate a random API key for demo purposes
    const key = `tsk_${Array.from({ length: 32 }, () =>
      Math.random().toString(36).charAt(2)
    ).join('')}`

    setGeneratedKey(key)
    setShowNewKey(true)
  }

  const handleCopy = () => {
    navigator.clipboard.writeText(generatedKey)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const handleClose = () => {
    setShowNewKey(false)
    setGeneratedKey('')
    setNewKeyName('')
    setCopied(false)
  }

  return (
    <div className="space-y-6">
      {/* Generate New Key Section */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Generate New API Key</h2>

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
              placeholder="e.g., Production Server, Development"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          <button
            onClick={handleGenerateKey}
            disabled={!newKeyName.trim()}
            className="bg-blue-600 text-white py-2 px-6 rounded-lg hover:bg-blue-700 transition-colors font-medium disabled:bg-gray-400 disabled:cursor-not-allowed"
          >
            Generate API Key
          </button>
        </div>

        {/* New Key Modal/Display */}
        {showNewKey && (
          <div className="mt-6 p-4 bg-green-50 border border-green-200 rounded-lg">
            <div className="flex items-start justify-between mb-3">
              <div>
                <h3 className="text-lg font-semibold text-green-900">API Key Generated!</h3>
                <p className="text-sm text-green-700 mt-1">
                  Make sure to copy this key now. You won't be able to see it again.
                </p>
              </div>
              <button
                onClick={handleClose}
                className="text-green-700 hover:text-green-900 text-xl font-bold"
              >
                ×
              </button>
            </div>

            <div className="bg-white rounded border border-green-300 p-3 font-mono text-sm break-all">
              {generatedKey}
            </div>

            <button
              onClick={handleCopy}
              className="mt-3 bg-green-600 text-white py-2 px-4 rounded-lg hover:bg-green-700 transition-colors font-medium"
            >
              {copied ? 'Copied!' : 'Copy to Clipboard'}
            </button>
          </div>
        )}
      </div>

      {/* API Key Information */}
      <div className="bg-blue-50 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-3">How to Use Your API Key</h3>
        <div className="space-y-3 text-sm text-gray-700">
          <p>1. Include your API key in the request header:</p>
          <pre className="bg-white p-3 rounded border border-blue-200 overflow-x-auto">
            <code>X-API-Key: your_api_key_here</code>
          </pre>

          <p>2. Example with curl:</p>
          <pre className="bg-white p-3 rounded border border-blue-200 overflow-x-auto">
            <code>{`curl -X POST http://localhost:8000/v1/queries \\
  -H "X-API-Key: your_api_key_here" \\
  -H "Content-Type: application/json" \\
  -d '{"question": "Show all users", "schema_id": "schema-id"}'`}</code>
          </pre>

          <p>3. Keep your API keys secure:</p>
          <ul className="list-disc list-inside space-y-1 ml-2">
            <li>Never commit keys to version control</li>
            <li>Use environment variables in your applications</li>
            <li>Rotate keys regularly</li>
            <li>Delete unused keys</li>
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
        "question": "Show all users",
        "schema_id": "your-schema-id"
    }
)

result = response.json()
print(result["sql"])`}</code>
            </pre>
          </div>

          {/* JavaScript Example */}
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-2">JavaScript (Node.js)</h4>
            <pre className="bg-gray-50 p-4 rounded border border-gray-200 overflow-x-auto text-sm">
              <code>{`const axios = require('axios');

const API_KEY = 'your_api_key_here';
const BASE_URL = 'http://localhost:8000';

async function generateSQL(question, schemaId) {
  const response = await axios.post(
    \`\${BASE_URL}/v1/queries\`,
    {
      question: question,
      schema_id: schemaId
    },
    {
      headers: { 'X-API-Key': API_KEY }
    }
  );

  return response.data.sql;
}`}</code>
            </pre>
          </div>
        </div>
      </div>
    </div>
  )
}
