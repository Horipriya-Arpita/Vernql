'use client'

import { useState } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import DashboardLayout from '@/components/DashboardLayout'
import { Copy, Check, Code, Database, Zap, ArrowRight, ExternalLink, MessageSquare } from 'lucide-react'
import ChatInterface from '@/components/IntegrationExamples/ChatInterface'
import { apiRouteCode, chatComponentCode, envFileCode } from '@/components/IntegrationExamples/ApiRouteCode'

export default function IntegrationPage() {
  const { user } = useAuth()
  const [copied, setCopied] = useState<string | null>(null)
  const [selectedTab, setSelectedTab] = useState<'nextjs' | 'python' | 'curl'>('nextjs')

  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text)
    setCopied(id)
    setTimeout(() => setCopied(null), 2000)
  }

  const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

  return (
    <DashboardLayout>
      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Integration Guide
          </h1>
          <p className="text-gray-600">
            Connect Vernql to your Next.js application in 3 simple steps
          </p>
        </div>

        {/* 3-Step Overview */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
            <div className="flex items-center mb-3">
              <div className="w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center font-bold mr-3">
                1
              </div>
              <Database className="w-6 h-6 text-blue-600" />
            </div>
            <h3 className="font-semibold text-gray-900 mb-2">Upload Schema</h3>
            <p className="text-sm text-gray-600">
              Export your database schema and upload it to Vernql
            </p>
          </div>

          <div className="bg-green-50 border border-green-200 rounded-lg p-6">
            <div className="flex items-center mb-3">
              <div className="w-8 h-8 bg-green-600 text-white rounded-full flex items-center justify-center font-bold mr-3">
                2
              </div>
              <Code className="w-6 h-6 text-green-600" />
            </div>
            <h3 className="font-semibold text-gray-900 mb-2">Add Code</h3>
            <p className="text-sm text-gray-600">
              Copy & paste integration code into your Next.js app
            </p>
          </div>

          <div className="bg-purple-50 border border-purple-200 rounded-lg p-6">
            <div className="flex items-center mb-3">
              <div className="w-8 h-8 bg-purple-600 text-white rounded-full flex items-center justify-center font-bold mr-3">
                3
              </div>
              <Zap className="w-6 h-6 text-purple-600" />
            </div>
            <h3 className="font-semibold text-gray-900 mb-2">Start Querying</h3>
            <p className="text-sm text-gray-600">
              Your users can now ask questions in plain English!
            </p>
          </div>
        </div>

        {/* Step 1: Setup */}
        <div className="bg-white shadow rounded-lg p-6 mb-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-4 flex items-center">
            <span className="w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center font-bold mr-3 text-lg">
              1
            </span>
            Setup Environment Variables
          </h2>

          <p className="text-gray-600 mb-4">
            Add these to your Next.js project's <code className="bg-gray-100 px-2 py-1 rounded">.env.local</code> file:
          </p>

          <div className="bg-gray-900 text-green-400 p-4 rounded-lg font-mono text-sm relative">
            <button
              onClick={() => copyToClipboard(
                `# Vernql Configuration\nVERNQL_API_KEY=your_api_key_here\nVERNQL_BASE_URL=${apiBaseUrl}\nVERNQL_SCHEMA_ID=your_schema_id_here`,
                'env'
              )}
              className="absolute top-4 right-4 text-gray-400 hover:text-white"
            >
              {copied === 'env' ? <Check className="w-5 h-5" /> : <Copy className="w-5 h-5" />}
            </button>
            <pre>{`# Vernql Configuration
VERNQL_API_KEY=your_api_key_here
VERNQL_BASE_URL=${apiBaseUrl}
VERNQL_SCHEMA_ID=your_schema_id_here`}</pre>
          </div>

          <div className="mt-4 flex gap-4">
            <a
              href="/dashboard/api-keys"
              className="inline-flex items-center text-blue-600 hover:text-blue-700 font-medium"
            >
              Get your API Key <ArrowRight className="w-4 h-4 ml-1" />
            </a>
            <a
              href="/dashboard/schemas"
              className="inline-flex items-center text-blue-600 hover:text-blue-700 font-medium"
            >
              Get your Schema ID <ArrowRight className="w-4 h-4 ml-1" />
            </a>
          </div>
        </div>

        {/* Step 2: Integration Code */}
        <div className="bg-white shadow rounded-lg p-6 mb-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-4 flex items-center">
            <span className="w-8 h-8 bg-green-600 text-white rounded-full flex items-center justify-center font-bold mr-3 text-lg">
              2
            </span>
            Add Integration Code
          </h2>

          {/* Tab Selector */}
          <div className="flex gap-2 mb-4 border-b border-gray-200">
            <button
              onClick={() => setSelectedTab('nextjs')}
              className={`px-4 py-2 font-medium ${
                selectedTab === 'nextjs'
                  ? 'text-blue-600 border-b-2 border-blue-600'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              Next.js (App Router)
            </button>
            <button
              onClick={() => setSelectedTab('python')}
              className={`px-4 py-2 font-medium ${
                selectedTab === 'python'
                  ? 'text-blue-600 border-b-2 border-blue-600'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              Python/FastAPI
            </button>
            <button
              onClick={() => setSelectedTab('curl')}
              className={`px-4 py-2 font-medium ${
                selectedTab === 'curl'
                  ? 'text-blue-600 border-b-2 border-blue-600'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              cURL (Test)
            </button>
          </div>

          {/* Next.js Code */}
          {selectedTab === 'nextjs' && (
            <div>
              <p className="text-gray-600 mb-4">
                Create <code className="bg-gray-100 px-2 py-1 rounded">app/api/ask/route.ts</code>:
              </p>
              <div className="bg-gray-900 text-green-400 p-4 rounded-lg font-mono text-sm relative overflow-x-auto">
                <button
                  onClick={() => copyToClipboard(nextjsCode, 'nextjs')}
                  className="absolute top-4 right-4 text-gray-400 hover:text-white"
                >
                  {copied === 'nextjs' ? <Check className="w-5 h-5" /> : <Copy className="w-5 h-5" />}
                </button>
                <pre className="text-xs">{nextjsCode}</pre>
              </div>
            </div>
          )}

          {/* Python Code */}
          {selectedTab === 'python' && (
            <div>
              <p className="text-gray-600 mb-4">
                Add this endpoint to your FastAPI app:
              </p>
              <div className="bg-gray-900 text-green-400 p-4 rounded-lg font-mono text-sm relative overflow-x-auto">
                <button
                  onClick={() => copyToClipboard(pythonCode, 'python')}
                  className="absolute top-4 right-4 text-gray-400 hover:text-white"
                >
                  {copied === 'python' ? <Check className="w-5 h-5" /> : <Copy className="w-5 h-5" />}
                </button>
                <pre className="text-xs">{pythonCode}</pre>
              </div>
            </div>
          )}

          {/* cURL Code */}
          {selectedTab === 'curl' && (
            <div>
              <p className="text-gray-600 mb-4">
                Test the API directly with cURL:
              </p>
              <div className="bg-gray-900 text-green-400 p-4 rounded-lg font-mono text-sm relative overflow-x-auto">
                <button
                  onClick={() => copyToClipboard(curlCode, 'curl')}
                  className="absolute top-4 right-4 text-gray-400 hover:text-white"
                >
                  {copied === 'curl' ? <Check className="w-5 h-5" /> : <Copy className="w-5 h-5" />}
                </button>
                <pre className="text-xs">{curlCode}</pre>
              </div>
            </div>
          )}
        </div>

        {/* Step 3: Flow Diagram */}
        <div className="bg-white shadow rounded-lg p-6 mb-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-4 flex items-center">
            <span className="w-8 h-8 bg-purple-600 text-white rounded-full flex items-center justify-center font-bold mr-3 text-lg">
              3
            </span>
            How It Works (2-Way Connection)
          </h2>

          <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg p-6">
            <div className="space-y-4">
              {/* Step 1 */}
              <div className="flex items-start">
                <div className="flex-shrink-0 w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center font-bold mr-4">
                  1
                </div>
                <div className="flex-1">
                  <div className="bg-white rounded-lg p-4 shadow-sm">
                    <p className="font-semibold text-gray-900">User asks question</p>
                    <p className="text-sm text-gray-600 mt-1">
                      "Show me top 10 customers by revenue"
                    </p>
                  </div>
                </div>
              </div>

              <div className="flex justify-center">
                <ArrowRight className="w-6 h-6 text-gray-400 transform rotate-90" />
              </div>

              {/* Step 2 */}
              <div className="flex items-start">
                <div className="flex-shrink-0 w-8 h-8 bg-green-600 text-white rounded-full flex items-center justify-center font-bold mr-4">
                  2
                </div>
                <div className="flex-1">
                  <div className="bg-white rounded-lg p-4 shadow-sm border-l-4 border-green-600">
                    <p className="font-semibold text-gray-900">Your Next.js app → Vernql API</p>
                    <p className="text-sm text-gray-600 mt-1">
                      POST /v1/queries with question + schema_id
                    </p>
                    <code className="text-xs bg-gray-100 px-2 py-1 rounded mt-2 block">
                      Headers: X-API-Key: vql_prod_...
                    </code>
                  </div>
                </div>
              </div>

              <div className="flex justify-center">
                <ArrowRight className="w-6 h-6 text-gray-400 transform rotate-90" />
              </div>

              {/* Step 3 */}
              <div className="flex items-start">
                <div className="flex-shrink-0 w-8 h-8 bg-purple-600 text-white rounded-full flex items-center justify-center font-bold mr-4">
                  3
                </div>
                <div className="flex-1">
                  <div className="bg-white rounded-lg p-4 shadow-sm border-l-4 border-purple-600">
                    <p className="font-semibold text-gray-900">Vernql → Your Next.js app</p>
                    <p className="text-sm text-gray-600 mt-1">
                      Returns generated SQL + query_id
                    </p>
                    <code className="text-xs bg-gray-100 px-2 py-1 rounded mt-2 block">
                      SELECT customer_name, SUM(revenue) FROM...
                    </code>
                  </div>
                </div>
              </div>

              <div className="flex justify-center">
                <ArrowRight className="w-6 h-6 text-gray-400 transform rotate-90" />
              </div>

              {/* Step 4 */}
              <div className="flex items-start">
                <div className="flex-shrink-0 w-8 h-8 bg-orange-600 text-white rounded-full flex items-center justify-center font-bold mr-4">
                  4
                </div>
                <div className="flex-1">
                  <div className="bg-white rounded-lg p-4 shadow-sm">
                    <p className="font-semibold text-gray-900">Your Next.js app runs SQL</p>
                    <p className="text-sm text-gray-600 mt-1">
                      Execute SQL on YOUR database (Vernql never touches your data)
                    </p>
                  </div>
                </div>
              </div>

              <div className="flex justify-center">
                <ArrowRight className="w-6 h-6 text-gray-400 transform rotate-90" />
              </div>

              {/* Step 5 */}
              <div className="flex items-start">
                <div className="flex-shrink-0 w-8 h-8 bg-green-600 text-white rounded-full flex items-center justify-center font-bold mr-4">
                  5
                </div>
                <div className="flex-1">
                  <div className="bg-white rounded-lg p-4 shadow-sm border-l-4 border-green-600">
                    <p className="font-semibold text-gray-900">Your Next.js app → Vernql API</p>
                    <p className="text-sm text-gray-600 mt-1">
                      POST /v1/visualizations/display with results
                    </p>
                    <code className="text-xs bg-gray-100 px-2 py-1 rounded mt-2 block">
                      {`{ query_id: "...", results: [{...}, {...}] }`}
                    </code>
                  </div>
                </div>
              </div>

              <div className="flex justify-center">
                <ArrowRight className="w-6 h-6 text-gray-400 transform rotate-90" />
              </div>

              {/* Step 6 */}
              <div className="flex items-start">
                <div className="flex-shrink-0 w-8 h-8 bg-purple-600 text-white rounded-full flex items-center justify-center font-bold mr-4">
                  6
                </div>
                <div className="flex-1">
                  <div className="bg-white rounded-lg p-4 shadow-sm border-l-4 border-purple-600">
                    <p className="font-semibold text-gray-900">Vernql → Your Next.js app</p>
                    <p className="text-sm text-gray-600 mt-1">
                      Returns visualization + AI insight + chart type
                    </p>
                    <code className="text-xs bg-gray-100 px-2 py-1 rounded mt-2 block">
                      chart_type: "bar", ai_insight: "Top customer..."
                    </code>
                  </div>
                </div>
              </div>

              <div className="flex justify-center">
                <ArrowRight className="w-6 h-6 text-gray-400 transform rotate-90" />
              </div>

              {/* Step 7 */}
              <div className="flex items-start">
                <div className="flex-shrink-0 w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center font-bold mr-4">
                  7
                </div>
                <div className="flex-1">
                  <div className="bg-white rounded-lg p-4 shadow-sm">
                    <p className="font-semibold text-gray-900">User sees beautiful chart! 🎉</p>
                    <p className="text-sm text-gray-600 mt-1">
                      Bar chart with AI insight displayed in your app
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Chat Interface Example */}
        <div className="bg-gradient-to-r from-green-50 to-blue-50 rounded-lg p-6 mb-6">
          <div className="flex items-center mb-4">
            <MessageSquare className="w-6 h-6 text-green-600 mr-3" />
            <h2 className="text-2xl font-bold text-gray-900">
              Ready-to-Use Chat Interface
            </h2>
          </div>

          <p className="text-gray-700 mb-6">
            Copy this complete chat interface into your Next.js app. It's ready to use - just add your API credentials!
          </p>

          {/* Tab Selector for Code/Preview */}
          <div className="mb-4">
            <div className="flex gap-2 border-b border-gray-300">
              <button
                onClick={() => setSelectedTab('preview' as any)}
                className={`px-4 py-2 font-medium ${
                  selectedTab === 'preview' as any
                    ? 'text-green-600 border-b-2 border-green-600'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                Live Preview
              </button>
              <button
                onClick={() => setSelectedTab('chat-code' as any)}
                className={`px-4 py-2 font-medium ${
                  selectedTab === 'chat-code' as any
                    ? 'text-green-600 border-b-2 border-green-600'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                API Route Code
              </button>
              <button
                onClick={() => setSelectedTab('chat-component' as any)}
                className={`px-4 py-2 font-medium ${
                  selectedTab === 'chat-component' as any
                    ? 'text-green-600 border-b-2 border-green-600'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                Chat Component
              </button>
            </div>
          </div>

          {/* Live Preview */}
          {selectedTab === 'preview' as any && (
            <div className="bg-white rounded-lg shadow-lg p-4">
              <p className="text-sm text-gray-600 mb-4 bg-yellow-50 border-l-4 border-yellow-400 p-3 rounded">
                ⚠️ This is a demo interface. Connect to your real API to make it functional.
              </p>
              <ChatInterface />
            </div>
          )}

          {/* API Route Code */}
          {selectedTab === 'chat-code' as any && (
            <div>
              <div className="mb-4 bg-blue-50 border-l-4 border-blue-400 p-4 rounded">
                <p className="text-sm text-blue-900">
                  <strong>📁 Create this file:</strong> <code className="bg-blue-100 px-2 py-1 rounded">app/api/ask/route.ts</code>
                </p>
              </div>
              <div className="bg-gray-900 text-green-400 p-4 rounded-lg font-mono text-xs relative overflow-x-auto max-h-[500px] overflow-y-auto">
                <button
                  onClick={() => copyToClipboard(apiRouteCode, 'api-route')}
                  className="absolute top-4 right-4 text-gray-400 hover:text-white z-10 bg-gray-800 p-2 rounded"
                >
                  {copied === 'api-route' ? <Check className="w-5 h-5" /> : <Copy className="w-5 h-5" />}
                </button>
                <pre>{apiRouteCode}</pre>
              </div>
            </div>
          )}

          {/* Chat Component Code */}
          {selectedTab === 'chat-component' as any && (
            <div>
              <div className="mb-4 bg-blue-50 border-l-4 border-blue-400 p-4 rounded">
                <p className="text-sm text-blue-900">
                  <strong>📁 Create this file:</strong> <code className="bg-blue-100 px-2 py-1 rounded">components/ChatInterface.tsx</code>
                </p>
              </div>
              <div className="bg-gray-900 text-green-400 p-4 rounded-lg font-mono text-xs relative overflow-x-auto max-h-[500px] overflow-y-auto">
                <button
                  onClick={() => copyToClipboard(chatComponentCode, 'chat-component')}
                  className="absolute top-4 right-4 text-gray-400 hover:text-white z-10 bg-gray-800 p-2 rounded"
                >
                  {copied === 'chat-component' ? <Check className="w-5 h-5" /> : <Copy className="w-5 h-5" />}
                </button>
                <pre>{chatComponentCode}</pre>
              </div>
            </div>
          )}

          {/* Quick Setup Steps */}
          <div className="mt-6 bg-white rounded-lg p-4 border border-gray-200">
            <h4 className="font-semibold text-gray-900 mb-3">🚀 Quick Setup (3 steps)</h4>
            <ol className="space-y-2 text-sm text-gray-700">
              <li className="flex items-start">
                <span className="inline-block w-6 h-6 bg-green-600 text-white rounded-full flex items-center justify-center mr-2 flex-shrink-0 text-xs font-bold">1</span>
                <span>Copy the API route code → Create <code className="bg-gray-100 px-2 py-1 rounded">app/api/ask/route.ts</code></span>
              </li>
              <li className="flex items-start">
                <span className="inline-block w-6 h-6 bg-green-600 text-white rounded-full flex items-center justify-center mr-2 flex-shrink-0 text-xs font-bold">2</span>
                <span>Copy the chat component → Create <code className="bg-gray-100 px-2 py-1 rounded">components/ChatInterface.tsx</code></span>
              </li>
              <li className="flex items-start">
                <span className="inline-block w-6 h-6 bg-green-600 text-white rounded-full flex items-center justify-center mr-2 flex-shrink-0 text-xs font-bold">3</span>
                <span>Add <code className="bg-gray-100 px-2 py-1 rounded">&lt;ChatInterface /&gt;</code> to any page</span>
              </li>
            </ol>
          </div>
        </div>

        {/* Resources */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">📚 Additional Resources</h3>
          <div className="space-y-3">
            <a
              href="https://github.com/yourusername/vernql/blob/main/docs/NEXTJS_INTEGRATION_GUIDE.md"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center text-blue-600 hover:text-blue-700"
            >
              <ExternalLink className="w-4 h-4 mr-2" />
              Full Next.js Integration Guide
            </a>
            <a
              href="/dashboard/api-keys"
              className="flex items-center text-blue-600 hover:text-blue-700"
            >
              <ArrowRight className="w-4 h-4 mr-2" />
              Manage API Keys
            </a>
            <a
              href="/dashboard/schemas"
              className="flex items-center text-blue-600 hover:text-blue-700"
            >
              <ArrowRight className="w-4 h-4 mr-2" />
              Upload Database Schema
            </a>
          </div>
        </div>
      </div>
    </DashboardLayout>
  )
}

// Code snippets
const nextjsCode = `import { NextRequest, NextResponse } from 'next/server';

const VERNQL_API_KEY = process.env.VERNQL_API_KEY!;
const VERNQL_BASE_URL = process.env.VERNQL_BASE_URL!;
const VERNQL_SCHEMA_ID = process.env.VERNQL_SCHEMA_ID!;

export async function POST(request: NextRequest) {
  const { question } = await request.json();

  // Step 1: Get SQL from Vernql
  const sqlRes = await fetch(\`\${VERNQL_BASE_URL}/v1/queries\`, {
    method: 'POST',
    headers: {
      'X-API-Key': VERNQL_API_KEY,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      schema_id: VERNQL_SCHEMA_ID,
      query: question
    })
  });

  const { id: query_id, generated_sql } = await sqlRes.json();

  // Step 2: Run SQL on YOUR database
  const results = await db.query(generated_sql); // Your DB client

  // Step 3: Get visualization from Vernql
  const vizRes = await fetch(\`\${VERNQL_BASE_URL}/v1/visualizations/display\`, {
    method: 'POST',
    headers: {
      'X-API-Key': VERNQL_API_KEY,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      query_id,
      results: results.rows,
      generate_insight: true
    })
  });

  return NextResponse.json(await vizRes.json());
}`

const pythonCode = `import requests
from fastapi import FastAPI, HTTPException

app = FastAPI()
VERNQL_API_KEY = "your_api_key"
VERNQL_BASE_URL = "http://localhost:8000"
VERNQL_SCHEMA_ID = "your_schema_id"

@app.post("/ask")
async def ask_data(question: str):
    # Step 1: Get SQL from Vernql
    sql_response = requests.post(
        f"{VERNQL_BASE_URL}/v1/queries",
        headers={"X-API-Key": VERNQL_API_KEY},
        json={"schema_id": VERNQL_SCHEMA_ID, "query": question}
    )

    data = sql_response.json()
    query_id = data["id"]
    sql = data["generated_sql"]

    # Step 2: Run SQL on your database
    results = your_db.execute(sql).fetchall()

    # Step 3: Get visualization
    viz_response = requests.post(
        f"{VERNQL_BASE_URL}/v1/visualizations/display",
        headers={"X-API-Key": VERNQL_API_KEY},
        json={"query_id": query_id, "results": results}
    )

    return viz_response.json()`

const curlCode = `# Step 1: Get SQL
curl -X POST http://localhost:8000/v1/queries \\
  -H "X-API-Key: your_api_key_here" \\
  -H "Content-Type: application/json" \\
  -d '{
    "schema_id": "your_schema_id",
    "query": "Show me all users"
  }'

# Step 2: Run SQL on your database (manually)

# Step 3: Send results for visualization
curl -X POST http://localhost:8000/v1/visualizations/display \\
  -H "X-API-Key: your_api_key_here" \\
  -H "Content-Type: application/json" \\
  -d '{
    "query_id": "uuid_from_step1",
    "results": [
      {"id": 1, "name": "John"},
      {"id": 2, "name": "Jane"}
    ],
    "generate_insight": true
  }'`
