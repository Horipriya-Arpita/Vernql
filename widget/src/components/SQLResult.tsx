'use client'

import { useState } from 'react'
import { Copy, Check, AlertTriangle, Database, Loader2 } from 'lucide-react'
import { copyToClipboard, formatConfidence } from '@/lib/utils'
import VisualizationRenderer from './charts/VisualizationRenderer'
import type { QueryResponse, SseNewResultPayload } from '@/lib/types'

interface SQLResultProps {
  result: QueryResponse
  awaitingViz?: boolean
  vizResult?: SseNewResultPayload
}

export default function SQLResult({ result, awaitingViz, vizResult }: SQLResultProps) {
  const [copied, setCopied] = useState(false)

  const handleCopy = async () => {
    const success = await copyToClipboard(result.generated_sql)
    if (success) {
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  const confidenceColor =
    result.confidence_score >= 0.8
      ? 'text-green-600 dark:text-green-400'
      : result.confidence_score >= 0.6
      ? 'text-yellow-600 dark:text-yellow-400'
      : 'text-red-600 dark:text-red-400'

  return (
    <div className="space-y-3">
      {/* Header with confidence — wraps on narrow embeds */}
      <div className="flex flex-wrap items-center justify-between gap-y-1.5 gap-x-2">
        <div className="flex items-center gap-2">
          <Database className="h-4 w-4 flex-shrink-0 text-primary-600 dark:text-primary-400" />
          <span className="text-sm font-medium text-gray-900 dark:text-gray-100">
            Generated SQL
          </span>
        </div>
        <div className="flex items-center gap-2">
          <span className={`text-xs font-medium ${confidenceColor}`}>
            {formatConfidence(result.confidence_score)} confidence
          </span>
          <button
            onClick={handleCopy}
            className="flex items-center gap-1.5 rounded-md px-2 py-1 text-xs font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
          >
            {copied ? (
              <>
                <Check className="h-3 w-3" />
                Copied
              </>
            ) : (
              <>
                <Copy className="h-3 w-3" />
                Copy
              </>
            )}
          </button>
        </div>
      </div>

      {/* SQL Code */}
      <div className="relative">
        <pre className="rounded-lg bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 p-4 overflow-x-auto">
          <code className="text-xs text-gray-800 dark:text-gray-200 font-mono">
            {result.generated_sql}
          </code>
        </pre>
      </div>

      {/* Warnings */}
      {result.warnings && result.warnings.length > 0 && (
        <div className="rounded-lg bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 p-3">
          <div className="flex gap-2">
            <AlertTriangle className="h-4 w-4 text-yellow-600 dark:text-yellow-400 flex-shrink-0 mt-0.5" />
            <div className="space-y-1">
              <p className="text-xs font-medium text-yellow-900 dark:text-yellow-200">
                Warnings:
              </p>
              <ul className="text-xs text-yellow-800 dark:text-yellow-300 space-y-0.5 list-disc list-inside">
                {result.warnings.map((warning, idx) => (
                  <li key={idx}>{warning}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* Metadata — wraps on narrow embeds */}
      <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-gray-500 dark:text-gray-400">
        <span>Model: {result.ai_model}</span>
        <span aria-hidden>•</span>
        <span>Provider: {result.ai_provider}</span>
      </div>

      {/* Awaiting visualization — shown while client backend runs the query */}
      {awaitingViz && !vizResult && (
        <div className="flex items-center gap-2 rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900 px-3 py-2.5">
          <Loader2 className="h-3.5 w-3.5 flex-shrink-0 text-primary-500 animate-spin" />
          <span className="text-xs text-gray-500 dark:text-gray-400">
            Waiting for query results from your database…
          </span>
        </div>
      )}

      {/* Visualization result — rendered once the SSE new_result event fires */}
      {vizResult && (
        <VisualizationRenderer
          visualizationData={vizResult.visualization_data}
          aiInsight={vizResult.ai_insight}
        />
      )}
    </div>
  )
}
