'use client'

import React, { createContext, useContext, useState, useEffect } from 'react'
import { apiClient } from '@/lib/api-client'
import { setCookie, getCookie, deleteCookie } from '@/lib/cookies'
import type { UserResponse, UserRegister, UserLogin } from '@/lib/types'

interface AuthContextType {
  // User state
  user: UserResponse | null
  isAuthenticated: boolean
  isLoading: boolean

  // JWT Authentication
  login: (credentials: UserLogin) => Promise<void>
  register: (data: UserRegister) => Promise<void>
  logout: () => void

  // Legacy API Key Authentication (for backward compatibility)
  apiKey: string | null
  setApiKey: (key: string) => void
  clearApiKey: () => void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<UserResponse | null>(null)
  const [apiKey, setApiKeyState] = useState<string | null>(null)
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [isLoading, setIsLoading] = useState(true)

  // Load authentication state on mount
  useEffect(() => {
    const loadAuthState = async () => {
      // Try to load JWT token first (from localStorage, cookies are synced)
      const accessToken = localStorage.getItem('access_token')
      if (accessToken) {
        apiClient.setAccessToken(accessToken)
        try {
          const userData = await apiClient.getCurrentUser()
          setUser(userData)
          setIsAuthenticated(true)
        } catch (error) {
          // Token invalid or expired, clear it
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
          deleteCookie('access_token')
          deleteCookie('refresh_token')
          apiClient.clearAccessToken()
        }
      } else {
        // Fallback to API key authentication — read from cookie only (not localStorage)
        const storedKey = getCookie('textsql_api_key')
        if (storedKey) {
          setApiKeyState(storedKey)
          apiClient.setApiKey(storedKey)
          setIsAuthenticated(true)
        }
      }
      setIsLoading(false)
    }

    loadAuthState()
  }, [])

  // Register new user
  const register = async (data: UserRegister) => {
    try {
      const response = await apiClient.register(data)

      // Store tokens in both localStorage and cookies
      localStorage.setItem('access_token', response.tokens.access_token)
      localStorage.setItem('refresh_token', response.tokens.refresh_token)
      setCookie('access_token', response.tokens.access_token, 7) // 7 days
      setCookie('refresh_token', response.tokens.refresh_token, 30) // 30 days

      // Set access token for API client
      apiClient.setAccessToken(response.tokens.access_token)

      // Update state
      setUser(response.user)
      setIsAuthenticated(true)
    } catch (error) {
      throw error
    }
  }

  // Login user
  const login = async (credentials: UserLogin) => {
    try {
      const response = await apiClient.login(credentials)

      // Store tokens in both localStorage and cookies
      localStorage.setItem('access_token', response.tokens.access_token)
      localStorage.setItem('refresh_token', response.tokens.refresh_token)
      setCookie('access_token', response.tokens.access_token, 7) // 7 days
      setCookie('refresh_token', response.tokens.refresh_token, 30) // 30 days

      // Set access token for API client
      apiClient.setAccessToken(response.tokens.access_token)

      // Update state
      setUser(response.user)
      setIsAuthenticated(true)
    } catch (error) {
      throw error
    }
  }

  // Logout user
  const logout = () => {
    // Clear tokens from localStorage and cookies
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    deleteCookie('access_token')
    deleteCookie('refresh_token')
    deleteCookie('textsql_api_key')

    // Clear API client auth
    apiClient.clearAccessToken()
    apiClient.clearApiKey()

    // Clear state
    setUser(null)
    setApiKeyState(null)
    setIsAuthenticated(false)
  }

  // Legacy API key methods (backward compatibility)
  const setApiKey = (key: string) => {
    setCookie('textsql_api_key', key, 30) // 30 days — cookie only, not localStorage
    setApiKeyState(key)
    apiClient.setApiKey(key)
    setIsAuthenticated(true)
  }

  const clearApiKey = () => {
    deleteCookie('textsql_api_key')
    setApiKeyState(null)
    apiClient.clearApiKey()
    setIsAuthenticated(false)
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated,
        isLoading,
        login,
        register,
        logout,
        apiKey,
        setApiKey,
        clearApiKey,
      }}
    >
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