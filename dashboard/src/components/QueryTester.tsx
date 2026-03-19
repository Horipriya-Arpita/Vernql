'use client'

import { useState, useEffect } from 'react'
import { apiClient } from '@/lib/api-client'
import type { Schema, Query } from '@/lib/types'

export default function QueryTester() {
  const [schemas, setSchemas] = useState<Schema[]>([])
  const [selectedSchemaId, setSelectedSchemaId] = useState('')
  const [question, setQuestion] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<Query | null>(null)
  const [error, setError] = useState('')
  const [history, setHistory] = useState<Query[]>([])

  useEffect(() => {
    loadSchemas()
    loadHistory()
  }, [])

  const loadSchemas = async () => {
    try {
      const response = await apiClient.listSchemas()
      setSchemas(response.schemas)
      if (response.schemas.length > 0) {
        setSelectedSchemaId(response.schemas[0].id)
      }
    } catch (err) {
      console.error('Failed to load schemas:', err)
    }
  }

  const loadHistory = async () => {
    try {
      const response = await apiClient.getQueryHistory(undefined, 10)
      setHistory(response.queries)
    } catch (err) {
      console.error('Failed to load history:', err)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setResult(null)

    if (!question.trim() || !selectedSchemaId) {
      setError('Please select a schema and enter a question')
      return
    }

    try {
      setLoading(true)
      const query = await apiClient.generateSQL({
        query: question.trim(),
        schema_id: selectedSchemaId,
      })

      setResult(query)
      loadHistory() // Refresh history
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate SQL')
    } finally {
      setLoading(false)
    }
  }

  const handleFeedback = async (queryId: string, isCorrect: boolean) => {
    try {
      await apiClient.submitQueryFeedback(queryId, {
        is_helpful: isCorrect,
        is_correct: isCorrect,
        feedback_notes: isCorrect ? 'Correct' : 'Incorrect',
      })

      // Update the result to show feedback was submitted
      if (result && result.id === queryId) {
        setResult({ ...result })
      }
    } catch (err) {
      console.error('Failed to submit feedback:', err)
    }
  }

  const exampleQuestions = [
    'Show all users',
    'Count total orders by status',
    'List top 10 customers by revenue',
    'Show recent activity in the last 30 days',
  ]

  return (
    <div className="space-y-6">
      {/* Query Form */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Test Your Queries</h2>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="schema" className="block text-sm font-medium text-gray-700 mb-2">
              Select Schema
            </label>
            <select
              id="schema"
              value={selectedSchemaId}
              onChange={(e) => setSelectedSchemaId(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              {schemas.length === 0 ? (
                <option value="">No schemas available</option>
              ) : (
                schemas.map((schema) => (
                  <option key={schema.id} value={schema.id}>
                    {schema.name} ({schema.db_type.toUpperCase()})
                  </option>
                ))
              )}
            </select>
          </div>

          <div>
            <label htmlFor="question" className="block text-sm font-medium text-gray-700 mb-2">
              Natural Language Question
            </label>
            <textarea
              id="question"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="e.g., Show me all users who signed up in the last 30 days"
              rows={3}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          <div className="flex flex-wrap gap-2">
            <span className="text-sm text-gray-600 mr-2">Try:</span>
            {exampleQuestions.map((example, index) => (
              <button
                key={index}
                type="button"
                onClick={() => setQuestion(example)}
                className="text-sm bg-gray-100 text-gray-700 px-3 py-1 rounded hover:bg-gray-200 transition-colors"
              >
                {example}
              </button>
            ))}
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading || !selectedSchemaId || !question.trim()}
            className="w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 transition-colors font-medium disabled:bg-gray-400 disabled:cursor-not-allowed"
          >
            {loading ? 'Generating SQL...' : 'Generate SQL'}
          </button>
        </form>
      </div>

      {/* Result */}
      {result && (
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Generated SQL</h3>
            <div className="flex items-center space-x-2">
              <span className="text-sm text-gray-600">Confidence:</span>
              <span
                className={`px-3 py-1 rounded-full text-sm font-medium ${
                  result.confidence_score >= 0.8
                    ? 'bg-green-100 text-green-800'
                    : result.confidence_score >= 0.6
                    ? 'bg-yellow-100 text-yellow-800'
                    : 'bg-red-100 text-red-800'
                }`}
              >
                {(result.confidence_score * 100).toFixed(0)}%
              </span>
            </div>
          </div>

          <div className="bg-gray-50 rounded-lg p-4 mb-4">
            <pre className="text-sm font-mono whitespace-pre-wrap overflow-x-auto">
              {result.generated_sql}
            </pre>
          </div>

          {result.warnings && result.warnings.length > 0 && (
            <div className="mb-4 p-4 bg-yellow-50 rounded-lg">
              <h4 className="text-sm font-semibold text-gray-900 mb-2">Warnings</h4>
              <ul className="text-sm text-gray-700 list-disc list-inside">
                {result.warnings.map((warning, idx) => (
                  <li key={idx}>{warning}</li>
                ))}
              </ul>
            </div>
          )}

          <div className="flex items-center justify-between pt-4 border-t border-gray-200">
            <span className="text-sm text-gray-600">Was this SQL query correct?</span>
            <div className="flex space-x-3">
              <button
                onClick={() => handleFeedback(result.id, true)}
                className="px-4 py-2 bg-green-100 text-green-700 rounded-lg hover:bg-green-200 transition-colors text-sm font-medium"
              >
                Yes
              </button>
              <button
                onClick={() => handleFeedback(result.id, false)}
                className="px-4 py-2 bg-red-100 text-red-700 rounded-lg hover:bg-red-200 transition-colors text-sm font-medium"
              >
                No
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Query History */}
      {history.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Queries</h3>
          <div className="space-y-3">
            {history.map((query) => (
              <div key={query.id} className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-start justify-between mb-2">
                  <p className="text-sm font-medium text-gray-900">{query.natural_language_query}</p>
                  <span
                    className={`px-2 py-1 rounded text-xs font-medium ${
                      query.confidence_score >= 0.8
                        ? 'bg-green-100 text-green-800'
                        : query.confidence_score >= 0.6
                        ? 'bg-yellow-100 text-yellow-800'
                        : 'bg-red-100 text-red-800'
                    }`}
                  >
                    {(query.confidence_score * 100).toFixed(0)}%
                  </span>
                </div>
                <pre className="text-xs font-mono text-gray-600 bg-gray-50 p-2 rounded overflow-x-auto">
                  {query.generated_sql}
                </pre>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
