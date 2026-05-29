'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useAuth } from '@/contexts/AuthContext'
import { useTheme } from '@/contexts/ThemeContext'
import { Database, Key, Zap, Code2, LogOut, Moon, Sun, Settings, BarChart3 } from 'lucide-react'

interface DashboardLayoutProps {
  children: React.ReactNode
}

const icons: Record<string, React.ReactNode> = {
  database: <Database className="w-4 h-4" />,
  key:      <Key className="w-4 h-4" />,
  zap:      <Zap className="w-4 h-4" />,
  chart:    <BarChart3 className="w-4 h-4" />,
  code:     <Code2 className="w-4 h-4" />,
  settings: <Settings className="w-4 h-4" />,
}

const NavIcon = ({ name }: { name: string }) => <>{icons[name]}</>

const navigation = [
  { name: 'Schemas',        href: '/dashboard/schemas',       icon: 'database' },
  { name: 'API Keys',       href: '/dashboard/api-keys',      icon: 'key'      },
  { name: 'Docs',           href: '/dashboard/integrations',  icon: 'code'     },
  { name: 'Query Testing',  href: '/dashboard/queries',       icon: 'zap'      },
  { name: 'Visualizations', href: '/dashboard/visualizations',icon: 'chart'    },
  { name: 'Settings',       href: '/dashboard/settings',      icon: 'settings' },
]

export default function DashboardLayout({ children }: DashboardLayoutProps) {
  const pathname  = usePathname()
  const { logout, user } = useAuth()
  const { theme, toggleTheme } = useTheme()

  const isActive = (href: string) => pathname?.startsWith(href)
  const userInitial = user ? (user.full_name || user.email || '?')[0].toUpperCase() : '?'

  return (
    <div className="min-h-screen bg-app transition-colors">

      {/* ── Floating navigation bar ── */}
      <div className="px-3 sm:px-4 lg:px-5 pt-4">
        {/* Gradient border wrapper */}
        <div className="p-[1.5px] rounded-2xl bg-gradient-to-r from-blue-500 via-violet-500 to-pink-500 shadow-nav">
        <nav className="bg-white/90 dark:bg-slate-900/90 backdrop-blur-md rounded-[14px]">
          <div className="px-4 sm:px-5">
            <div className="flex items-center justify-between h-16 gap-4">

              {/* Logo */}
              <Link href="/dashboard" className="flex items-center gap-2 flex-shrink-0">
                <div className="w-7 h-7 rounded-lg bg-blue-600 flex items-center justify-center shadow-blue-sm">
                  <span className="text-white font-bold text-xs leading-none">V</span>
                </div>
                <span className="text-lg font-bold text-blue-600 dark:text-blue-400 tracking-tight">
                  Vernql
                </span>
              </Link>

              {/* Desktop nav items — pill-style active state */}
              <div className="hidden sm:flex items-center gap-0.5 flex-1">
                {navigation.map((item) => (
                  <Link
                    key={item.name}
                    href={item.href}
                    className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
                      isActive(item.href)
                        ? 'bg-blue-600 text-white shadow-sm'
                        : 'text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 hover:text-slate-800 dark:hover:text-slate-200'
                    }`}
                  >
                    <NavIcon name={item.icon} />
                    {item.name}
                  </Link>
                ))}
              </div>

              {/* Right controls */}
              <div className="flex items-center gap-2 flex-shrink-0">

                {/* User avatar + info */}
                {user && (
                  <div className="hidden md:flex items-center gap-2.5">
                    <div className="text-right leading-tight">
                      <div className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                        {user.full_name || user.email}
                      </div>
                      {user.company_name && (
                        <div className="text-[11px] text-slate-400 dark:text-slate-500 mt-0.5">
                          {user.company_name}
                        </div>
                      )}
                    </div>
                    <div className="w-8 h-8 rounded-full bg-blue-100 dark:bg-blue-900/40 flex items-center justify-center text-blue-700 dark:text-blue-300 font-bold text-sm flex-shrink-0 ring-2 ring-blue-50 dark:ring-blue-900/30">
                      {userInitial}
                    </div>
                  </div>
                )}

                {/* Theme toggle */}
                <button
                  onClick={toggleTheme}
                  className="p-2 rounded-lg text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 hover:text-slate-600 dark:hover:text-slate-300 transition-colors"
                  title={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
                >
                  {theme === 'dark'
                    ? <Sun className="w-4 h-4" />
                    : <Moon className="w-4 h-4" />}
                </button>

                {/* Sign out */}
                <button
                  onClick={logout}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium text-slate-500 dark:text-slate-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 dark:hover:text-red-400 transition-colors"
                >
                  <LogOut className="w-4 h-4" />
                  <span className="hidden sm:inline">Sign out</span>
                </button>

              </div>
            </div>
          </div>
        </nav>
        </div>{/* end gradient border wrapper */}
      </div>

      {/* ── Mobile navigation (scrollable pill row below the navbar) ── */}
      <div className="sm:hidden mx-3 mt-1.5">
        <div className="p-[1.5px] rounded-xl bg-gradient-to-r from-blue-500 via-violet-500 to-pink-500">
        <div className="bg-white/90 dark:bg-slate-900/90 backdrop-blur-md rounded-[10px] px-3 py-2">
          <div className="flex gap-1 overflow-x-auto no-scrollbar">
            {navigation.map((item) => (
              <Link
                key={item.name}
                href={item.href}
                className={`inline-flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition-all ${
                  isActive(item.href)
                    ? 'bg-blue-600 text-white'
                    : 'text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 hover:text-slate-700 dark:hover:text-slate-300'
                }`}
              >
                <NavIcon name={item.icon} />
                {item.name}
              </Link>
            ))}
          </div>
        </div>
        </div>{/* end gradient border wrapper */}
      </div>

      {/* ── Page content ── */}
      <main className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
        {children}
      </main>

    </div>
  )
}