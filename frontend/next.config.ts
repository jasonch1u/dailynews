import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Allow LAN access during development without cross-origin warnings for /_next/*
  allowedDevOrigins: ["*.*.*.*", "*.localhost", "localhost"],
  // Proxy API calls to the Python backend in development
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: process.env.NODE_ENV === 'development'
          ? 'http://localhost:8000/api/:path*'
          : '/api/:path*',
      },
    ];
  },
};

export default nextConfig;
