'use client'

import { useAuth } from '@/contexts/AuthContext'
import ApiKeyInput from '@/components/ApiKeyInput'
import DashboardLayout from '@/components/DashboardLayout'
import Link from 'next/link'

export default function DashboardPage() {
  const { isAuthenticated } = useAuth()

  if (!isAuthenticated) {
    return <ApiKeyInput />
  }

  return (
    <DashboardLayout>
      <div className="px-4 py-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">Dashboard</h1>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Schemas Card */}
          <Link href="/dashboard/schemas" className="block">
            <div className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition-shadow cursor-pointer">
              <div className="flex items-center mb-4">
                <span className="text-4xl mr-4">📊</span>
                <h2 className="text-xl font-semibold text-gray-900">Schemas</h2>
              </div>
              <p className="text-gray-600">
                Upload and manage your database schemas. AI-powered enrichment available.
              </p>
            </div>
          </Link>

          {/* API Keys Card */}
          <Link href="/dashboard/api-keys" className="block">
            <div className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition-shadow cursor-pointer">
              <div className="flex items-center mb-4">
                <span className="text-4xl mr-4">🔑</span>
                <h2 className="text-xl font-semibold text-gray-900">API Keys</h2>
              </div>
              <p className="text-gray-600">
                Generate and manage API keys for your applications.
              </p>
            </div>
          </Link>

          {/* Query Testing Card */}
          <Link href="/dashboard/queries" className="block">
            <div className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition-shadow cursor-pointer">
              <div className="flex items-center mb-4">
                <span className="text-4xl mr-4">⚡</span>
                <h2 className="text-xl font-semibold text-gray-900">Query Testing</h2>
              </div>
              <p className="text-gray-600">
                Test natural language to SQL conversion with your schemas.
              </p>
            </div>
          </Link>
        </div>

        {/* Quick Start Guide */}
        <div className="mt-8 bg-blue-50 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Start</h3>
          <ol className="list-decimal list-inside space-y-2 text-gray-700">
            <li>Upload your database schema in the Schemas section</li>
            <li>Let AI enrich your schema with descriptions (optional)</li>
            <li>Test queries in the Query Testing section</li>
            <li>Generate API keys for your application</li>
            <li>Integrate TextSQL into your app using the provided code snippets</li>
          </ol>
        </div>
      </div>
    </DashboardLayout>
  )
}
