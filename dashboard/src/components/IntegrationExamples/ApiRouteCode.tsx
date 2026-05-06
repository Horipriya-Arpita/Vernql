'use client'

export const apiRouteCode = `// app/api/ask/route.ts
import { NextRequest, NextResponse } from 'next/server'

const VERNQL_API_KEY = process.env.VERNQL_API_KEY!
const VERNQL_BASE_URL = process.env.VERNQL_BASE_URL || 'http://localhost:8000'
const VERNQL_SCHEMA_ID = process.env.VERNQL_SCHEMA_ID!

export async function POST(request: NextRequest) {
  try {
    const { question } = await request.json()

    // ==========================================
    // STEP 1: Get SQL from Vernql
    // ==========================================
    const queryResponse = await fetch(\`\${VERNQL_BASE_URL}/v1/queries\`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': VERNQL_API_KEY,
      },
      body: JSON.stringify({
        schema_id: VERNQL_SCHEMA_ID,
        query: question,
      }),
    })

    if (!queryResponse.ok) {
      throw new Error('Failed to generate SQL')
    }

    const queryData = await queryResponse.json()
    const { id: query_id, generated_sql, confidence_score } = queryData

    // ==========================================
    // STEP 2: Run SQL on YOUR database
    // ==========================================
    const results = await runSQLOnYourDatabase(generated_sql)

    // ==========================================
    // STEP 3: Send results to Vernql for visualization
    // ==========================================
    const vizResponse = await fetch(\`\${VERNQL_BASE_URL}/v1/visualizations/display\`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': VERNQL_API_KEY,
      },
      body: JSON.stringify({
        query_id,
        results: results,
        generate_insight: true,
      }),
    })

    if (!vizResponse.ok) {
      throw new Error('Failed to generate visualization')
    }

    const vizData = await vizResponse.json()

    return NextResponse.json({
      sql: generated_sql,
      confidence: confidence_score,
      visualization: vizData,
    })

  } catch (error) {
    console.error('Query error:', error)
    return NextResponse.json(
      { error: 'Failed to process query' },
      { status: 500 }
    )
  }
}

// ==========================================
// Database Query Function (CUSTOMIZE THIS!)
// ==========================================
async function runSQLOnYourDatabase(sql: string) {
  // OPTION 1: Using Prisma
  // const prisma = new PrismaClient()
  // const results = await prisma.$queryRawUnsafe(sql)
  // return results

  // OPTION 2: Using pg (PostgreSQL)
  // import { Pool } from 'pg'
  // const pool = new Pool({ connectionString: process.env.DATABASE_URL })
  // const { rows } = await pool.query(sql)
  // return rows

  // OPTION 3: Using mysql2
  // import mysql from 'mysql2/promise'
  // const connection = await mysql.createConnection(process.env.DATABASE_URL)
  // const [rows] = await connection.execute(sql)
  // return rows

  // TEMPORARY: Mock data for testing
  // Replace this with your actual database query!
  return [
    { id: 1, name: 'Acme Corp', revenue: 125000 },
    { id: 2, name: 'TechStart Inc', revenue: 98000 },
    { id: 3, name: 'Global Solutions', revenue: 87000 },
  ]
}`

export const envFileCode = `# .env.local
VERNQL_API_KEY=vql_prod_your_api_key_here
VERNQL_BASE_URL=http://localhost:8000
VERNQL_SCHEMA_ID=your_schema_uuid_here

# Your Database (choose one)
DATABASE_URL=postgresql://user:password@localhost:5432/your_db
# DATABASE_URL=mysql://user:password@localhost:3306/your_db`

export const chatComponentCode = `// components/ChatInterface.tsx
'use client'

import { useState } from 'react'
import { Send, Loader2 } from 'lucide-react'

export default function ChatInterface() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSend = async () => {
    if (!input.trim()) return

    // Add user message
    setMessages(prev => [...prev, {
      type: 'user',
      content: input
    }])

    setLoading(true)
    const question = input
    setInput('')

    try {
      // Call Vernql API route
      const response = await fetch('/api/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question })
      })

      const data = await response.json()

      // Add assistant message with visualization
      setMessages(prev => [...prev, {
        type: 'assistant',
        content: data.visualization?.ai_insight || 'Here are your results',
        visualization: data.visualization
      }])
    } catch (error) {
      setMessages(prev => [...prev, {
        type: 'assistant',
        content: 'Sorry, something went wrong.'
      }])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex flex-col h-screen max-w-4xl mx-auto">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg, i) => (
          <div key={i} className={\`flex \${msg.type === 'user' ? 'justify-end' : 'justify-start'}\`}>
            <div className={\`max-w-[80%] rounded-lg px-4 py-2 \${
              msg.type === 'user'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100'
            }\`}>
              <p>{msg.content}</p>

              {/* Show visualization data */}
              {msg.visualization && (
                <div className="mt-2 bg-white rounded p-3">
                  <p className="text-sm font-semibold">
                    {msg.visualization.chart_type} chart
                  </p>
                  <p className="text-xs text-gray-600">
                    {msg.visualization.row_count} rows
                  </p>
                </div>
              )}
            </div>
          </div>
        ))}
        {loading && <div>Loading...</div>}
      </div>

      {/* Input */}
      <div className="border-t p-4">
        <div className="flex gap-2">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Ask about your data..."
            className="flex-1 px-4 py-2 border rounded-lg"
          />
          <button
            onClick={handleSend}
            disabled={loading}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  )
}`

export const pageUsageCode = `// app/page.tsx
import ChatInterface from '@/components/ChatInterface'

export default function HomePage() {
  return (
    <main>
      <h1>Ask Your Data</h1>
      <ChatInterface />
    </main>
  )
}`
