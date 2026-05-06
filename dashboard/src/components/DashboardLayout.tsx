'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useAuth } from '@/contexts/AuthContext'
import { useTheme } from '@/contexts/ThemeContext'
import { Database, Key, Zap, Code2, LogOut, Moon, Sun, Settings, BarChart3 } from 'lucide-react'

interface DashboardLayoutProps {
  children: React.ReactNode
}

const IconComponent = ({ name }: { name: string }) => {
  const icons: Record<string, React.ReactNode> = {
    database: <Database className="w-4 h-4" />,
    key: <Key className="w-4 h-4" />,
    zap: <Zap className="w-4 h-4" />,
    chart: <BarChart3 className="w-4 h-4" />,
    code: <Code2 className="w-4 h-4" />,
    settings: <Settings className="w-4 h-4" />,
  }
  return <>{icons[name]}</>
}

export default function DashboardLayout({ children }: DashboardLayoutProps) {
  const pathname = usePathname()
  const { logout, user } = useAuth()
  const { theme, toggleTheme } = useTheme()

  const navigation = [
    { name: 'Schemas', href: '/dashboard/schemas', icon: 'database' },
    { name: 'API Keys', href: '/dashboard/api-keys', icon: 'key' },
    { name: 'Docs', href: '/dashboard/integrations', icon: 'code' },
    { name: 'Query Testing', href: '/dashboard/queries', icon: 'zap' },
    { name: 'Visualizations', href: '/dashboard/visualizations', icon: 'chart' },
    { name: 'Settings', href: '/dashboard/settings', icon: 'settings' },
  ]

  const isActive = (href: string) => pathname?.startsWith(href)

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 transition-colors">
      {/* Top Navigation */}
      <nav className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 transition-colors">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex">
              <Link href="/dashboard" className="flex items-center">
                <span className="text-2xl font-bold text-blue-600 dark:text-blue-400">TextSQL</span>
              </Link>
              <div className="hidden sm:ml-8 sm:flex sm:space-x-8">
                {navigation.map((item) => (
                  <Link
                    key={item.name}
                    href={item.href}
                    className={`inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium transition-colors ${
                      isActive(item.href)
                        ? 'border-blue-500 text-gray-900 dark:text-white'
                        : 'border-transparent text-gray-500 dark:text-gray-400 hover:border-gray-300 dark:hover:border-gray-600 hover:text-gray-700 dark:hover:text-gray-300'
                    }`}
                  >
                    <span className="mr-2">
                      <IconComponent name={item.icon} />
                    </span>
                    {item.name}
                  </Link>
                ))}
              </div>
            </div>
            <div className="flex items-center space-x-4">
              {/* User Info */}
              {user && (
                <div className="hidden md:flex items-center text-sm text-gray-700 dark:text-gray-300">
                  <div className="text-right mr-3">
                    <div className="font-medium">{user.full_name || user.email}</div>
                    <div className="text-xs text-gray-500 dark:text-gray-400">{user.company_name}</div>
                  </div>
                </div>
              )}

              {/* Theme Toggle */}
              <button
                onClick={toggleTheme}
                className="p-2 rounded-lg text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                title={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
              >
                {theme === 'dark' ? (
                  <Sun className="w-5 h-5" />
                ) : (
                  <Moon className="w-5 h-5" />
                )}
              </button>

              {/* Logout Button */}
              <button
                onClick={logout}
                className="inline-flex items-center px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:text-red-600 dark:hover:text-red-400 transition-colors"
              >
                <LogOut className="w-4 h-4 mr-2" />
                <span className="hidden sm:inline">Logout</span>
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Mobile Navigation */}
      <div className="sm:hidden bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <div className="pt-2 pb-3 space-y-1">
          {navigation.map((item) => (
            <Link
              key={item.name}
              href={item.href}
              className={`flex items-center pl-3 pr-4 py-2 border-l-4 text-base font-medium ${
                isActive(item.href)
                  ? 'bg-blue-50 dark:bg-blue-900/20 border-blue-500 text-blue-700 dark:text-blue-400'
                  : 'border-transparent text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700 hover:border-gray-300 dark:hover:border-gray-600 hover:text-gray-800 dark:hover:text-gray-300'
              }`}
            >
              <span className="mr-2">
                <IconComponent name={item.icon} />
              </span>
              {item.name}
            </Link>
          ))}
        </div>
      </div>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        {children}
      </main>
    </div>
  )
}
