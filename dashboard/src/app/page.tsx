import Link from 'next/link'

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-16">
        <div className="max-w-4xl mx-auto text-center">
          {/* Hero Section */}
          <h1 className="text-5xl font-bold text-gray-900 mb-6">
            TextSQL Dashboard
          </h1>
          <p className="text-xl text-gray-600 mb-12">
            Convert natural language questions to SQL queries with AI-powered generation
          </p>

          {/* Features */}
          <div className="grid md:grid-cols-3 gap-8 mb-12">
            <FeatureCard
              title="Schema Management"
              description="Upload and manage database schemas with AI enrichment"
              icon="📊"
            />
            <FeatureCard
              title="SQL Generation"
              description="Convert natural language to accurate SQL queries"
              icon="⚡"
            />
            <FeatureCard
              title="Integration"
              description="Get code snippets for multiple languages and frameworks"
              icon="🔗"
            />
          </div>

          {/* CTA */}
          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
            <Link
              href="/signup"
              className="inline-block px-8 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium shadow-lg hover:shadow-xl"
            >
              Get Started Free
            </Link>
            <Link
              href="/login"
              className="inline-block px-8 py-3 bg-white text-blue-600 rounded-lg hover:bg-gray-50 transition-colors font-medium border-2 border-blue-600"
            >
              Sign In
            </Link>
            <Link
              href="/demo"
              className="inline-block px-8 py-3 text-gray-600 hover:text-gray-900 transition-colors font-medium underline"
            >
              View Demo & Docs
            </Link>
          </div>

          {/* Status */}
          <div className="mt-16 pt-8 border-t border-gray-200">
            <p className="text-sm text-gray-500">
              API Status: <span className="text-green-600 font-medium">● Online</span>
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

function FeatureCard({
  title,
  description,
  icon,
}: {
  title: string
  description: string
  icon: string
}) {
  return (
    <div className="bg-white p-6 rounded-xl shadow-sm hover:shadow-md transition-shadow">
      <div className="text-4xl mb-4">{icon}</div>
      <h3 className="text-lg font-semibold text-gray-900 mb-2">{title}</h3>
      <p className="text-gray-600 text-sm">{description}</p>
    </div>
  )
}
