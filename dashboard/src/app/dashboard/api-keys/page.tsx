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
      <div>
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-slate-900 dark:text-white tracking-tight mb-1.5">
            API Key Management
          </h1>
          <p className="text-slate-500 dark:text-slate-400 text-lg">
            Generate and manage API keys for your applications
          </p>
        </div>
        <ApiKeyManager />
      </div>
    </DashboardLayout>
  )
}
