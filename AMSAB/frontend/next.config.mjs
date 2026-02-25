/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    // Ollama planning can take 30-60s; increase proxy timeout to 3 minutes
    proxyTimeout: 180_000,
  },
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "http://localhost:8088/api/:path*",
      },
      {
        source: "/ws/:path*",
        destination: "http://localhost:8088/ws/:path*",
      },
    ];
  },
};

export default nextConfig;
