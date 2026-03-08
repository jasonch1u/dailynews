import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Allow LAN access during development without cross-origin warnings
  allowedDevOrigins: ["*.*.*.*", "*.localhost", "localhost"],
};

export default nextConfig;
