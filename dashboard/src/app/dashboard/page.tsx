'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/contexts/AuthContext'
import DashboardLayout from '@/components/DashboardLayout'
import Link from 'next/link'
import { Database, Key, Zap, BarChart3, Code2, ArrowRight } from 'lucide-react'

const features = [
  {
    href:       '/dashboard/schemas',
    icon:       Database,
    iconBg:    'bg-blue-50 dark:bg-blue-900/20',
    iconColor: 'text-blue-600 dark:text-blue-400',
    title:     'Schemas',
    desc:      'Upload and manage your database schemas. AI-powered enrichment available.',
  },
  {
    href:       '/dashboard/api-keys',
    icon:       Key,
    iconBg:    'bg-violet-50 dark:bg-violet-900/20',
    iconColor: 'text-violet-600 dark:text-violet-400',
    title:     'API Keys',
    desc:      'Generate and manage API keys for your applications.',
  },
  {
    href:       '/dashboard/queries',
    icon:       Zap,
    iconBg:    'bg-amber-50 dark:bg-amber-900/20',
    iconColor: 'text-amber-500 dark:text-amber-400',
    title:     'Query Testing',
    desc:      'Test natural language to SQL conversion with your schemas.',
  },
  {
    href:       '/dashboard/visualizations',
    icon:       BarChart3,
    iconBg:    'bg-emerald-50 dark:bg-emerald-900/20',
    iconColor: 'text-emerald-600 dark:text-emerald-400',
    title:     'Visualizations',
    desc:      'Browse and replay AI-generated chart visualizations from past queries.',
  },
  {
    href:       '/dashboard/integrations',
    icon:       Code2,
    iconBg:    'bg-slate-50 dark:bg-slate-700/30',
    iconColor: 'text-slate-600 dark:text-slate-400',
    title:     'Docs & Integration',
    desc:      'Get code snippets and guides to embed Vernql in your app.',
  },
]

const steps = [
  'Upload your database schema in the Schemas section',
  'Let AI enrich your schema with descriptions (optional)',
  'Test queries in the Query Testing section',
  'Generate API keys for your application',
  'Integrate Vernql into your app using the provided code snippets',
]

export default function DashboardPage() {
  const { isAuthenticated, isLoading } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.replace('/login')
    }
  }, [isLoading, isAuthenticated, router])

  if (isLoading || !isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-app">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-600" />
      </div>
    )
  }

  return (
    <DashboardLayout>
      <div>

        {/* ── Page header ── */}
        <div className="mb-10">
          <h1 className="text-4xl font-bold text-slate-900 dark:text-white tracking-tight mb-2">
            Welcome to Vernql
          </h1>
          <p className="text-slate-500 dark:text-slate-400 text-lg">
            Your natural language to SQL platform — set up in minutes.
          </p>
        </div>

        {/* ── Feature cards ── */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
          {features.map((f) => (
            <Link key={f.href} href={f.href} className="group block">
              <div className="bg-white dark:bg-slate-800/70 rounded-2xl border border-slate-100 dark:border-slate-700/50 p-6 h-full hover:shadow-card-hover hover:border-blue-100 dark:hover:border-blue-900/50 transition-all duration-200">
                <div className={`w-11 h-11 ${f.iconBg} rounded-xl flex items-center justify-center mb-4 transition-transform duration-200 group-hover:scale-105`}>
                  <f.icon className={`w-5 h-5 ${f.iconColor}`} />
                </div>
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <h2 className="text-base font-semibold text-slate-900 dark:text-white mb-1">
                      {f.title}
                    </h2>
                    <p className="text-slate-500 dark:text-slate-400 text-sm leading-relaxed">
                      {f.desc}
                    </p>
                  </div>
                  <ArrowRight className="w-4 h-4 text-slate-300 dark:text-slate-600 group-hover:text-blue-500 group-hover:translate-x-0.5 transition-all duration-200 mt-0.5 flex-shrink-0" />
                </div>
              </div>
            </Link>
          ))}
        </div>

        {/* ── Quick start guide ── */}
        <div className="bg-white dark:bg-slate-800/70 rounded-2xl border border-slate-100 dark:border-slate-700/50 p-8">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 bg-blue-600 rounded-xl flex items-center justify-center flex-shrink-0 shadow-blue-sm">
              <Zap className="w-5 h-5 text-white" />
            </div>
            <div>
              <h3 className="text-base font-semibold text-slate-900 dark:text-white">Quick Start</h3>
              <p className="text-sm text-slate-400 dark:text-slate-500">Get up and running in 5 steps</p>
            </div>
          </div>
          <ol className="space-y-3.5">
            {steps.map((step, i) => (
              <li key={i} className="flex items-start gap-3">
                <span className="flex-shrink-0 w-6 h-6 rounded-full bg-blue-600 text-white text-xs font-bold flex items-center justify-center mt-0.5 shadow-sm">
                  {i + 1}
                </span>
                <span className="text-slate-600 dark:text-slate-400 text-sm leading-relaxed pt-0.5">
                  {step}
                </span>
              </li>
            ))}
          </ol>
        </div>

      </div>
    </DashboardLayout>
  )
}
