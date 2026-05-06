'use client'

import { useAuth } from '@/contexts/AuthContext'
import ApiKeyInput from '@/components/ApiKeyInput'
import DashboardLayout from '@/components/DashboardLayout'
import { useState } from 'react'
import { apiClient } from '@/lib/api-client'
import type { Schema } from '@/lib/types'
import useSWR from 'swr'
import toast from 'react-hot-toast'
import Link from 'next/link'
import {
  Code, Copy, Check, Database, Globe, ArrowRight,
  AlertTriangle, CheckCircle2, ExternalLink, Zap,
  MessageSquare, Key, ChevronDown, ChevronRight,
} from 'lucide-react'

// ─── Per-framework widget snippets ───────────────────────────────────────────

function getWidgetSnippets(schemaId: string) {
  const sid = schemaId || 'YOUR_SCHEMA_ID'
  return {
    html: `<!-- Place this just before the closing </body> tag -->
<script src="https://cdn.vernql.com/embed.js"></script>
<script>
  Vernql.init({
    apiKey:    'YOUR_API_KEY',
    schemaId:  '${sid}',
    apiUrl:    'https://api.vernql.com',
    theme:     'auto',           // 'light' | 'dark' | 'auto'
    position:  'bottom-right',   // 'bottom-right' | 'bottom-left'
    width:     '400px',          // optional
    height:    '600px',          // optional
    title:     'Ask your data',  // optional
  })
</script>`,

    nextjs: `// 1. Create components/VernqlWidget.tsx
'use client'
import { useEffect } from 'react'

declare global {
  interface Window {
    Vernql?: {
      init: (config: object) => void
      destroy: () => void
      open: () => void
      close: () => void
    }
  }
}

export default function VernqlWidget() {
  useEffect(() => {
    const script = document.createElement('script')
    script.src = 'https://cdn.vernql.com/embed.js'
    script.async = true
    script.onload = () => {
      window.Vernql?.init({
        apiKey:   process.env.NEXT_PUBLIC_VERNQL_API_KEY!,
        schemaId: '${sid}',
        apiUrl:   process.env.NEXT_PUBLIC_VERNQL_API_URL ?? 'https://api.vernql.com',
        theme:    'auto',
        position: 'bottom-right',
      })
    }
    document.body.appendChild(script)
    return () => {
      window.Vernql?.destroy()
      if (document.body.contains(script)) document.body.removeChild(script)
    }
  }, [])
  return null
}

// 2. Add to app/layout.tsx
// import VernqlWidget from '@/components/VernqlWidget'
// ...
// <body>
//   {children}
//   <VernqlWidget />   ← add this line
// </body>

// 3. Add to .env.local
// NEXT_PUBLIC_VERNQL_API_KEY=your_api_key_here
// NEXT_PUBLIC_VERNQL_API_URL=https://api.vernql.com`,

    react: `// 1. Create src/components/VernqlWidget.jsx
import { useEffect } from 'react'

export default function VernqlWidget() {
  useEffect(() => {
    const script = document.createElement('script')
    script.src = 'https://cdn.vernql.com/embed.js'
    script.async = true
    script.onload = () => {
      window.Vernql?.init({
        apiKey:   import.meta.env.VITE_VERNQL_API_KEY,
        schemaId: '${sid}',
        apiUrl:   import.meta.env.VITE_VERNQL_API_URL ?? 'https://api.vernql.com',
        theme:    'auto',
        position: 'bottom-right',
      })
    }
    document.body.appendChild(script)
    return () => {
      window.Vernql?.destroy()
      if (document.body.contains(script)) document.body.removeChild(script)
    }
  }, [])
  return null
}

// 2. Add to src/App.jsx
// import VernqlWidget from './components/VernqlWidget'
// function App() {
//   return (
//     <>
//       <YourApp />
//       <VernqlWidget />   ← add this line
//     </>
//   )
// }

// 3. Add to .env
// VITE_VERNQL_API_KEY=your_api_key_here`,

    vue: `<!-- 1. Create src/components/VernqlWidget.vue -->
<template><div /></template>

<script>
export default {
  name: 'VernqlWidget',
  mounted() {
    const script = document.createElement('script')
    script.src = 'https://cdn.vernql.com/embed.js'
    script.async = true
    script.onload = () => {
      window.Vernql?.init({
        apiKey:   import.meta.env.VITE_VERNQL_API_KEY,
        schemaId: '${sid}',
        apiUrl:   import.meta.env.VITE_VERNQL_API_URL ?? 'https://api.vernql.com',
        theme:    'auto',
        position: 'bottom-right',
      })
    }
    document.body.appendChild(script)
  },
  beforeUnmount() {
    window.Vernql?.destroy()
  },
}
</script>

<!-- 2. Add to src/App.vue -->
<!-- <VernqlWidget /> at the bottom of your <template> -->

<!-- 3. .env -->
<!-- VITE_VERNQL_API_KEY=your_api_key_here -->`,

    wordpress: `<?php
// Add to your theme's functions.php

function vernql_add_widget() {
    $api_key = get_option('vernql_api_key', '');
    if (empty($api_key)) return;
    ?>
    <script src="https://cdn.vernql.com/embed.js"></script>
    <script>
      Vernql.init({
        apiKey:   '<?php echo esc_js($api_key); ?>',
        schemaId: '${sid}',
        apiUrl:   'https://api.vernql.com',
        theme:    'auto',
        position: 'bottom-right',
      })
    </script>
    <?php
}
add_action('wp_footer', 'vernql_add_widget');

// Store your key via WP admin or:
// update_option('vernql_api_key', 'your_api_key_here');`,
  }
}

// ─── Per-language API snippets ────────────────────────────────────────────────

function getApiSnippets(schemaId: string) {
  const sid = schemaId || 'YOUR_SCHEMA_ID'
  return {
    nextjs: `// app/api/ask/route.ts
import { NextRequest, NextResponse } from 'next/server'

export async function POST(req: NextRequest) {
  const { question } = await req.json()

  // Step 1 — Ask Vernql to generate SQL
  const sqlRes = await fetch(\`\${process.env.VERNQL_API_URL}/v1/queries\`, {
    method: 'POST',
    headers: {
      'X-API-Key': process.env.VERNQL_API_KEY!,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      schema_id: '${sid}',
      query: question,
    }),
  })

  if (!sqlRes.ok) {
    return NextResponse.json({ error: 'SQL generation failed' }, { status: sqlRes.status })
  }

  const { id: queryId, generated_sql } = await sqlRes.json()

  // Step 2 — Run the SQL on YOUR database (you control this)
  // const rows = await db.query(generated_sql)

  // Step 3 — Ask Vernql to generate a visualisation (optional)
  const vizRes = await fetch(\`\${process.env.VERNQL_API_URL}/v1/visualizations/display\`, {
    method: 'POST',
    headers: {
      'X-API-Key': process.env.VERNQL_API_KEY!,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      query_id: queryId,
      results: [], // rows from step 2
      generate_insight: true,
    }),
  })

  return NextResponse.json(await vizRes.json())
}

// .env.local
// VERNQL_API_KEY=your_api_key_here
// VERNQL_API_URL=https://api.vernql.com`,

    python: `# requirements.txt: httpx fastapi uvicorn

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os

app = FastAPI()

VERNQL_API_KEY = os.getenv("VERNQL_API_KEY")
VERNQL_API_URL = os.getenv("VERNQL_API_URL", "https://api.vernql.com")

class AskRequest(BaseModel):
    question: str

@app.post("/ask")
async def ask(body: AskRequest):
    headers = {"X-API-Key": VERNQL_API_KEY}

    # Step 1 — Generate SQL
    async with httpx.AsyncClient() as client:
        sql_res = await client.post(
            f"{VERNQL_API_URL}/v1/queries",
            headers=headers,
            json={"schema_id": "${sid}", "query": body.question},
            timeout=30,
        )
        sql_res.raise_for_status()
        data = sql_res.json()

    query_id   = data["id"]
    sql        = data["generated_sql"]

    # Step 2 — Run on your database (you control this)
    # rows = your_db.execute(sql).fetchall()

    # Step 3 — Get visualisation (optional)
    async with httpx.AsyncClient() as client:
        viz_res = await client.post(
            f"{VERNQL_API_URL}/v1/visualizations/display",
            headers=headers,
            json={"query_id": query_id, "results": [], "generate_insight": True},
            timeout=30,
        )
        return viz_res.json()

# .env
# VERNQL_API_KEY=your_api_key_here`,

    curl: `# Step 1 — Generate SQL
curl -X POST https://api.vernql.com/v1/queries \\
  -H "X-API-Key: YOUR_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{
    "schema_id": "${sid}",
    "query": "Show me the top 10 customers by revenue"
  }'

# Response:
# {
#   "id": "query_abc123",
#   "generated_sql": "SELECT customer_name, SUM(revenue) ...",
#   "confidence_score": 0.92
# }

# Step 2 — Run the SQL on YOUR database (you control this)

# Step 3 — Get a visualisation (optional, pass results from step 2)
curl -X POST https://api.vernql.com/v1/visualizations/display \\
  -H "X-API-Key: YOUR_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{
    "query_id": "query_abc123",
    "results": [
      {"customer_name": "Acme Corp", "revenue": 98000},
      {"customer_name": "Globex",    "revenue": 74500}
    ],
    "generate_insight": true
  }'`,
  }
}

// ─── Config options table data ────────────────────────────────────────────────

const WIDGET_CONFIG_OPTIONS = [
  { name: 'apiKey',    type: 'string',                          required: true,  desc: 'Your Vernql API key' },
  { name: 'schemaId',  type: 'string',                          required: true,  desc: 'The schema ID to query against' },
  { name: 'apiUrl',    type: 'string',                          required: false, desc: 'Vernql API endpoint (default: https://api.vernql.com)' },
  { name: 'theme',     type: "'light' | 'dark' | 'auto'",       required: false, desc: "Widget colour theme (default: 'auto' follows OS setting)" },
  { name: 'position',  type: "'bottom-right' | 'bottom-left'",  required: false, desc: "Floating button position (default: 'bottom-right')" },
  { name: 'width',     type: 'string',                          required: false, desc: "Panel width, any CSS value (default: '400px')" },
  { name: 'height',    type: 'string',                          required: false, desc: "Panel height, any CSS value (default: '600px')" },
  { name: 'title',     type: 'string',                          required: false, desc: "Custom header title (default: 'Vernql Assistant')" },
  { name: 'placeholder', type: 'string',                        required: false, desc: "Input placeholder text" },
]

const TROUBLESHOOTING = [
  {
    q: 'Widget button does not appear',
    a: "Check the browser console for errors. The most common causes are: (1) embed.js URL is unreachable, (2) Vernql.init() was called before the script loaded — make sure init() is inside script.onload, (3) a z-index conflict with another element on your page.",
  },
  {
    q: 'Widget opens but shows "Missing required parameters"',
    a: 'Both apiKey and schemaId must be passed to Vernql.init(). Check that your environment variables are loaded (NEXT_PUBLIC_ prefix for Next.js, VITE_ prefix for Vite).',
  },
  {
    q: 'Network error / "Failed to fetch"',
    a: 'Verify apiUrl points to your running Vernql backend. If self-hosting, ensure CORS is configured to allow the domain where the widget is embedded. Check the Network tab in DevTools for the failing request.',
  },
  {
    q: 'Widget appears behind other elements',
    a: 'The widget uses z-index: 999998 for the panel and 999999 for the button. If your app has modals or headers with higher z-indexes, set a custom z-index by overriding #vernql-widget-container and #vernql-widget-button in your CSS.',
  },
  {
    q: 'Calling Vernql.init() twice throws a warning',
    a: 'The embed script prevents double-initialization. Call Vernql.destroy() first if you need to reinitialise with different config (e.g. after a user logs in with a different schema).',
  },
]

// ─── Helper components ────────────────────────────────────────────────────────

type Framework = 'html' | 'nextjs' | 'react' | 'vue' | 'wordpress'
type ApiLang = 'nextjs' | 'python' | 'curl'

const WIDGET_TABS: { id: Framework; label: string }[] = [
  { id: 'html',      label: 'HTML / Any site' },
  { id: 'nextjs',    label: 'Next.js' },
  { id: 'react',     label: 'React (Vite)' },
  { id: 'vue',       label: 'Vue.js' },
  { id: 'wordpress', label: 'WordPress' },
]

const API_TABS: { id: ApiLang; label: string }[] = [
  { id: 'nextjs',  label: 'Next.js' },
  { id: 'python',  label: 'Python' },
  { id: 'curl',    label: 'cURL' },
]

function CodeBlock({ code, id, copiedId, onCopy }: {
  code: string
  id: string
  copiedId: string | null
  onCopy: (code: string, id: string) => void
}) {
  return (
    <div className="relative">
      <pre className="bg-gray-900 text-gray-100 rounded-lg p-4 overflow-x-auto text-xs font-mono leading-relaxed whitespace-pre">
        <code>{code}</code>
      </pre>
      <button
        onClick={() => onCopy(code, id)}
        className="absolute top-3 right-3 flex items-center gap-1.5 bg-gray-700 hover:bg-gray-600 text-gray-200 text-xs px-2.5 py-1.5 rounded-md transition-colors"
      >
        {copiedId === id ? <><Check className="w-3.5 h-3.5" />Copied</> : <><Copy className="w-3.5 h-3.5" />Copy</>}
      </button>
    </div>
  )
}

function StepBadge({ n, color = 'blue' }: { n: number; color?: string }) {
  const colors: Record<string, string> = {
    blue:   'bg-blue-600 text-white',
    green:  'bg-green-600 text-white',
    purple: 'bg-purple-600 text-white',
  }
  return (
    <span className={`inline-flex items-center justify-center w-7 h-7 rounded-full text-sm font-bold flex-shrink-0 ${colors[color]}`}>
      {n}
    </span>
  )
}

// ─── Main page ────────────────────────────────────────────────────────────────

export default function IntegrationsPage() {
  const { isAuthenticated } = useAuth()
  const [path, setPath]       = useState<'widget' | 'api'>('widget')
  const [wTab, setWTab]       = useState<Framework>('html')
  const [aTab, setATab]       = useState<ApiLang>('nextjs')
  const [schema, setSchema]   = useState('')
  const [copied, setCopied]   = useState<string | null>(null)
  const [openFaq, setOpenFaq] = useState<number | null>(null)

  const { data: schemasData } = useSWR(
    isAuthenticated ? 'schemas' : null,
    () => apiClient.listSchemas(true),
  )
  const schemas: Schema[] = schemasData?.schemas ?? []

  const handleCopy = async (code: string, id: string) => {
    try {
      await navigator.clipboard.writeText(code)
      setCopied(id)
      toast.success('Copied to clipboard')
      setTimeout(() => setCopied(null), 2000)
    } catch {
      toast.error('Could not copy')
    }
  }

  if (!isAuthenticated) return <ApiKeyInput />

  const widgetSnippets = getWidgetSnippets(schema)
  const apiSnippets    = getApiSnippets(schema)

  const hasSchema   = Boolean(schema)
  const schemaName  = schemas.find(s => s.id === schema)?.name ?? ''

  return (
    <DashboardLayout>
      <div className="max-w-4xl mx-auto px-4 py-10 space-y-10">

        {/* ── Page header ───────────────────────────────────────────────── */}
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Integration Docs</h1>
          <p className="mt-1 text-gray-500 dark:text-gray-400">
            Everything Sarah (or any developer) needs to add Vernql to their project in under 5 minutes.
          </p>
        </div>

        {/* ── Path selector ─────────────────────────────────────────────── */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <button
            onClick={() => setPath('widget')}
            className={`flex items-start gap-4 rounded-xl border-2 p-5 text-left transition-all ${
              path === 'widget'
                ? 'border-blue-600 bg-blue-50 dark:bg-blue-900/20'
                : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
            }`}
          >
            <MessageSquare className={`w-8 h-8 flex-shrink-0 mt-0.5 ${path === 'widget' ? 'text-blue-600' : 'text-gray-400'}`} />
            <div>
              <div className="flex items-center gap-2">
                <span className="font-semibold text-gray-900 dark:text-white">Embed Widget</span>
                <span className="text-xs bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400 px-2 py-0.5 rounded-full font-medium">Recommended</span>
              </div>
              <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                Drop a floating chat bubble onto any site with 2 script tags. No build process. Works with React, Vue, WordPress, PHP — anything.
              </p>
            </div>
          </button>

          <button
            onClick={() => setPath('api')}
            className={`flex items-start gap-4 rounded-xl border-2 p-5 text-left transition-all ${
              path === 'api'
                ? 'border-blue-600 bg-blue-50 dark:bg-blue-900/20'
                : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
            }`}
          >
            <Code className={`w-8 h-8 flex-shrink-0 mt-0.5 ${path === 'api' ? 'text-blue-600' : 'text-gray-400'}`} />
            <div>
              <span className="font-semibold text-gray-900 dark:text-white">REST API</span>
              <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                Call the Vernql API directly from your backend and build your own UI. Full control over rendering, database queries, and visualisations.
              </p>
            </div>
          </button>
        </div>

        {/* ── Schema selector (shared) ───────────────────────────────────── */}
        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6 space-y-4">
          <h2 className="font-semibold text-gray-900 dark:text-white flex items-center gap-2">
            <Database className="w-5 h-5 text-blue-600" />
            Before you start — select your schema
          </h2>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {/* Schema pick */}
            <div>
              <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1.5">Schema</label>
              {schemas.length === 0 ? (
                <div className="flex items-center gap-2 text-sm text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg px-3 py-2">
                  <AlertTriangle className="w-4 h-4 flex-shrink-0" />
                  No schemas yet —{' '}
                  <Link href="/dashboard/schemas" className="underline font-medium">upload one first</Link>
                </div>
              ) : (
                <select
                  value={schema}
                  onChange={e => setSchema(e.target.value)}
                  className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="">Choose a schema…</option>
                  {schemas.map(s => (
                    <option key={s.id} value={s.id}>{s.name}</option>
                  ))}
                </select>
              )}
            </div>

            {/* API key reminder */}
            <div>
              <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1.5">API Key</label>
              <div className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300 bg-gray-50 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg px-3 py-2">
                <Key className="w-4 h-4 flex-shrink-0 text-gray-400" />
                <span className="truncate">Replace <code className="bg-gray-200 dark:bg-gray-600 px-1 rounded">YOUR_API_KEY</code> in the snippet</span>
                <Link href="/dashboard/api-keys" className="text-blue-600 dark:text-blue-400 hover:underline whitespace-nowrap flex items-center gap-0.5 ml-auto">
                  Get key <ExternalLink className="w-3 h-3" />
                </Link>
              </div>
            </div>
          </div>

          {/* Checklist */}
          <div className="flex flex-wrap gap-4 pt-1">
            {[
              { label: 'Schema selected', done: hasSchema },
              { label: 'API key ready', done: false },
            ].map(item => (
              <div key={item.label} className="flex items-center gap-1.5 text-sm">
                {item.done
                  ? <CheckCircle2 className="w-4 h-4 text-green-500" />
                  : <div className="w-4 h-4 rounded-full border-2 border-gray-300 dark:border-gray-600" />}
                <span className={item.done ? 'text-green-700 dark:text-green-400' : 'text-gray-500 dark:text-gray-400'}>
                  {item.label}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* ════════════════════════════════════════════════════════════════
            WIDGET PATH
        ════════════════════════════════════════════════════════════════ */}
        {path === 'widget' && (
          <div className="space-y-8">

            {/* How it works */}
            <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
              <h2 className="font-semibold text-gray-900 dark:text-white mb-5">How it works</h2>
              <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3">
                {[
                  { icon: Code,          label: 'You add 2 script tags',         color: 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300' },
                  { icon: MessageSquare, label: 'Floating chat button appears',   color: 'bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300' },
                  { icon: Globe,         label: 'Widget loads in a sandboxed iframe', color: 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300' },
                  { icon: Database,      label: 'Calls Vernql API → returns SQL', color: 'bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-300' },
                  { icon: Zap,           label: 'SQL shown in the chat panel',    color: 'bg-pink-100 dark:bg-pink-900/30 text-pink-700 dark:text-pink-300' },
                ].map((step, i, arr) => (
                  <div key={i} className="flex sm:flex-col items-center gap-2 flex-1">
                    <div className={`w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0 ${step.color}`}>
                      <step.icon className="w-4 h-4" />
                    </div>
                    <span className="text-xs text-gray-600 dark:text-gray-400 text-center leading-tight">{step.label}</span>
                    {i < arr.length - 1 && (
                      <ArrowRight className="w-4 h-4 text-gray-300 dark:text-gray-600 hidden sm:block flex-shrink-0 self-start mt-3" />
                    )}
                  </div>
                ))}
              </div>
              <p className="mt-4 text-xs text-gray-500 dark:text-gray-400 bg-gray-50 dark:bg-gray-700 rounded-lg p-3">
                <strong>Security note:</strong> The widget runs inside a sandboxed <code>&lt;iframe&gt;</code> — it has no access to your page's DOM or cookies. The API key is passed via URL parameters to the iframe on your domain only.
              </p>
            </div>

            {/* Step 1 — get schema/key (already done above) */}
            <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6 space-y-4">
              <div className="flex items-center gap-3">
                <StepBadge n={1} />
                <h2 className="font-semibold text-gray-900 dark:text-white">Copy this snippet into your project</h2>
              </div>

              {!hasSchema && (
                <div className="flex items-center gap-2 text-sm text-amber-700 dark:text-amber-300 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-700 rounded-lg px-3 py-2.5">
                  <AlertTriangle className="w-4 h-4 flex-shrink-0" />
                  Select a schema above to auto-fill the <code className="bg-amber-100 dark:bg-amber-800 px-1 rounded">schemaId</code> in the snippet.
                </div>
              )}
              {hasSchema && (
                <div className="flex items-center gap-2 text-sm text-green-700 dark:text-green-300 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-700 rounded-lg px-3 py-2.5">
                  <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
                  <code className="bg-green-100 dark:bg-green-800 px-1 rounded">schemaId</code> pre-filled with <strong>{schemaName}</strong>
                </div>
              )}

              {/* Framework tabs */}
              <div className="flex flex-wrap gap-1 border-b border-gray-200 dark:border-gray-700 pb-0">
                {WIDGET_TABS.map(t => (
                  <button
                    key={t.id}
                    onClick={() => setWTab(t.id)}
                    className={`px-3 py-2 text-sm font-medium rounded-t-md transition-colors ${
                      wTab === t.id
                        ? 'bg-gray-900 text-white'
                        : 'text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
                    }`}
                  >
                    {t.label}
                  </button>
                ))}
              </div>

              <CodeBlock
                code={widgetSnippets[wTab]}
                id={`widget-${wTab}`}
                copiedId={copied}
                onCopy={handleCopy}
              />
            </div>

            {/* Step 2 — replace YOUR_API_KEY */}
            <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
              <div className="flex items-center gap-3 mb-4">
                <StepBadge n={2} color="green" />
                <h2 className="font-semibold text-gray-900 dark:text-white">Replace <code className="bg-gray-100 dark:bg-gray-700 px-1.5 py-0.5 rounded text-sm">YOUR_API_KEY</code></h2>
              </div>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
                Never hard-code the key in client-side HTML — anyone can see it in the page source. Instead, inject it server-side or through an environment variable:
              </p>
              <div className="overflow-x-auto rounded-lg border border-gray-200 dark:border-gray-700">
                <table className="w-full text-sm">
                  <thead className="bg-gray-50 dark:bg-gray-700">
                    <tr>
                      <th className="text-left px-4 py-2.5 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide">Framework</th>
                      <th className="text-left px-4 py-2.5 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide">Env variable name</th>
                      <th className="text-left px-4 py-2.5 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide">How to use</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                    {[
                      { fw: 'Next.js',    env: 'NEXT_PUBLIC_VERNQL_API_KEY', usage: 'process.env.NEXT_PUBLIC_VERNQL_API_KEY' },
                      { fw: 'React/Vite', env: 'VITE_VERNQL_API_KEY',        usage: 'import.meta.env.VITE_VERNQL_API_KEY' },
                      { fw: 'Vue 3',      env: 'VITE_VERNQL_API_KEY',        usage: 'import.meta.env.VITE_VERNQL_API_KEY' },
                      { fw: 'WordPress',  env: 'WordPress option',            usage: "get_option('vernql_api_key')" },
                    ].map(row => (
                      <tr key={row.fw} className="bg-white dark:bg-gray-800">
                        <td className="px-4 py-3 font-medium text-gray-900 dark:text-white">{row.fw}</td>
                        <td className="px-4 py-3"><code className="text-xs bg-gray-100 dark:bg-gray-700 px-1.5 py-0.5 rounded">{row.env}</code></td>
                        <td className="px-4 py-3"><code className="text-xs bg-gray-100 dark:bg-gray-700 px-1.5 py-0.5 rounded">{row.usage}</code></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Step 3 — done */}
            <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
              <div className="flex items-center gap-3 mb-3">
                <StepBadge n={3} color="purple" />
                <h2 className="font-semibold text-gray-900 dark:text-white">Open your site — the chat button should appear</h2>
              </div>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                A blue floating button will appear in the bottom-right corner. Click it to open the Vernql chat panel. Users can type questions like <em>"Show me revenue by month"</em> and get SQL back instantly.
              </p>
              <div className="mt-4 grid grid-cols-1 sm:grid-cols-3 gap-3 text-sm">
                {[
                  { label: 'Programmatically open',    code: 'Vernql.open()' },
                  { label: 'Programmatically close',   code: 'Vernql.close()' },
                  { label: 'Remove widget from page',  code: 'Vernql.destroy()' },
                ].map(item => (
                  <div key={item.label} className="bg-gray-50 dark:bg-gray-700 rounded-lg px-3 py-2.5">
                    <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">{item.label}</div>
                    <code className="text-xs text-gray-800 dark:text-gray-200">{item.code}</code>
                  </div>
                ))}
              </div>
            </div>

            {/* Config reference */}
            <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
              <h2 className="font-semibold text-gray-900 dark:text-white mb-4">All configuration options</h2>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-gray-50 dark:bg-gray-700">
                    <tr>
                      <th className="text-left px-4 py-2.5 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide">Option</th>
                      <th className="text-left px-4 py-2.5 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide">Type</th>
                      <th className="text-left px-4 py-2.5 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide">Required</th>
                      <th className="text-left px-4 py-2.5 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide">Description</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                    {WIDGET_CONFIG_OPTIONS.map(opt => (
                      <tr key={opt.name} className="bg-white dark:bg-gray-800">
                        <td className="px-4 py-3">
                          <code className="text-xs bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 px-1.5 py-0.5 rounded">{opt.name}</code>
                        </td>
                        <td className="px-4 py-3 text-gray-500 dark:text-gray-400 text-xs">{opt.type}</td>
                        <td className="px-4 py-3">
                          {opt.required
                            ? <span className="text-red-600 dark:text-red-400 font-medium text-xs">Required</span>
                            : <span className="text-gray-400 dark:text-gray-500 text-xs">Optional</span>}
                        </td>
                        <td className="px-4 py-3 text-gray-600 dark:text-gray-400 text-xs">{opt.desc}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Troubleshooting */}
            <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
              <h2 className="font-semibold text-gray-900 dark:text-white mb-4">Troubleshooting</h2>
              <div className="space-y-2">
                {TROUBLESHOOTING.map((item, i) => (
                  <div key={i} className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
                    <button
                      onClick={() => setOpenFaq(openFaq === i ? null : i)}
                      className="w-full flex items-center justify-between px-4 py-3 text-sm font-medium text-left text-gray-900 dark:text-white hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                    >
                      {item.q}
                      {openFaq === i
                        ? <ChevronDown className="w-4 h-4 text-gray-400 flex-shrink-0" />
                        : <ChevronRight className="w-4 h-4 text-gray-400 flex-shrink-0" />}
                    </button>
                    {openFaq === i && (
                      <div className="px-4 pb-4 pt-1 text-sm text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-gray-700 border-t border-gray-200 dark:border-gray-600">
                        {item.a}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* ════════════════════════════════════════════════════════════════
            API PATH
        ════════════════════════════════════════════════════════════════ */}
        {path === 'api' && (
          <div className="space-y-8">

            {/* How the API flow works */}
            <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
              <h2 className="font-semibold text-gray-900 dark:text-white mb-5">3-step API flow</h2>
              <div className="space-y-3">
                {[
                  { step: 1, color: 'blue',   title: 'POST /v1/queries',                body: 'Send your user\'s natural-language question + schema_id. Vernql returns generated SQL and a query_id.' },
                  { step: 2, color: 'green',  title: 'Run the SQL on YOUR database',    body: 'Vernql never touches your data. You execute the SQL with your own DB client (Prisma, pg, mysql2, SQLAlchemy…) and get the rows back.' },
                  { step: 3, color: 'purple', title: 'POST /v1/visualizations/display', body: 'Send the rows back to Vernql along with the query_id. Get a chart type, axis config, and an AI-written insight in return.' },
                ].map(s => (
                  <div key={s.step} className="flex gap-4 items-start">
                    <StepBadge n={s.step} color={s.color} />
                    <div>
                      <code className="text-sm font-mono text-gray-800 dark:text-gray-200">{s.title}</code>
                      <p className="text-sm text-gray-500 dark:text-gray-400 mt-0.5">{s.body}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Code snippets */}
            <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6 space-y-4">
              <h2 className="font-semibold text-gray-900 dark:text-white">Integration code</h2>

              {!hasSchema && (
                <div className="flex items-center gap-2 text-sm text-amber-700 dark:text-amber-300 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-700 rounded-lg px-3 py-2.5">
                  <AlertTriangle className="w-4 h-4 flex-shrink-0" />
                  Select a schema above to pre-fill <code className="bg-amber-100 dark:bg-amber-800 px-1 rounded">schema_id</code>.
                </div>
              )}

              <div className="flex flex-wrap gap-1 border-b border-gray-200 dark:border-gray-700">
                {API_TABS.map(t => (
                  <button
                    key={t.id}
                    onClick={() => setATab(t.id)}
                    className={`px-3 py-2 text-sm font-medium rounded-t-md transition-colors ${
                      aTab === t.id
                        ? 'bg-gray-900 text-white'
                        : 'text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
                    }`}
                  >
                    {t.label}
                  </button>
                ))}
              </div>

              <CodeBlock
                code={apiSnippets[aTab]}
                id={`api-${aTab}`}
                copiedId={copied}
                onCopy={handleCopy}
              />
            </div>

            {/* Response shape */}
            <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
              <h2 className="font-semibold text-gray-900 dark:text-white mb-4">API response shape</h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-2">POST /v1/queries → response</p>
                  <CodeBlock
                    code={`{
  "id":                 "query_abc123",
  "generated_sql":      "SELECT ...",
  "confidence_score":   0.92,       // 0–1
  "warnings":           [],         // low-confidence hints
  "ai_model":           "gpt-4o",
  "ai_provider":        "openai",
  "status":             "success"
}`}
                    id="resp-query"
                    copiedId={copied}
                    onCopy={handleCopy}
                  />
                </div>
                <div>
                  <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-2">POST /v1/visualizations/display → response</p>
                  <CodeBlock
                    code={`{
  "chart_type":   "bar",           // bar|line|pie|table|metric
  "x_axis":       "month",
  "y_axis":       "revenue",
  "ai_insight":   "Revenue peaked in March…",
  "data":         [{ "month": "Jan", … }]
}`}
                    id="resp-viz"
                    copiedId={copied}
                    onCopy={handleCopy}
                  />
                </div>
              </div>
            </div>

            {/* Common errors */}
            <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
              <h2 className="font-semibold text-gray-900 dark:text-white mb-4">Common errors</h2>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-gray-50 dark:bg-gray-700">
                    <tr>
                      <th className="text-left px-4 py-2.5 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide">HTTP status</th>
                      <th className="text-left px-4 py-2.5 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide">Meaning</th>
                      <th className="text-left px-4 py-2.5 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide">Fix</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                    {[
                      { status: '401', meaning: 'Invalid or missing API key', fix: 'Check X-API-Key header. Retrieve a fresh key from the API Keys page.' },
                      { status: '404', meaning: 'Schema not found',           fix: 'Verify schema_id exists in your account. Check /dashboard/schemas.' },
                      { status: '422', meaning: 'Validation error',           fix: 'Read the response body — it lists the exact field that failed.' },
                      { status: '429', meaning: 'Rate limit hit',             fix: 'Back off and retry with exponential backoff. Upgrade your plan for higher limits.' },
                      { status: '500', meaning: 'AI provider error',          fix: 'Transient. Retry once. If persistent, check the status page.' },
                    ].map(r => (
                      <tr key={r.status} className="bg-white dark:bg-gray-800">
                        <td className="px-4 py-3 font-mono text-xs text-red-600 dark:text-red-400">{r.status}</td>
                        <td className="px-4 py-3 text-gray-700 dark:text-gray-300">{r.meaning}</td>
                        <td className="px-4 py-3 text-gray-500 dark:text-gray-400 text-xs">{r.fix}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* ── Footer links ──────────────────────────────────────────────── */}
        <div className="flex flex-wrap gap-4 pt-2 border-t border-gray-200 dark:border-gray-700">
          <Link href="/dashboard/api-keys" className="flex items-center gap-1.5 text-sm text-blue-600 dark:text-blue-400 hover:underline">
            <Key className="w-4 h-4" /> Manage API Keys
          </Link>
          <Link href="/dashboard/schemas" className="flex items-center gap-1.5 text-sm text-blue-600 dark:text-blue-400 hover:underline">
            <Database className="w-4 h-4" /> Upload / manage schemas
          </Link>
          <Link href="/dashboard/queries" className="flex items-center gap-1.5 text-sm text-blue-600 dark:text-blue-400 hover:underline">
            <Zap className="w-4 h-4" /> Test queries live
          </Link>
        </div>

      </div>
    </DashboardLayout>
  )
}
