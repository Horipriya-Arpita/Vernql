'use client'

import { useEffect, useRef, useState, useCallback, Suspense } from 'react'
import { useSearchParams } from 'next/navigation'
import ChatWindow from '@/components/ChatWindow'
import { VernqlApiClient } from '@/lib/api-client'
import {
  getThemePreference,
  generateId,
  getStoredSessionId,
  setStoredSessionId,
  clearStoredSessionId,
} from '@/lib/utils'
import type {
  ChatMessage,
  SseNewResultPayload,
  WidgetConfig,
  ProxyVisualization,
} from '@/lib/types'

// ---------------------------------------------------------------------------
// useSearchParams() must be inside a Suspense boundary in Next.js App Router.
// Split into inner component + exported wrapper to satisfy that requirement.
// ---------------------------------------------------------------------------

function WidgetContent() {
  const searchParams = useSearchParams()

  const [config, setConfig] = useState<WidgetConfig | null>(null)
  const [apiClient, setApiClient] = useState<VernqlApiClient | null>(null)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [isSending, setIsSending] = useState(false)
  const [ready, setReady] = useState(false)

  // Direct mode only — session + SSE state
  const [sessionId, setSessionId] = useState<string | null>(null)
  const sseCleanupRef = useRef<(() => void) | null>(null)

  // Proxy mode only — map of pending postMessage promises keyed by messageId
  const pendingRef = useRef<
    Map<string, { resolve: (v: ProxyVisualization) => void; reject: (e: Error) => void }>
  >(new Map())

  // -------------------------------------------------------------------
  // Config + client init
  //
  // Mode detection:
  //   proxy  — proxyUrl param present in URL → initialize immediately
  //   direct — credentials arrive via 'vernql:init' postMessage from
  //             embed.js (never put in URL to avoid key exposure).
  //             Legacy fallback: apiKey+schemaId in URL still accepted
  //             for backward compatibility / standalone dev testing.
  // -------------------------------------------------------------------

  // Effect 1: non-sensitive URL params + proxy mode
  useEffect(() => {
    const proxyUrl    = searchParams.get('proxyUrl')
    const theme       = (searchParams.get('theme') as 'light' | 'dark' | 'auto') || 'auto'
    const title       = searchParams.get('title')       || undefined
    const placeholder = searchParams.get('placeholder') || undefined

    // Apply theme immediately regardless of mode
    const resolvedTheme = getThemePreference(theme)
    if (resolvedTheme === 'dark') {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }

    if (proxyUrl) {
      // Proxy mode — no secrets needed, initialize right away
      setConfig({ proxyUrl, apiUrl: 'https://api.vernql.com', theme, title, placeholder })
      setReady(true)
      return
    }

    // Legacy direct mode: apiKey/schemaId passed in URL (deprecated, kept for
    // backward compat and local dev).  When embed.js is used these params are
    // absent — credentials arrive via postMessage (Effect 2 below).
    const legacyApiKey   = searchParams.get('apiKey')
    const legacySchemaId = searchParams.get('schemaId')
    const legacyApiUrl   = searchParams.get('apiUrl') || 'https://api.vernql.com'
    if (legacyApiKey && legacySchemaId) {
      setConfig({ apiKey: legacyApiKey, schemaId: legacySchemaId, apiUrl: legacyApiUrl, theme, title, placeholder })
      setApiClient(new VernqlApiClient(legacyApiUrl, legacyApiKey, legacySchemaId))
      setReady(true)
      return
    }

    // Secure direct mode: stay in loading state until vernql:init arrives
    // (Effect 2 will call setReady once credentials are received)
  }, [searchParams])

  // Effect 2: Secure direct mode — receive credentials from embed.js via postMessage.
  // Keeping this in a separate effect ensures the listener is registered even before
  // searchParams resolves, so the 'load' event from the parent frame is never missed.
  useEffect(() => {
    function handleInitMessage(event: MessageEvent) {
      if (event.data?.type !== 'vernql:init') return
      const { apiKey, schemaId, apiUrl = 'https://api.vernql.com' } = event.data as {
        apiKey?: string; schemaId?: string; apiUrl?: string
      }
      if (!apiKey || !schemaId) return

      // Read non-sensitive display params from the current URL
      const params      = new URLSearchParams(window.location.search)
      const theme       = (params.get('theme') as 'light' | 'dark' | 'auto') || 'auto'
      const title       = params.get('title')       || undefined
      const placeholder = params.get('placeholder') || undefined

      setConfig({ apiKey, schemaId, apiUrl, theme, title, placeholder })
      setApiClient(new VernqlApiClient(apiUrl, apiKey, schemaId))
      setReady(true)
    }

    window.addEventListener('message', handleInitMessage)
    return () => window.removeEventListener('message', handleInitMessage)
  }, []) // register once — no deps needed

  // -------------------------------------------------------------------
  // Proxy mode — listen for postMessage replies from the host page.
  // We accept messages from any origin here because the widget can be
  // embedded in any host page; we use the messageId to match requests
  // instead of relying on origin (the messageId is a secret the iframe
  // generated — no external party can guess it).
  // -------------------------------------------------------------------
  useEffect(() => {
    const handler = (event: MessageEvent) => {
      if (event.data?.type === 'vernql:result') {
        const pending = pendingRef.current.get(event.data.messageId)
        if (pending) {
          pending.resolve(event.data.visualization as ProxyVisualization)
          pendingRef.current.delete(event.data.messageId)
        }
      } else if (event.data?.type === 'vernql:error') {
        const pending = pendingRef.current.get(event.data.messageId)
        if (pending) {
          pending.reject(new Error(event.data.error || 'Query failed'))
          pendingRef.current.delete(event.data.messageId)
        }
      }
    }
    window.addEventListener('message', handler)
    return () => window.removeEventListener('message', handler)
  }, [])

  // -------------------------------------------------------------------
  // Direct mode — session creation + SSE stream setup
  // Only runs when an apiClient is available (i.e. not proxy mode).
  // -------------------------------------------------------------------
  useEffect(() => {
    if (!apiClient || !config) return

    let cancelled = false

    const setup = async () => {
      try {
        let sid: string | null = getStoredSessionId(config.apiKey!, config.schemaId!)

        if (sid) {
          const valid = await apiClient.sessionExists(sid)
          if (!valid) {
            clearStoredSessionId(config.apiKey!, config.schemaId!)
            sid = null
          }
        }

        if (!sid) {
          sid = await apiClient.createSession()
          setStoredSessionId(config.apiKey!, config.schemaId!, sid)
        }

        if (cancelled) return
        setSessionId(sid)

        const handleSseEvent = (payload: SseNewResultPayload) => {
          setMessages((prev) => {
            const idx = prev.findIndex((m) => m.awaitingViz === true)
            if (idx === -1) return prev
            const updated = [...prev]
            updated[idx] = { ...updated[idx], awaitingViz: false, vizResult: payload }
            return updated
          })
        }

        const cleanup = apiClient.openSseStream(sid, handleSseEvent, (err) => {
          console.warn('[Vernql SSE]', err.message)
        })

        sseCleanupRef.current = cleanup
      } catch (err) {
        console.warn('[Vernql] Could not create session:', err)
      }
    }

    setup()

    return () => {
      cancelled = true
      sseCleanupRef.current?.()
      sseCleanupRef.current = null
    }
  }, [apiClient, config])

  // -------------------------------------------------------------------
  // Send a natural language query
  // Two paths: proxy mode (postMessage) vs direct mode (Vernql API)
  // -------------------------------------------------------------------
  const handleSendMessage = useCallback(
    async (query: string) => {
      if (!config) return

      const userMessage: ChatMessage = {
        id: generateId(),
        type: 'user',
        content: query,
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, userMessage])
      setIsSending(true)

      try {
        if (config.proxyUrl) {
          // ----------------------------------------------------------
          // Proxy mode: ask the host page to run the query
          // ----------------------------------------------------------
          const messageId = generateId()

          const visualization = await new Promise<ProxyVisualization>((resolve, reject) => {
            pendingRef.current.set(messageId, {
              resolve: (v) => {
                if (!v || !v.chart_type) {
                  reject(new Error('Invalid response from host page'))
                  return
                }
                resolve(v)
              },
              reject,
            })

            // Ask the parent (host page, e.g. ShopMetrics) to run the query.
            // embed.js running in the host page listens for this message,
            // calls /api/vernql, and posts the result back.
            window.parent.postMessage(
              { type: 'vernql:query', question: query, messageId },
              '*'
            )

            // Safety timeout — reject if host page doesn't respond in 30s
            setTimeout(() => {
              if (pendingRef.current.has(messageId)) {
                pendingRef.current.delete(messageId)
                reject(new Error('Query timed out. Please try again.'))
              }
            }, 30_000)
          })

          const assistantMessage: ChatMessage = {
            id: generateId(),
            type: 'assistant',
            content: '',
            // Map the proxy visualization directly to SseNewResultPayload shape
            vizResult: {
              result_id:          messageId,
              chart_type:         visualization.chart_type,
              ai_insight:         visualization.ai_insight ?? null,
              visualization_data: visualization.visualization_data,
            },
            timestamp: new Date(),
          }
          setMessages((prev) => [...prev, assistantMessage])
        } else {
          // ----------------------------------------------------------
          // Direct mode: call Vernql API, wait for SSE viz result
          // ----------------------------------------------------------
          const result = await apiClient!.generateSQL(query, sessionId ?? undefined)
          const assistantMessage: ChatMessage = {
            id: generateId(),
            type: 'assistant',
            content: '',
            sqlResult: result,
            awaitingViz: sessionId !== null,
            timestamp: new Date(),
          }
          setMessages((prev) => [...prev, assistantMessage])
        }
      } catch (error) {
        const errorMessage: ChatMessage = {
          id: generateId(),
          type: 'error',
          content: error instanceof Error ? error.message : 'An unexpected error occurred',
          timestamp: new Date(),
        }
        setMessages((prev) => [...prev, errorMessage])
      } finally {
        setIsSending(false)
      }
    },
    [config, apiClient, sessionId]
  )

  // Still waiting for searchParams — neutral loading state
  if (!ready) {
    return (
      <div className="flex items-center justify-center h-full bg-gray-50 dark:bg-gray-900">
        <div className="w-6 h-6 rounded-full border-2 border-primary-500 border-t-transparent animate-spin" />
      </div>
    )
  }

  if (!config) {
    return (
      <div className="flex items-center justify-center h-full bg-gray-50 dark:bg-gray-900">
        <div className="text-center px-4">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-full bg-red-100 dark:bg-red-900/30 mb-4">
            <svg className="w-7 h-7 text-red-600 dark:text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <h2 className="text-base font-semibold text-gray-900 dark:text-gray-100 mb-1">
            Configuration Error
          </h2>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Provide either a{' '}
            <code className="bg-gray-100 dark:bg-gray-700 px-1 rounded">proxyUrl</code>
            {' '}(proxy mode) or both{' '}
            <code className="bg-gray-100 dark:bg-gray-700 px-1 rounded">apiKey</code> and{' '}
            <code className="bg-gray-100 dark:bg-gray-700 px-1 rounded">schemaId</code>
            {' '}(direct mode).
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="w-full h-full">
      <ChatWindow
        messages={messages}
        onSendMessage={handleSendMessage}
        isLoading={isSending}
        title={config.title}
        placeholder={config.placeholder}
      />
    </div>
  )
}

export default function WidgetPage() {
  return (
    <Suspense
      fallback={
        <div className="flex items-center justify-center h-full bg-gray-50 dark:bg-gray-900">
          <div className="w-6 h-6 rounded-full border-2 border-primary-500 border-t-transparent animate-spin" />
        </div>
      }
    >
      <WidgetContent />
    </Suspense>
  )
}
