'use client'

import { useState, useRef, useEffect, useCallback } from 'react'
import { Pencil, Check, X, Sparkles, User } from 'lucide-react'

interface EditableDescriptionProps {
  /** Current description text (null/undefined = not yet enriched) */
  description?: string | null
  /** Who wrote it: 'ai', 'user', or null */
  source?: 'ai' | 'user' | null
  /** Called with the new text when the user saves */
  onSave: (text: string) => Promise<void>
  placeholder?: string
  /** Render as compact single-line (e.g. column cell) vs full block */
  compact?: boolean
  className?: string
}

export default function EditableDescription({
  description,
  source,
  onSave,
  placeholder = 'No description — click to add one',
  compact = false,
  className = '',
}: EditableDescriptionProps) {
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState(description ?? '')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  // Sync external description changes (e.g. after AI enrichment)
  useEffect(() => {
    if (!editing) setDraft(description ?? '')
  }, [description, editing])

  // Auto-focus and auto-size when entering edit mode
  useEffect(() => {
    if (editing && textareaRef.current) {
      const el = textareaRef.current
      el.focus()
      // Move cursor to end
      el.setSelectionRange(el.value.length, el.value.length)
      autoSize(el)
    }
  }, [editing])

  const autoSize = (el: HTMLTextAreaElement) => {
    el.style.height = 'auto'
    el.style.height = `${el.scrollHeight}px`
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Escape') {
      cancel()
    } else if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
      save()
    }
  }

  const save = useCallback(async () => {
    const trimmed = draft.trim()
    if (!trimmed) {
      setError('Description cannot be empty')
      return
    }
    if (trimmed === (description ?? '').trim()) {
      // No change — just close
      setEditing(false)
      return
    }

    setSaving(true)
    setError('')
    try {
      await onSave(trimmed)
      setEditing(false)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save')
    } finally {
      setSaving(false)
    }
  }, [draft, description, onSave])

  const cancel = () => {
    setDraft(description ?? '')
    setError('')
    setEditing(false)
  }

  // -----------------------------------------------------------------------
  // Source badge
  // -----------------------------------------------------------------------
  const SourceBadge = () => {
    if (!source) return null
    if (source === 'user') {
      return (
        <span className="inline-flex items-center gap-1 text-xs px-1.5 py-0.5 rounded bg-blue-100 text-blue-700 font-medium shrink-0">
          <User className="w-2.5 h-2.5" />
          Edited
        </span>
      )
    }
    return (
      <span className="inline-flex items-center gap-1 text-xs px-1.5 py-0.5 rounded bg-purple-100 text-purple-700 font-medium shrink-0">
        <Sparkles className="w-2.5 h-2.5" />
        AI
      </span>
    )
  }

  // -----------------------------------------------------------------------
  // Edit mode
  // -----------------------------------------------------------------------
  if (editing) {
    return (
      <div className={`space-y-2 ${className}`}>
        <textarea
          ref={textareaRef}
          value={draft}
          onChange={(e) => {
            setDraft(e.target.value)
            autoSize(e.target)
          }}
          onKeyDown={handleKeyDown}
          rows={compact ? 2 : 3}
          className="w-full px-3 py-2 border border-blue-400 rounded-lg text-sm text-gray-800 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
          disabled={saving}
        />
        {error && <p className="text-xs text-red-600">{error}</p>}
        <div className="flex items-center gap-2">
          <button
            onClick={save}
            disabled={saving}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-blue-600 text-white text-xs font-medium rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <Check className="w-3.5 h-3.5" />
            {saving ? 'Saving…' : 'Save'}
          </button>
          <button
            onClick={cancel}
            disabled={saving}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-white border border-gray-300 text-gray-700 text-xs font-medium rounded-md hover:bg-gray-50 disabled:opacity-50 transition-colors"
          >
            <X className="w-3.5 h-3.5" />
            Cancel
          </button>
          <span className="text-xs text-gray-400 ml-1">
            {navigator?.platform?.includes('Mac') ? '⌘' : 'Ctrl'}+Enter to save · Esc to cancel
          </span>
        </div>
      </div>
    )
  }

  // -----------------------------------------------------------------------
  // View mode
  // -----------------------------------------------------------------------
  return (
    <div
      className={`group flex items-start gap-2 cursor-pointer ${className}`}
      onClick={() => setEditing(true)}
      title="Click to edit description"
    >
      <div className="flex-1 min-w-0">
        {description ? (
          <span className={`text-gray-700 ${compact ? 'text-sm' : 'text-base'}`}>
            {description}
          </span>
        ) : (
          <span className={`text-gray-400 italic ${compact ? 'text-sm' : 'text-base'}`}>
            {placeholder}
          </span>
        )}
      </div>

      <div className="flex items-center gap-1.5 shrink-0 mt-0.5">
        <SourceBadge />
        <Pencil className="w-3.5 h-3.5 text-gray-300 group-hover:text-blue-500 transition-colors" />
      </div>
    </div>
  )
}