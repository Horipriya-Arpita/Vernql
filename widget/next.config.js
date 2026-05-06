/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  reactStrictMode: true,
  // Allow embedding in iframes from any domain
  async headers() {
    return [
      {
        source: '/:path*',
        headers: [
          // X-Frame-Options does not support "allow from any domain".
          // CSP frame-ancestors covers that case for all modern browsers.
          {
            key: 'Content-Security-Policy',
            value: "frame-ancestors *",
          },
        ],
      },
    ]
  },
}

module.exports = nextConfig
