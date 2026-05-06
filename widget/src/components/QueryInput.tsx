'use client'

import { useState, FormEvent, KeyboardEvent } from 'react'
import { Send, Loader2 } from 'lucide-react'

interface QueryInputProps {
  onSubmit: (query: string) => void
  isLoading: boolean
  placeholder?: string
}

export default function QueryInput({ onSubmit, isLoading, placeholder }: QueryInputProps) {
  const [query, setQuery] = useState('')

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    if (query.trim() && !isLoading) {
      onSubmit(query.trim())
      setQuery('')
    }
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="relative">
      <textarea
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder || 'Ask a question about your data...'}
        disabled={isLoading}
        rows={1}
        className="w-full resize-none rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-4 py-3 pr-12 text-sm text-gray-900 dark:text-gray-100 placeholder-gray-500 dark:placeholder-gray-400 focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500/20 disabled:opacity-50 disabled:cursor-not-allowed"
        style={{
          minHeight: '3rem',
          maxHeight: '7.5rem',
        }}
      />
      <button
        type="submit"
        disabled={!query.trim() || isLoading}
        className="absolute right-2 bottom-2 rounded-lg bg-primary-600 p-2 text-white hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      >
        {isLoading ? (
          <Loader2 className="h-4 w-4 animate-spin" />
        ) : (
          <Send className="h-4 w-4" />
        )}
      </button>
    </form>
  )
}
