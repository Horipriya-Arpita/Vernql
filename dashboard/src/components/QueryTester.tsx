'use client'

import { useState, useEffect } from 'react'
import { apiClient } from '@/lib/api-client'
import type { Schema, Query } from '@/lib/types'

const inputClass =
  'w-full px-4 py-2.5 border border-slate-200 dark:border-slate-600 rounded-xl bg-white dark:bg-slate-700/50 text-slate-900 dark:text-white placeholder:text-slate-400 dark:placeholder:text-slate-500 focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition text-[0.9375rem]'

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
      loadHistory()
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
      if (result && result.id === queryId) setResult({ ...result })
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

      {/* ── Query form ── */}
      <div className="bg-white dark:bg-slate-800/70 rounded-2xl border border-slate-100 dark:border-slate-700/50 p-6">
        <h2 className="text-lg font-semibold text-slate-900 dark:text-white mb-5">Test Your Queries</h2>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="schema" className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">
              Select Schema
            </label>
            <select
              id="schema" value={selectedSchemaId}
              onChange={(e) => setSelectedSchemaId(e.target.value)}
              className={inputClass}
            >
              {schemas.length === 0
                ? <option value="">No schemas available</option>
                : schemas.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.name} ({s.db_type.toUpperCase()})
                    </option>
                  ))}
            </select>
          </div>

          <div>
            <label htmlFor="question" className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">
              Natural Language Question
            </label>
            <textarea
              id="question" value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="e.g., Show me all users who signed up in the last 30 days"
              rows={3}
              className="w-full px-4 py-2.5 border border-slate-200 dark:border-slate-600 rounded-xl bg-white dark:bg-slate-700/50 text-slate-900 dark:text-white placeholder:text-slate-400 dark:placeholder:text-slate-500 focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition resize-none text-[0.9375rem]"
            />
          </div>

          {/* Example prompts */}
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-sm text-slate-500 dark:text-slate-400">Try:</span>
            {exampleQuestions.map((ex, i) => (
              <button
                key={i} type="button" onClick={() => setQuestion(ex)}
                className="text-sm bg-slate-100 dark:bg-slate-700/50 text-slate-700 dark:text-slate-300 px-3 py-1 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors"
              >
                {ex}
              </button>
            ))}
          </div>

          {error && (
            <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800/50 text-red-700 dark:text-red-400 px-4 py-3 rounded-xl text-sm">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading || !selectedSchemaId || !question.trim()}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white py-2.5 px-4 rounded-xl font-semibold text-sm shadow-blue-sm disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? 'Generating SQL…' : 'Generate SQL'}
          </button>
        </form>
      </div>

      {/* ── Result ── */}
      {result && (
        <div className="bg-white dark:bg-slate-800/70 rounded-2xl border border-slate-100 dark:border-slate-700/50 p-6">
          <div className="flex items-center justify-between mb-5">
            <h3 className="text-lg font-semibold text-slate-900 dark:text-white">Generated SQL</h3>
            <div className="flex items-center gap-2">
              <span className="text-sm text-slate-500 dark:text-slate-400">Confidence:</span>
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                result.confidence_score >= 0.8
                  ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400'
                  : result.confidence_score >= 0.6
                  ? 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400'
                  : 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400'
              }`}>
                {(result.confidence_score * 100).toFixed(0)}%
              </span>
            </div>
          </div>

          <pre className="bg-slate-900 dark:bg-slate-950 text-slate-100 p-4 rounded-xl text-sm font-mono whitespace-pre-wrap overflow-x-auto mb-5 leading-relaxed border border-slate-800">
            {result.generated_sql}
          </pre>

          {result.warnings && result.warnings.length > 0 && (
            <div className="mb-5 p-4 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800/40 rounded-xl">
              <h4 className="text-sm font-semibold text-slate-900 dark:text-white mb-2">Warnings</h4>
              <ul className="text-sm text-slate-700 dark:text-slate-300 list-disc list-inside space-y-1">
                {result.warnings.map((w, i) => <li key={i}>{w}</li>)}
              </ul>
            </div>
          )}

          <div className="flex items-center justify-between pt-4 border-t border-slate-100 dark:border-slate-700/50">
            <span className="text-sm text-slate-600 dark:text-slate-400">Was this SQL query correct?</span>
            <div className="flex gap-2">
              <button
                onClick={() => handleFeedback(result.id, true)}
                className="px-4 py-1.5 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 rounded-lg hover:bg-green-200 dark:hover:bg-green-900/50 text-sm font-medium transition-colors"
              >
                Yes
              </button>
              <button
                onClick={() => handleFeedback(result.id, false)}
                className="px-4 py-1.5 bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400 rounded-lg hover:bg-red-200 dark:hover:bg-red-900/50 text-sm font-medium transition-colors"
              >
                No
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── Query history ── */}
      {history.length > 0 && (
        <div className="bg-white dark:bg-slate-800/70 rounded-2xl border border-slate-100 dark:border-slate-700/50 p-6">
          <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-5">Recent Queries</h3>
          <div className="space-y-3">
            {history.map((query) => (
              <div key={query.id} className="border border-slate-200 dark:border-slate-700/50 rounded-xl p-4">
                <div className="flex items-start justify-between gap-3 mb-2">
                  <p className="text-sm font-medium text-slate-900 dark:text-white">{query.natural_language_query}</p>
                  <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium flex-shrink-0 ${
                    query.confidence_score >= 0.8
                      ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400'
                      : query.confidence_score >= 0.6
                      ? 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400'
                      : 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400'
                  }`}>
                    {(query.confidence_score * 100).toFixed(0)}%
                  </span>
                </div>
                <pre className="text-xs font-mono text-slate-500 dark:text-slate-400 bg-slate-50 dark:bg-slate-700/30 p-3 rounded-lg overflow-x-auto">
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
