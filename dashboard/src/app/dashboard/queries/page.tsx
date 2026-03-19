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
      <div className="px-4 py-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">Query Testing</h1>
        <QueryTester />
      </div>
    </DashboardLayout>
  )
}
