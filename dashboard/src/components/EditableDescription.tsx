'use client'

import { useState, useRef, useEffect, useCallback } from 'react'
import { Pencil, Check, X, Sparkles, User } from 'lucide-react'

interface EditableDescriptionProps {
  description?: string | null
  source?: 'ai' | 'user' | null
  onSave: (text: string) => Promise<void>
  placeholder?: string
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

  useEffect(() => {
    if (!editing) setDraft(description ?? '')
  }, [description, editing])

  useEffect(() => {
    if (editing && textareaRef.current) {
      const el = textareaRef.current
      el.focus()
      el.setSelectionRange(el.value.length, el.value.length)
      autoSize(el)
    }
  }, [editing])

  const autoSize = (el: HTMLTextAreaElement) => {
    el.style.height = 'auto'
    el.style.height = `${el.scrollHeight}px`
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Escape') cancel()
    else if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) save()
  }

  const save = useCallback(async () => {
    const trimmed = draft.trim()
    if (!trimmed) { setError('Description cannot be empty'); return }
    if (trimmed === (description ?? '').trim()) { setEditing(false); return }
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

  const cancel = () => { setDraft(description ?? ''); setError(''); setEditing(false) }

  // ── Source badge ──
  const SourceBadge = () => {
    if (!source) return null
    if (source === 'user') return (
      <span className="inline-flex items-center gap-1 text-xs px-1.5 py-0.5 rounded-md bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 font-medium flex-shrink-0">
        <User className="w-2.5 h-2.5" /> Edited
      </span>
    )
    return (
      <span className="inline-flex items-center gap-1 text-xs px-1.5 py-0.5 rounded-md bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-400 font-medium flex-shrink-0">
        <Sparkles className="w-2.5 h-2.5" /> AI
      </span>
    )
  }

  // ── Edit mode ──
  if (editing) {
    return (
      <div className={`space-y-2 ${className}`}>
        <textarea
          ref={textareaRef}
          value={draft}
          onChange={(e) => { setDraft(e.target.value); autoSize(e.target) }}
          onKeyDown={handleKeyDown}
          rows={compact ? 2 : 3}
          className="w-full px-3 py-2 border border-blue-400 dark:border-blue-500 rounded-lg text-sm text-slate-800 dark:text-slate-200 bg-white dark:bg-slate-700/60 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none transition"
          disabled={saving}
        />
        {error && <p className="text-xs text-red-600 dark:text-red-400">{error}</p>}
        <div className="flex items-center gap-2">
          <button
            onClick={save} disabled={saving}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-medium rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <Check className="w-3.5 h-3.5" />
            {saving ? 'Saving…' : 'Save'}
          </button>
          <button
            onClick={cancel} disabled={saving}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-white dark:bg-slate-700 border border-slate-200 dark:border-slate-600 text-slate-700 dark:text-slate-300 text-xs font-medium rounded-lg hover:bg-slate-50 dark:hover:bg-slate-600 disabled:opacity-50 transition-colors"
          >
            <X className="w-3.5 h-3.5" /> Cancel
          </button>
          <span className="text-xs text-slate-400 dark:text-slate-500 ml-1">
            {typeof navigator !== 'undefined' && navigator.platform?.includes('Mac') ? '⌘' : 'Ctrl'}+Enter to save · Esc to cancel
          </span>
        </div>
      </div>
    )
  }

  // ── View mode ──
  return (
    <div
      className={`group flex items-start gap-2 cursor-pointer ${className}`}
      onClick={() => setEditing(true)}
      title="Click to edit description"
    >
      <div className="flex-1 min-w-0">
        {description ? (
          <span className={`text-slate-700 dark:text-slate-300 ${compact ? 'text-sm' : 'text-base'}`}>
            {description}
          </span>
        ) : (
          <span className={`text-slate-400 dark:text-slate-500 italic ${compact ? 'text-sm' : 'text-base'}`}>
            {placeholder}
          </span>
        )}
      </div>
      <div className="flex items-center gap-1.5 flex-shrink-0 mt-0.5">
        <SourceBadge />
        <Pencil className="w-3.5 h-3.5 text-slate-300 dark:text-slate-600 group-hover:text-blue-500 dark:group-hover:text-blue-400 transition-colors" />
      </div>
    </div>
  )
}
