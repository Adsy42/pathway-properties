/** @type {import('next').NextConfig} */
const nextConfig = {
  images: {
    domains: ['images.domain.com.au', 'i2.au.reastatic.net', 'rimh2.domainstatic.com.au'],
  },
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/api/:path*',
      },
    ]
  },
}

module.exports = nextConfig







