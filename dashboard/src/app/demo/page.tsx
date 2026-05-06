'use client'

import Link from 'next/link'
import {
  UserPlus,
  LogIn,
  Database,
  Zap,
  Key,
  Code,
  CheckCircle,
  ArrowRight,
  Sparkles,
  Shield,
  Clock,
  Layers
} from 'lucide-react'

export default function DemoPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900">
      {/* Hero Section */}
      <div className="relative overflow-hidden">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24">
          <div className="text-center">
            <div className="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-r from-blue-600 to-purple-600 rounded-full mb-6">
              <Sparkles className="w-10 h-10 text-white" />
            </div>
            <h1 className="text-5xl md:text-6xl font-bold text-gray-900 dark:text-white mb-6">
              Welcome to <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-purple-600">Vernql</span>
            </h1>
            <p className="text-xl text-gray-600 dark:text-gray-400 max-w-3xl mx-auto mb-8">
              Transform natural language into SQL queries instantly with our powerful Text-to-SQL API.
              Built for developers, designed for simplicity.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link
                href="/signup"
                className="inline-flex items-center justify-center px-8 py-4 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg font-semibold hover:from-blue-700 hover:to-purple-700 transition-all shadow-lg hover:shadow-xl"
              >
                Get Started Free
                <ArrowRight className="w-5 h-5 ml-2" />
              </Link>
              <Link
                href="/login"
                className="inline-flex items-center justify-center px-8 py-4 border-2 border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg font-semibold hover:bg-gray-50 dark:hover:bg-gray-800 transition-all"
              >
                Sign In
                <LogIn className="w-5 h-5 ml-2" />
              </Link>
            </div>
          </div>
        </div>
      </div>

      {/* Features Section */}
      <div className="bg-white dark:bg-gray-800 py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-gray-900 dark:text-white mb-4">
              Why Choose Vernql?
            </h2>
            <p className="text-lg text-gray-600 dark:text-gray-400 max-w-2xl mx-auto">
              Powerful features that make Text-to-SQL conversion effortless
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {/* Feature 1 */}
            <div className="bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-900/30 dark:to-blue-800/30 rounded-xl p-6 border border-blue-200 dark:border-blue-700">
              <div className="w-12 h-12 bg-blue-600 rounded-lg flex items-center justify-center mb-4">
                <Zap className="w-6 h-6 text-white" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                Lightning Fast
              </h3>
              <p className="text-gray-600 dark:text-gray-400">
                Get SQL queries in milliseconds. Our AI-powered engine is optimized for speed and accuracy.
              </p>
            </div>

            {/* Feature 2 */}
            <div className="bg-gradient-to-br from-purple-50 to-purple-100 dark:from-purple-900/30 dark:to-purple-800/30 rounded-xl p-6 border border-purple-200 dark:border-purple-700">
              <div className="w-12 h-12 bg-purple-600 rounded-lg flex items-center justify-center mb-4">
                <Shield className="w-6 h-6 text-white" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                Secure & Reliable
              </h3>
              <p className="text-gray-600 dark:text-gray-400">
                Enterprise-grade security with API key authentication, rate limiting, and audit logs.
              </p>
            </div>

            {/* Feature 3 */}
            <div className="bg-gradient-to-br from-green-50 to-green-100 dark:from-green-900/30 dark:to-green-800/30 rounded-xl p-6 border border-green-200 dark:border-green-700">
              <div className="w-12 h-12 bg-green-600 rounded-lg flex items-center justify-center mb-4">
                <Database className="w-6 h-6 text-white" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                Schema-Aware
              </h3>
              <p className="text-gray-600 dark:text-gray-400">
                Upload your database schema and get context-aware SQL queries tailored to your structure.
              </p>
            </div>

            {/* Feature 4 */}
            <div className="bg-gradient-to-br from-yellow-50 to-yellow-100 dark:from-yellow-900/30 dark:to-yellow-800/30 rounded-xl p-6 border border-yellow-200 dark:border-yellow-700">
              <div className="w-12 h-12 bg-yellow-600 rounded-lg flex items-center justify-center mb-4">
                <Code className="w-6 h-6 text-white" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                Easy Integration
              </h3>
              <p className="text-gray-600 dark:text-gray-400">
                Simple REST API with SDKs for Python, JavaScript, and more. Start coding in minutes.
              </p>
            </div>

            {/* Feature 5 */}
            <div className="bg-gradient-to-br from-red-50 to-red-100 dark:from-red-900/30 dark:to-red-800/30 rounded-xl p-6 border border-red-200 dark:border-red-700">
              <div className="w-12 h-12 bg-red-600 rounded-lg flex items-center justify-center mb-4">
                <Clock className="w-6 h-6 text-white" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                Real-time Testing
              </h3>
              <p className="text-gray-600 dark:text-gray-400">
                Test queries instantly in our dashboard before integrating into your application.
              </p>
            </div>

            {/* Feature 6 */}
            <div className="bg-gradient-to-br from-indigo-50 to-indigo-100 dark:from-indigo-900/30 dark:to-indigo-800/30 rounded-xl p-6 border border-indigo-200 dark:border-indigo-700">
              <div className="w-12 h-12 bg-indigo-600 rounded-lg flex items-center justify-center mb-4">
                <Layers className="w-6 h-6 text-white" />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                AI Enrichment
              </h3>
              <p className="text-gray-600 dark:text-gray-400">
                Automatically generate descriptions for your schema to improve query accuracy.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Getting Started Flow */}
      <div className="py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-gray-900 dark:text-white mb-4">
              Get Started in 4 Simple Steps
            </h2>
            <p className="text-lg text-gray-600 dark:text-gray-400 max-w-2xl mx-auto">
              From signup to your first API call in minutes
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {/* Step 1 */}
            <div className="relative">
              <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 border border-gray-200 dark:border-gray-700 hover:shadow-xl transition-shadow">
                <div className="w-12 h-12 bg-gradient-to-r from-blue-600 to-blue-700 rounded-full flex items-center justify-center mb-4 text-white font-bold text-xl">
                  1
                </div>
                <div className="mb-4">
                  <UserPlus className="w-8 h-8 text-blue-600 dark:text-blue-400" />
                </div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                  Create Account
                </h3>
                <p className="text-gray-600 dark:text-gray-400 text-sm mb-4">
                  Sign up with your email and create your company account. No credit card required.
                </p>
                <Link
                  href="/signup"
                  className="text-blue-600 dark:text-blue-400 text-sm font-medium hover:underline inline-flex items-center"
                >
                  Sign up now
                  <ArrowRight className="w-4 h-4 ml-1" />
                </Link>
              </div>
              <div className="hidden lg:block absolute top-1/2 -right-4 w-8 h-0.5 bg-gradient-to-r from-blue-600 to-purple-600"></div>
            </div>

            {/* Step 2 */}
            <div className="relative">
              <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 border border-gray-200 dark:border-gray-700 hover:shadow-xl transition-shadow">
                <div className="w-12 h-12 bg-gradient-to-r from-purple-600 to-purple-700 rounded-full flex items-center justify-center mb-4 text-white font-bold text-xl">
                  2
                </div>
                <div className="mb-4">
                  <Database className="w-8 h-8 text-purple-600 dark:text-purple-400" />
                </div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                  Upload Schema
                </h3>
                <p className="text-gray-600 dark:text-gray-400 text-sm mb-4">
                  Upload your database schema in SQL DDL or JSON format. AI enrichment optional.
                </p>
                <span className="text-purple-600 dark:text-purple-400 text-sm font-medium">
                  Step 2
                </span>
              </div>
              <div className="hidden lg:block absolute top-1/2 -right-4 w-8 h-0.5 bg-gradient-to-r from-purple-600 to-green-600"></div>
            </div>

            {/* Step 3 */}
            <div className="relative">
              <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 border border-gray-200 dark:border-gray-700 hover:shadow-xl transition-shadow">
                <div className="w-12 h-12 bg-gradient-to-r from-green-600 to-green-700 rounded-full flex items-center justify-center mb-4 text-white font-bold text-xl">
                  3
                </div>
                <div className="mb-4">
                  <Key className="w-8 h-8 text-green-600 dark:text-green-400" />
                </div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                  Generate API Key
                </h3>
                <p className="text-gray-600 dark:text-gray-400 text-sm mb-4">
                  Create secure API keys for your applications with custom rate limits.
                </p>
                <span className="text-green-600 dark:text-green-400 text-sm font-medium">
                  Step 3
                </span>
              </div>
              <div className="hidden lg:block absolute top-1/2 -right-4 w-8 h-0.5 bg-gradient-to-r from-green-600 to-yellow-600"></div>
            </div>

            {/* Step 4 */}
            <div className="relative">
              <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 border border-gray-200 dark:border-gray-700 hover:shadow-xl transition-shadow">
                <div className="w-12 h-12 bg-gradient-to-r from-yellow-600 to-yellow-700 rounded-full flex items-center justify-center mb-4 text-white font-bold text-xl">
                  4
                </div>
                <div className="mb-4">
                  <Code className="w-8 h-8 text-yellow-600 dark:text-yellow-400" />
                </div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                  Start Building
                </h3>
                <p className="text-gray-600 dark:text-gray-400 text-sm mb-4">
                  Integrate our API into your application and start converting queries.
                </p>
                <span className="text-yellow-600 dark:text-yellow-400 text-sm font-medium">
                  Step 4
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Code Example Section */}
      <div className="bg-gray-900 py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-4xl font-bold text-white mb-4">
              Simple API Integration
            </h2>
            <p className="text-lg text-gray-400 max-w-2xl mx-auto">
              Clean, intuitive API that gets you up and running in minutes
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Python Example */}
            <div className="bg-gray-800 rounded-xl overflow-hidden border border-gray-700">
              <div className="bg-gray-700 px-6 py-3 border-b border-gray-600">
                <span className="text-sm font-medium text-gray-300">Python</span>
              </div>
              <pre className="p-6 overflow-x-auto text-sm">
                <code className="text-gray-300">
{`import requests

# Your API configuration
API_KEY = "your_api_key_here"
BASE_URL = "https://api.vernql.com"

# Convert natural language to SQL
response = requests.post(
    f"{BASE_URL}/v1/queries",
    headers={"X-API-Key": API_KEY},
    json={
        "schema_id": "your-schema-id",
        "question": "Show top 10 customers"
    }
)

result = response.json()
print(result["sql_query"])`}
                </code>
              </pre>
            </div>

            {/* JavaScript Example */}
            <div className="bg-gray-800 rounded-xl overflow-hidden border border-gray-700">
              <div className="bg-gray-700 px-6 py-3 border-b border-gray-600">
                <span className="text-sm font-medium text-gray-300">JavaScript</span>
              </div>
              <pre className="p-6 overflow-x-auto text-sm">
                <code className="text-gray-300">
{`// Your API configuration
const API_KEY = "your_api_key_here";
const BASE_URL = "https://api.vernql.com";

// Convert natural language to SQL
const response = await fetch(
  \`\${BASE_URL}/v1/queries\`,
  {
    method: "POST",
    headers: {
      "X-API-Key": API_KEY,
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      schema_id: "your-schema-id",
      question: "Show top 10 customers"
    })
  }
);

const result = await response.json();
console.log(result.sql_query);`}
                </code>
              </pre>
            </div>
          </div>
        </div>
      </div>

      {/* Use Cases Section */}
      <div className="bg-white dark:bg-gray-800 py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-gray-900 dark:text-white mb-4">
              Perfect For
            </h2>
            <p className="text-lg text-gray-600 dark:text-gray-400 max-w-2xl mx-auto">
              Vernql powers a wide variety of applications and use cases
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="text-center">
              <div className="w-16 h-16 bg-blue-100 dark:bg-blue-900/30 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-3xl">📊</span>
              </div>
              <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                Business Intelligence
              </h3>
              <p className="text-gray-600 dark:text-gray-400">
                Enable non-technical users to query data using natural language
              </p>
            </div>

            <div className="text-center">
              <div className="w-16 h-16 bg-purple-100 dark:bg-purple-900/30 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-3xl">🤖</span>
              </div>
              <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                AI Chatbots
              </h3>
              <p className="text-gray-600 dark:text-gray-400">
                Power conversational interfaces with database query capabilities
              </p>
            </div>

            <div className="text-center">
              <div className="w-16 h-16 bg-green-100 dark:bg-green-900/30 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-3xl">📱</span>
              </div>
              <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                SaaS Applications
              </h3>
              <p className="text-gray-600 dark:text-gray-400">
                Add natural language search and reporting to your product
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* CTA Section */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 py-20">
        <div className="max-w-4xl mx-auto text-center px-4">
          <h2 className="text-4xl md:text-5xl font-bold text-white mb-6">
            Ready to Get Started?
          </h2>
          <p className="text-xl text-blue-100 mb-8 max-w-2xl mx-auto">
            Join developers who are already building amazing applications with Vernql's Text-to-SQL API
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              href="/signup"
              className="inline-flex items-center justify-center px-8 py-4 bg-white text-blue-600 rounded-lg font-semibold hover:bg-gray-100 transition-all shadow-lg hover:shadow-xl"
            >
              Create Free Account
              <ArrowRight className="w-5 h-5 ml-2" />
            </Link>
            <Link
              href="/dashboard/integrations"
              className="inline-flex items-center justify-center px-8 py-4 border-2 border-white text-white rounded-lg font-semibold hover:bg-white hover:text-blue-600 transition-all"
            >
              View Documentation
              <Code className="w-5 h-5 ml-2" />
            </Link>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="bg-gray-900 py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center text-gray-400">
            <p className="mb-4">
              &copy; 2026 Vernql. All rights reserved.
            </p>
            <div className="flex justify-center gap-6 text-sm">
              <Link href="/demo" className="hover:text-white transition-colors">
                Demo
              </Link>
              <Link href="/dashboard" className="hover:text-white transition-colors">
                Dashboard
              </Link>
              <Link href="/login" className="hover:text-white transition-colors">
                Login
              </Link>
              <Link href="/signup" className="hover:text-white transition-colors">
                Sign Up
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}