import type { NextConfig } from "next";

const backendUrl = (process.env.API_URL ?? "http://localhost:8000").replace(/\/$/, "");
const vacationUrl = (process.env.VACATION_API_URL ?? backendUrl).replace(/\/$/, "");

const nextConfig: NextConfig = {
  output: "standalone",
  poweredByHeader: false,
  async rewrites() {
    return [
      {
        source: "/api/vacation-mode",
        destination: `${vacationUrl}/vacation-mode`,
      },
      {
        source: "/api/vacation-mode/plan-only",
        destination: `${vacationUrl}/vacation-mode/plan-only`,
      },
      {
        source: "/api/:path*",
        destination: `${backendUrl}/api/:path*`,
      },
      {
        source: "/health",
        destination: `${backendUrl}/health`,
      },
    ];
  },
};

export default nextConfig;
