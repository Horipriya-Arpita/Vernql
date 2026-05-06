'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/contexts/AuthContext'
import {
  CheckCircle,
  Circle,
  ArrowRight,
  ArrowLeft,
  Sparkles,
  Database,
  Zap,
  Key,
  Rocket
} from 'lucide-react'

interface Step {
  id: number
  title: string
  description: string
  icon: React.ReactNode
  content: React.ReactNode
}

export default function OnboardingWizard() {
  const router = useRouter()
  const { user } = useAuth()
  const [currentStep, setCurrentStep] = useState(0)

  const steps: Step[] = [
    {
      id: 1,
      title: 'Welcome to Vernql',
      description: 'Your Natural Language to SQL API',
      icon: <Sparkles className="w-8 h-8" />,
      content: (
        <div className="space-y-6">
          <div className="text-center">
            <div className="inline-flex items-center justify-center w-20 h-20 bg-blue-100 dark:bg-blue-900/30 rounded-full mb-4">
              <Sparkles className="w-10 h-10 text-blue-600 dark:text-blue-400" />
            </div>
            <h2 className="text-3xl font-bold text-gray-900 dark:text-white mb-4">
              Welcome, {user?.full_name || 'there'}! 👋
            </h2>
            <p className="text-lg text-gray-600 dark:text-gray-400 max-w-2xl mx-auto">
              You've successfully created your account with <strong>{user?.company_name}</strong>.
              Let's get you set up with Vernql's powerful Text-to-SQL API in just a few steps.
            </p>
          </div>

          <div className="bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 rounded-lg p-6 mt-8">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">
              What you'll learn:
            </h3>
            <ul className="space-y-3">
              <li className="flex items-start">
                <CheckCircle className="w-5 h-5 text-green-600 dark:text-green-400 mr-3 mt-0.5 flex-shrink-0" />
                <span className="text-gray-700 dark:text-gray-300">
                  How to upload and manage your database schemas
                </span>
              </li>
              <li className="flex items-start">
                <CheckCircle className="w-5 h-5 text-green-600 dark:text-green-400 mr-3 mt-0.5 flex-shrink-0" />
                <span className="text-gray-700 dark:text-gray-300">
                  Testing natural language queries in real-time
                </span>
              </li>
              <li className="flex items-start">
                <CheckCircle className="w-5 h-5 text-green-600 dark:text-green-400 mr-3 mt-0.5 flex-shrink-0" />
                <span className="text-gray-700 dark:text-gray-300">
                  Generating and managing API keys for your applications
                </span>
              </li>
              <li className="flex items-start">
                <CheckCircle className="w-5 h-5 text-green-600 dark:text-green-400 mr-3 mt-0.5 flex-shrink-0" />
                <span className="text-gray-700 dark:text-gray-300">
                  Integrating the API into your application
                </span>
              </li>
            </ul>
          </div>
        </div>
      ),
    },
    {
      id: 2,
      title: 'Upload Database Schema',
      description: 'Connect your database structure',
      icon: <Database className="w-8 h-8" />,
      content: (
        <div className="space-y-6">
          <div className="text-center mb-6">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-purple-100 dark:bg-purple-900/30 rounded-full mb-4">
              <Database className="w-8 h-8 text-purple-600 dark:text-purple-400" />
            </div>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
              Database Schema
            </h2>
            <p className="text-gray-600 dark:text-gray-400">
              Your schema is the foundation for accurate SQL generation
            </p>
          </div>

          <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              What is a database schema?
            </h3>
            <p className="text-gray-700 dark:text-gray-300 mb-4">
              A database schema defines the structure of your database including tables,
              columns, data types, and relationships. Vernql uses this information to
              generate accurate SQL queries from natural language.
            </p>

            <h4 className="text-md font-semibold text-gray-900 dark:text-white mb-3 mt-6">
              Supported formats:
            </h4>
            <ul className="space-y-2">
              <li className="flex items-start">
                <CheckCircle className="w-5 h-5 text-green-600 dark:text-green-400 mr-2 mt-0.5" />
                <div>
                  <strong className="text-gray-900 dark:text-white">SQL DDL</strong>
                  <span className="text-gray-600 dark:text-gray-400"> - CREATE TABLE statements</span>
                </div>
              </li>
              <li className="flex items-start">
                <CheckCircle className="w-5 h-5 text-green-600 dark:text-green-400 mr-2 mt-0.5" />
                <div>
                  <strong className="text-gray-900 dark:text-white">JSON Schema</strong>
                  <span className="text-gray-600 dark:text-gray-400"> - Structured JSON format</span>
                </div>
              </li>
            </ul>
          </div>

          <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
            <p className="text-sm text-blue-900 dark:text-blue-300">
              <strong>💡 Pro Tip:</strong> Use our AI enrichment feature to automatically
              generate helpful descriptions for your tables and columns!
            </p>
          </div>
        </div>
      ),
    },
    {
      id: 3,
      title: 'Test Your Queries',
      description: 'Try natural language to SQL conversion',
      icon: <Zap className="w-8 h-8" />,
      content: (
        <div className="space-y-6">
          <div className="text-center mb-6">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-yellow-100 dark:bg-yellow-900/30 rounded-full mb-4">
              <Zap className="w-8 h-8 text-yellow-600 dark:text-yellow-400" />
            </div>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
              Query Testing
            </h2>
            <p className="text-gray-600 dark:text-gray-400">
              See the magic in action with real-time query conversion
            </p>
          </div>

          <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              How it works:
            </h3>
            <div className="space-y-4">
              <div className="flex items-start">
                <div className="flex-shrink-0 w-8 h-8 bg-blue-100 dark:bg-blue-900/30 rounded-full flex items-center justify-center mr-3">
                  <span className="text-blue-600 dark:text-blue-400 font-bold">1</span>
                </div>
                <div>
                  <h4 className="font-semibold text-gray-900 dark:text-white">Write your question</h4>
                  <p className="text-gray-600 dark:text-gray-400 text-sm">
                    Type a natural language question like "Show me all users who signed up last month"
                  </p>
                </div>
              </div>

              <div className="flex items-start">
                <div className="flex-shrink-0 w-8 h-8 bg-blue-100 dark:bg-blue-900/30 rounded-full flex items-center justify-center mr-3">
                  <span className="text-blue-600 dark:text-blue-400 font-bold">2</span>
                </div>
                <div>
                  <h4 className="font-semibold text-gray-900 dark:text-white">Get instant SQL</h4>
                  <p className="text-gray-600 dark:text-gray-400 text-sm">
                    Our AI analyzes your schema and generates optimized SQL
                  </p>
                </div>
              </div>

              <div className="flex items-start">
                <div className="flex-shrink-0 w-8 h-8 bg-blue-100 dark:bg-blue-900/30 rounded-full flex items-center justify-center mr-3">
                  <span className="text-blue-600 dark:text-blue-400 font-bold">3</span>
                </div>
                <div>
                  <h4 className="font-semibold text-gray-900 dark:text-white">Review and refine</h4>
                  <p className="text-gray-600 dark:text-gray-400 text-sm">
                    View the generated SQL and provide feedback to improve accuracy
                  </p>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-gradient-to-r from-gray-50 to-gray-100 dark:from-gray-800 dark:to-gray-700 rounded-lg p-6">
            <h4 className="font-semibold text-gray-900 dark:text-white mb-3">Example queries:</h4>
            <div className="space-y-2 text-sm">
              <div className="bg-white dark:bg-gray-900 rounded px-3 py-2 text-gray-700 dark:text-gray-300">
                "What are the top 10 customers by revenue?"
              </div>
              <div className="bg-white dark:bg-gray-900 rounded px-3 py-2 text-gray-700 dark:text-gray-300">
                "Show me all pending orders from the last week"
              </div>
              <div className="bg-white dark:bg-gray-900 rounded px-3 py-2 text-gray-700 dark:text-gray-300">
                "Find users who haven't logged in for 30 days"
              </div>
            </div>
          </div>
        </div>
      ),
    },
    {
      id: 4,
      title: 'Generate API Keys',
      description: 'Secure access for your applications',
      icon: <Key className="w-8 h-8" />,
      content: (
        <div className="space-y-6">
          <div className="text-center mb-6">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-green-100 dark:bg-green-900/30 rounded-full mb-4">
              <Key className="w-8 h-8 text-green-600 dark:text-green-400" />
            </div>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
              API Keys
            </h2>
            <p className="text-gray-600 dark:text-gray-400">
              Secure authentication for your production applications
            </p>
          </div>

          <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Why use API keys?
            </h3>
            <ul className="space-y-3">
              <li className="flex items-start">
                <CheckCircle className="w-5 h-5 text-green-600 dark:text-green-400 mr-2 mt-0.5" />
                <span className="text-gray-700 dark:text-gray-300">
                  Secure server-to-server authentication
                </span>
              </li>
              <li className="flex items-start">
                <CheckCircle className="w-5 h-5 text-green-600 dark:text-green-400 mr-2 mt-0.5" />
                <span className="text-gray-700 dark:text-gray-300">
                  Rate limiting and usage tracking
                </span>
              </li>
              <li className="flex items-start">
                <CheckCircle className="w-5 h-5 text-green-600 dark:text-green-400 mr-2 mt-0.5" />
                <span className="text-gray-700 dark:text-gray-300">
                  Easy revocation and rotation
                </span>
              </li>
              <li className="flex items-start">
                <CheckCircle className="w-5 h-5 text-green-600 dark:text-green-400 mr-2 mt-0.5" />
                <span className="text-gray-700 dark:text-gray-300">
                  Separate keys for different environments (dev, staging, prod)
                </span>
              </li>
            </ul>
          </div>

          <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg p-4">
            <h4 className="font-semibold text-amber-900 dark:text-amber-300 mb-2">
              🔒 Security Best Practices
            </h4>
            <ul className="space-y-1 text-sm text-amber-800 dark:text-amber-400">
              <li>• Never commit API keys to version control</li>
              <li>• Store keys in environment variables</li>
              <li>• Rotate keys regularly</li>
              <li>• Use different keys for each environment</li>
              <li>• Revoke unused or compromised keys immediately</li>
            </ul>
          </div>
        </div>
      ),
    },
    {
      id: 5,
      title: 'You\'re All Set!',
      description: 'Start building amazing things',
      icon: <Rocket className="w-8 h-8" />,
      content: (
        <div className="space-y-6">
          <div className="text-center mb-6">
            <div className="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full mb-4">
              <Rocket className="w-10 h-10 text-white" />
            </div>
            <h2 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
              Ready to Launch! 🚀
            </h2>
            <p className="text-lg text-gray-600 dark:text-gray-400">
              You're all set up and ready to start using Vernql
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-900/30 dark:to-blue-800/30 rounded-lg p-6 border border-blue-200 dark:border-blue-700">
              <h3 className="text-lg font-semibold text-blue-900 dark:text-blue-300 mb-3">
                Next Steps
              </h3>
              <ul className="space-y-2 text-sm text-blue-800 dark:text-blue-400">
                <li className="flex items-center">
                  <ArrowRight className="w-4 h-4 mr-2" />
                  Upload your first schema
                </li>
                <li className="flex items-center">
                  <ArrowRight className="w-4 h-4 mr-2" />
                  Test some queries
                </li>
                <li className="flex items-center">
                  <ArrowRight className="w-4 h-4 mr-2" />
                  Generate your API key
                </li>
                <li className="flex items-center">
                  <ArrowRight className="w-4 h-4 mr-2" />
                  Integrate into your app
                </li>
              </ul>
            </div>

            <div className="bg-gradient-to-br from-purple-50 to-purple-100 dark:from-purple-900/30 dark:to-purple-800/30 rounded-lg p-6 border border-purple-200 dark:border-purple-700">
              <h3 className="text-lg font-semibold text-purple-900 dark:text-purple-300 mb-3">
                Resources
              </h3>
              <ul className="space-y-2 text-sm text-purple-800 dark:text-purple-400">
                <li className="flex items-center">
                  <ArrowRight className="w-4 h-4 mr-2" />
                  API Documentation
                </li>
                <li className="flex items-center">
                  <ArrowRight className="w-4 h-4 mr-2" />
                  Code Examples
                </li>
                <li className="flex items-center">
                  <ArrowRight className="w-4 h-4 mr-2" />
                  Integration Guides
                </li>
                <li className="flex items-center">
                  <ArrowRight className="w-4 h-4 mr-2" />
                  Support & Help
                </li>
              </ul>
            </div>
          </div>

          <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg p-8 text-center text-white">
            <h3 className="text-2xl font-bold mb-3">
              Thank you for choosing Vernql! 💙
            </h3>
            <p className="text-blue-100 mb-0">
              We're excited to see what you'll build with our Text-to-SQL API.
              If you have any questions, our support team is here to help.
            </p>
          </div>
        </div>
      ),
    },
  ]

  const handleNext = () => {
    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1)
    }
  }

  const handlePrevious = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1)
    }
  }

  const handleFinish = () => {
    router.push('/dashboard')
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900">
      <div className="max-w-4xl mx-auto px-4 py-12">
        {/* Progress Steps */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            {steps.map((step, index) => (
              <div key={step.id} className="flex items-center flex-1">
                <div className="flex flex-col items-center flex-1">
                  <button
                    onClick={() => setCurrentStep(index)}
                    className={`w-10 h-10 rounded-full flex items-center justify-center transition-all ${
                      index === currentStep
                        ? 'bg-blue-600 text-white ring-4 ring-blue-200 dark:ring-blue-900'
                        : index < currentStep
                        ? 'bg-green-600 text-white'
                        : 'bg-gray-200 dark:bg-gray-700 text-gray-500 dark:text-gray-400'
                    }`}
                  >
                    {index < currentStep ? (
                      <CheckCircle className="w-6 h-6" />
                    ) : (
                      <Circle className="w-6 h-6" fill={index === currentStep ? 'currentColor' : 'none'} />
                    )}
                  </button>
                  <span className="text-xs mt-2 text-center text-gray-600 dark:text-gray-400 hidden md:block">
                    {step.title}
                  </span>
                </div>
                {index < steps.length - 1 && (
                  <div
                    className={`h-1 flex-1 mx-2 rounded ${
                      index < currentStep
                        ? 'bg-green-600'
                        : 'bg-gray-200 dark:bg-gray-700'
                    }`}
                  />
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Content Card */}
        <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl p-8 md:p-12 mb-6">
          {steps[currentStep].content}
        </div>

        {/* Navigation Buttons */}
        <div className="flex items-center justify-between">
          <button
            onClick={handlePrevious}
            disabled={currentStep === 0}
            className="inline-flex items-center px-6 py-3 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-700 dark:text-gray-300 font-medium hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <ArrowLeft className="w-5 h-5 mr-2" />
            Previous
          </button>

          <div className="text-sm text-gray-500 dark:text-gray-400">
            Step {currentStep + 1} of {steps.length}
          </div>

          {currentStep === steps.length - 1 ? (
            <button
              onClick={handleFinish}
              className="inline-flex items-center px-8 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg font-medium hover:from-blue-700 hover:to-purple-700 transition-all shadow-lg hover:shadow-xl"
            >
              Go to Dashboard
              <Rocket className="w-5 h-5 ml-2" />
            </button>
          ) : (
            <button
              onClick={handleNext}
              className="inline-flex items-center px-6 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors"
            >
              Next
              <ArrowRight className="w-5 h-5 ml-2" />
            </button>
          )}
        </div>

        {/* Skip Button */}
        <div className="text-center mt-6">
          <button
            onClick={handleFinish}
            className="text-sm text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 underline"
          >
            Skip tutorial
          </button>
        </div>
      </div>
    </div>
  )
}