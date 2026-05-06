'use client'

import { useEffect, useRef } from 'react'
import { Sparkles } from 'lucide-react'
import ChatMessage from './ChatMessage'
import QueryInput from './QueryInput'
import type { ChatMessage as ChatMessageType } from '@/lib/types'

interface ChatWindowProps {
  messages: ChatMessageType[]
  onSendMessage: (query: string) => void
  isLoading: boolean
  title?: string
  placeholder?: string
}

export default function ChatWindow({
  messages,
  onSendMessage,
  isLoading,
  title,
  placeholder,
}: ChatWindowProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  return (
    <div className="flex flex-col h-full bg-gray-50 dark:bg-gray-900">
      {/* Header — compact padding so it doesn't dominate narrow/short embeds */}
      <div className="flex-shrink-0 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-4 py-3">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 flex-shrink-0 rounded-lg bg-gradient-to-br from-primary-500 to-primary-600 flex items-center justify-center">
            <Sparkles className="h-3.5 w-3.5 text-white" />
          </div>
          <div className="min-w-0">
            <h2 className="text-sm font-semibold text-gray-900 dark:text-gray-100 truncate">
              {title || 'Vernql Assistant'}
            </h2>
            <p className="text-xs text-gray-500 dark:text-gray-400 truncate">
              Ask questions in natural language
            </p>
          </div>
        </div>
      </div>

      {/* Messages — min-h-0 prevents flex child from overflowing */}
      <div className="flex-1 min-h-0 overflow-y-auto px-4 py-4 space-y-4">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center px-2">
            <div className="w-12 h-12 rounded-full bg-primary-100 dark:bg-primary-900/30 flex items-center justify-center mb-3">
              <Sparkles className="h-6 w-6 text-primary-600 dark:text-primary-400" />
            </div>
            <h3 className="text-base font-medium text-gray-900 dark:text-gray-100 mb-1">
              Welcome to Vernql
            </h3>
            <p className="text-xs text-gray-500 dark:text-gray-400 max-w-[18rem]">
              Ask questions about your data in plain English, and I'll generate SQL queries for you.
            </p>
            <div className="mt-4 space-y-2 w-full max-w-xs">
              <p className="text-xs font-medium text-gray-700 dark:text-gray-300 text-left">
                Try asking:
              </p>
              <div className="space-y-1.5">
                {[
                  'Show me users who signed up this week',
                  'What are the top 10 products by revenue?',
                  'Find customers with more than 5 orders',
                ].map((example, idx) => (
                  <button
                    key={idx}
                    onClick={() => onSendMessage(example)}
                    disabled={isLoading}
                    className="w-full text-left px-3 py-2 text-xs rounded-lg bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 hover:border-primary-500 dark:hover:border-primary-500 transition-colors text-gray-700 dark:text-gray-300 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {example}
                  </button>
                ))}
              </div>
            </div>
          </div>
        ) : (
          <>
            {messages.map((message) => (
              <ChatMessage key={message.id} message={message} />
            ))}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* Input */}
      <div className="flex-shrink-0 bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 px-4 py-3">
        <QueryInput
          onSubmit={onSendMessage}
          isLoading={isLoading}
          placeholder={placeholder}
        />
      </div>
    </div>
  )
}
