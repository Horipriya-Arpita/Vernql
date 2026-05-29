'use client'

import { useState } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import toast from 'react-hot-toast'
import { Mail, Lock, Eye, EyeOff, AlertCircle } from 'lucide-react'

export default function LoginPage() {
  const router = useRouter()
  const { login } = useAuth()

  const [formData, setFormData] = useState({ email: '', password: '' })
  const [showPassword, setShowPassword] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value })
    setError('')
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!formData.email || !formData.password) {
      setError('Please enter your email and password')
      return
    }
    setIsLoading(true)
    setError('')
    try {
      await login({ email: formData.email, password: formData.password })
      toast.success('Welcome back!')
      router.push('/dashboard')
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Login failed. Please try again.'
      setError(msg)
      toast.error(msg)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-auth flex items-center justify-center px-4 py-12">
      <div className="max-w-md w-full">

        {/* ── Brand mark + header ── */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-14 h-14 bg-blue-600 rounded-2xl shadow-blue mb-5">
            <span className="text-white font-bold text-2xl leading-none">V</span>
          </div>
          <h1 className="text-3xl font-bold text-slate-900 tracking-tight mb-1.5">
            Welcome back
          </h1>
          <p className="text-slate-500">Sign in to your Vernql account</p>
        </div>

        {/* ── Glassmorphism form card ── */}
        <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl shadow-slate-200/60 border border-white/90 p-8">

          {error && (
            <div className="mb-5 p-4 bg-red-50 border border-red-200 rounded-xl flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-red-500 mt-0.5 flex-shrink-0" />
              <p className="text-sm text-red-700">{error}</p>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">

            {/* Email */}
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-slate-700 mb-2">
                Email Address
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4.5 h-4.5 text-slate-400 pointer-events-none" />
                <input
                  type="email"
                  id="email"
                  name="email"
                  value={formData.email}
                  onChange={handleChange}
                  required
                  autoComplete="email"
                  className="w-full pl-10 pr-4 py-2.5 border border-slate-200 rounded-xl bg-white/70 focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition text-slate-900 placeholder:text-slate-400 text-sm"
                  placeholder="you@company.com"
                />
              </div>
            </div>

            {/* Password */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <label htmlFor="password" className="block text-sm font-medium text-slate-700">
                  Password
                </label>
                <Link href="/forgot-password" className="text-sm text-blue-600 hover:text-blue-700 font-medium">
                  Forgot password?
                </Link>
              </div>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4.5 h-4.5 text-slate-400 pointer-events-none" />
                <input
                  type={showPassword ? 'text' : 'password'}
                  id="password"
                  name="password"
                  value={formData.password}
                  onChange={handleChange}
                  required
                  autoComplete="current-password"
                  className="w-full pl-10 pr-11 py-2.5 border border-slate-200 rounded-xl bg-white/70 focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition text-slate-900 placeholder:text-slate-400 text-sm"
                  placeholder="Enter your password"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 transition-colors"
                >
                  {showPassword ? <EyeOff className="w-4.5 h-4.5" /> : <Eye className="w-4.5 h-4.5" />}
                </button>
              </div>
            </div>

            {/* Submit */}
            <button
              type="submit"
              disabled={isLoading}
              className="w-full bg-blue-600 hover:bg-blue-700 text-white py-2.5 rounded-xl font-semibold text-sm shadow-blue-sm hover:shadow-blue transition-all disabled:opacity-50 disabled:cursor-not-allowed mt-2"
            >
              {isLoading ? 'Signing in…' : 'Sign In'}
            </button>

          </form>

          {/* Divider */}
          <div className="my-6 flex items-center gap-4">
            <div className="flex-1 border-t border-slate-200" />
            <span className="text-xs text-slate-400">or</span>
            <div className="flex-1 border-t border-slate-200" />
          </div>

          {/* Sign-up link */}
          <p className="text-center text-sm text-slate-500">
            Don&apos;t have an account?{' '}
            <Link href="/signup" className="text-blue-600 hover:text-blue-700 font-semibold">
              Create account
            </Link>
          </p>
        </div>

        {/* API Key fallback */}
        <div className="mt-5 text-center">
          <Link href="/dashboard" className="text-sm text-slate-400 hover:text-slate-600 underline underline-offset-2 transition-colors">
            Continue with API Key instead
          </Link>
        </div>

      </div>
    </div>
  )
}
