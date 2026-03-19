'use client'

import React, { createContext, useContext, useState, useEffect } from 'react'
import { apiClient } from '@/lib/api-client'

interface AuthContextType {
  apiKey: string | null
  setApiKey: (key: string) => void
  clearApiKey: () => void
  isAuthenticated: boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [apiKey, setApiKeyState] = useState<string | null>(null)
  const [isAuthenticated, setIsAuthenticated] = useState(false)

  useEffect(() => {
    // Load API key from localStorage on mount
    const storedKey = localStorage.getItem('textsql_api_key')
    if (storedKey) {
      setApiKeyState(storedKey)
      apiClient.setApiKey(storedKey)
      setIsAuthenticated(true)
    }
  }, [])

  const setApiKey = (key: string) => {
    localStorage.setItem('textsql_api_key', key)
    setApiKeyState(key)
    apiClient.setApiKey(key)
    setIsAuthenticated(true)
  }

  const clearApiKey = () => {
    localStorage.removeItem('textsql_api_key')
    setApiKeyState(null)
    apiClient.clearApiKey()
    setIsAuthenticated(false)
  }

  return (
    <AuthContext.Provider value={{ apiKey, setApiKey, clearApiKey, isAuthenticated }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
