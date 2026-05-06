import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

// Routes that require authentication
const protectedRoutes = [
  '/dashboard',
  '/onboarding',
]

// Routes that should redirect to dashboard if already authenticated
const authRoutes = [
  '/login',
  '/signup',
]

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl

  // Get tokens from cookies or localStorage (note: middleware can only access cookies)
  const accessToken = request.cookies.get('access_token')?.value
  const apiKey = request.cookies.get('textsql_api_key')?.value

  // Check if user is authenticated (has either JWT token or API key)
  const isAuthenticated = !!(accessToken || apiKey)

  // Check if trying to access protected route
  const isProtectedRoute = protectedRoutes.some(route => pathname.startsWith(route))

  // Check if trying to access auth route (login/signup)
  const isAuthRoute = authRoutes.some(route => pathname.startsWith(route))

  // Redirect unauthenticated users trying to access protected routes
  if (isProtectedRoute && !isAuthenticated) {
    const loginUrl = new URL('/login', request.url)
    loginUrl.searchParams.set('redirect', pathname)
    return NextResponse.redirect(loginUrl)
  }

  // Redirect authenticated users away from auth pages
  if (isAuthRoute && isAuthenticated) {
    return NextResponse.redirect(new URL('/dashboard', request.url))
  }

  return NextResponse.next()
}

// Configure which routes to run middleware on
export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - api (API routes)
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - public folder
     */
    '/((?!api|_next/static|_next/image|favicon.ico|.*\\..*|public).*)',
  ],
}