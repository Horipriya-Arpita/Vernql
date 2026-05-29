'use client'

import { useAuth } from '@/contexts/AuthContext'
import ApiKeyInput from '@/components/ApiKeyInput'
import DashboardLayout from '@/components/DashboardLayout'
import QueryTester from '@/components/QueryTester'

export default function QueriesPage() {
  const { isAuthenticated } = useAuth()

  if (!isAuthenticated) {
    return <ApiKeyInput />
  }

  return (
    <DashboardLayout>
      <div>
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-slate-900 dark:text-white tracking-tight mb-1.5">
            Query Testing
          </h1>
          <p className="text-slate-500 dark:text-slate-400 text-lg">
            Test natural language to SQL conversion with your schemas
          </p>
        </div>
        <QueryTester />
      </div>
    </DashboardLayout>
  )
}
