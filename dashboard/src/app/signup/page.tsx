'use client'

import { useState } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import toast from 'react-hot-toast'
import { Mail, Lock, User, Building2, Eye, EyeOff, AlertCircle } from 'lucide-react'

export default function SignupPage() {
  const router = useRouter()
  const { register } = useAuth()

  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: '',
    full_name: '',
    company_name: '',
  })
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value })
    setError('')
  }

  const validateForm = () => {
    if (!formData.email || !formData.password || !formData.company_name) {
      setError('Please fill in all required fields')
      return false
    }
    if (formData.password.length < 8) {
      setError('Password must be at least 8 characters long')
      return false
    }
    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match')
      return false
    }
    return true
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!validateForm()) return
    setIsLoading(true)
    setError('')
    try {
      await register({
        email: formData.email,
        password: formData.password,
        full_name: formData.full_name || undefined,
        company_name: formData.company_name,
      })
      toast.success('Account created successfully!')
      router.push('/onboarding')
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Registration failed. Please try again.'
      setError(msg)
      toast.error(msg)
    } finally {
      setIsLoading(false)
    }
  }

  const inputClass =
    'w-full pl-10 pr-4 py-2.5 border border-slate-200 rounded-xl bg-white/70 focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition text-slate-900 placeholder:text-slate-400 text-sm'

  return (
    <div className="min-h-screen bg-auth flex items-center justify-center px-4 py-12">
      <div className="max-w-md w-full">

        {/* ── Brand mark + header ── */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-14 h-14 bg-blue-600 rounded-2xl shadow-blue mb-5">
            <span className="text-white font-bold text-2xl leading-none">V</span>
          </div>
          <h1 className="text-3xl font-bold text-slate-900 tracking-tight mb-1.5">
            Create your account
          </h1>
          <p className="text-slate-500">Start using the Vernql Text-to-SQL API</p>
        </div>

        {/* ── Glassmorphism form card ── */}
        <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl shadow-slate-200/60 border border-white/90 p-8">

          {error && (
            <div className="mb-5 p-4 bg-red-50 border border-red-200 rounded-xl flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-red-500 mt-0.5 flex-shrink-0" />
              <p className="text-sm text-red-700">{error}</p>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">

            {/* Email */}
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-slate-700 mb-1.5">
                Email Address <span className="text-red-400">*</span>
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
                <input
                  type="email" id="email" name="email"
                  value={formData.email} onChange={handleChange}
                  required autoComplete="email"
                  className={inputClass}
                  placeholder="you@company.com"
                />
              </div>
            </div>

            {/* Full Name */}
            <div>
              <label htmlFor="full_name" className="block text-sm font-medium text-slate-700 mb-1.5">
                Full Name
              </label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
                <input
                  type="text" id="full_name" name="full_name"
                  value={formData.full_name} onChange={handleChange}
                  className={inputClass}
                  placeholder="John Doe"
                />
              </div>
            </div>

            {/* Company Name */}
            <div>
              <label htmlFor="company_name" className="block text-sm font-medium text-slate-700 mb-1.5">
                Company Name <span className="text-red-400">*</span>
              </label>
              <div className="relative">
                <Building2 className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
                <input
                  type="text" id="company_name" name="company_name"
                  value={formData.company_name} onChange={handleChange}
                  required className={inputClass}
                  placeholder="Acme Corporation"
                />
              </div>
            </div>

            {/* Password */}
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-slate-700 mb-1.5">
                Password <span className="text-red-400">*</span>
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
                <input
                  type={showPassword ? 'text' : 'password'}
                  id="password" name="password"
                  value={formData.password} onChange={handleChange}
                  required minLength={8}
                  className="w-full pl-10 pr-11 py-2.5 border border-slate-200 rounded-xl bg-white/70 focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition text-slate-900 placeholder:text-slate-400 text-sm"
                  placeholder="Minimum 8 characters"
                />
                <button type="button" onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 transition-colors">
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            {/* Confirm Password */}
            <div>
              <label htmlFor="confirmPassword" className="block text-sm font-medium text-slate-700 mb-1.5">
                Confirm Password <span className="text-red-400">*</span>
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
                <input
                  type={showConfirmPassword ? 'text' : 'password'}
                  id="confirmPassword" name="confirmPassword"
                  value={formData.confirmPassword} onChange={handleChange}
                  required
                  className="w-full pl-10 pr-11 py-2.5 border border-slate-200 rounded-xl bg-white/70 focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition text-slate-900 placeholder:text-slate-400 text-sm"
                  placeholder="Re-enter password"
                />
                <button type="button" onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 transition-colors">
                  {showConfirmPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            {/* Submit */}
            <button
              type="submit"
              disabled={isLoading}
              className="w-full bg-blue-600 hover:bg-blue-700 text-white py-2.5 rounded-xl font-semibold text-sm shadow-blue-sm hover:shadow-blue transition-all disabled:opacity-50 disabled:cursor-not-allowed mt-2"
            >
              {isLoading ? 'Creating Account…' : 'Create Account'}
            </button>

          </form>

          {/* Divider */}
          <div className="my-6 flex items-center gap-4">
            <div className="flex-1 border-t border-slate-200" />
            <span className="text-xs text-slate-400">or</span>
            <div className="flex-1 border-t border-slate-200" />
          </div>

          {/* Login link */}
          <p className="text-center text-sm text-slate-500">
            Already have an account?{' '}
            <Link href="/login" className="text-blue-600 hover:text-blue-700 font-semibold">
              Sign in
            </Link>
          </p>
        </div>

        {/* Footer */}
        <p className="text-center text-xs text-slate-400 mt-5">
          By creating an account you agree to our{' '}
          <Link href="/terms" className="text-blue-500 hover:underline">Terms of Service</Link>{' '}
          and{' '}
          <Link href="/privacy" className="text-blue-500 hover:underline">Privacy Policy</Link>
        </p>

      </div>
    </div>
  )
}
