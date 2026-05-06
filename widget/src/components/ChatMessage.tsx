'use client'

import { User, Bot, AlertCircle } from 'lucide-react'
import SQLResult from './SQLResult'
import VisualizationRenderer from './charts/VisualizationRenderer'
import type { ChatMessage as ChatMessageType } from '@/lib/types'

interface ChatMessageProps {
  message: ChatMessageType
}

export default function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.type === 'user'
  const isError = message.type === 'error'

  return (
    <div className={`flex gap-3 ${isUser ? 'justify-end' : 'justify-start'}`}>
      {!isUser && (
        <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
          isError
            ? 'bg-red-100 dark:bg-red-900/30'
            : 'bg-primary-100 dark:bg-primary-900/30'
        }`}>
          {isError ? (
            <AlertCircle className="h-4 w-4 text-red-600 dark:text-red-400" />
          ) : (
            <Bot className="h-4 w-4 text-primary-600 dark:text-primary-400" />
          )}
        </div>
      )}

      <div className={`flex-1 max-w-[85%] ${isUser ? 'text-right' : 'text-left'}`}>
        {isUser ? (
          <div className="inline-block rounded-lg bg-primary-600 px-4 py-2 text-sm text-white">
            {message.content}
          </div>
        ) : isError ? (
          <div className="rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 px-4 py-3">
            <p className="text-sm text-red-800 dark:text-red-200">{message.content}</p>
          </div>
        ) : (
          <div className="rounded-lg bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 p-4 shadow-sm">
            {message.sqlResult ? (
              // Direct mode — show generated SQL + awaiting/viz result
              <SQLResult
                result={message.sqlResult}
                awaitingViz={message.awaitingViz}
                vizResult={message.vizResult}
              />
            ) : message.vizResult ? (
              // Proxy mode — host page executed the query; show viz directly
              <VisualizationRenderer
                visualizationData={message.vizResult.visualization_data}
                aiInsight={message.vizResult.ai_insight}
              />
            ) : (
              <p className="text-sm text-gray-700 dark:text-gray-300">{message.content}</p>
            )}
          </div>
        )}

        <div className="mt-1 text-xs text-gray-400 dark:text-gray-500">
          {message.timestamp.toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit',
          })}
        </div>
      </div>

      {isUser && (
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gray-200 dark:bg-gray-700 flex items-center justify-center">
          <User className="h-4 w-4 text-gray-600 dark:text-gray-300" />
        </div>
      )}
    </div>
  )
}
