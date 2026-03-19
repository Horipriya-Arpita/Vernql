'use client'

import { useAuth } from '@/contexts/AuthContext'
import ApiKeyInput from '@/components/ApiKeyInput'
import DashboardLayout from '@/components/DashboardLayout'
import ApiKeyManager from '@/components/ApiKeyManager'

export default function ApiKeysPage() {
  const { isAuthenticated } = useAuth()

  if (!isAuthenticated) {
    return <ApiKeyInput />
  }

  return (
    <DashboardLayout>
      <div className="px-4 py-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">API Key Management</h1>
        <ApiKeyManager />
      </div>
    </DashboardLayout>
  )
}
