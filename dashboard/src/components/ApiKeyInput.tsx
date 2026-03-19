'use client'

import { useState } from 'react'
import { useAuth } from '@/contexts/AuthContext'

export default function ApiKeyInput() {
  const [inputKey, setInputKey] = useState('')
  const [error, setError] = useState('')
  const { setApiKey } = useAuth()

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    if (!inputKey.trim()) {
      setError('Please enter an API key')
      return
    }

    setApiKey(inputKey.trim())
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-8">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Welcome to TextSQL</h1>
          <p className="text-gray-600">Enter your API key to get started</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="apiKey" className="block text-sm font-medium text-gray-700 mb-2">
              API Key
            </label>
            <input
              type="text"
              id="apiKey"
              value={inputKey}
              onChange={(e) => {
                setInputKey(e.target.value)
                setError('')
              }}
              placeholder="Enter your API key"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
          </div>

          <button
            type="submit"
            className="w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 transition-colors font-medium"
          >
            Continue
          </button>
        </form>

        <div className="mt-6 pt-6 border-t border-gray-200">
          <p className="text-sm text-gray-600 text-center">
            Don't have an API key?{' '}
            <a href="http://localhost:8000/docs" target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:text-blue-700">
              Check the API docs
            </a>
          </p>
        </div>
      </div>
    </div>
  )
}
