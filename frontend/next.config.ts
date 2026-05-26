import type { NextConfig } from "next";

import { withSentryConfig } from "@sentry/nextjs";

const nextConfig: NextConfig = {
  experimental: {
    authInterrupts: true,
  },
  async rewrites() {
    const backendUrl = process.env.BACKEND_URL ?? "http://localhost:8000";
    return [
      {
        destination: `${backendUrl}/:path*`,
        source: "/api/backend/:path*",
      },
    ];
  },
};

const sentryOrg = process.env.SENTRY_ORG;
const sentryProject = process.env.SENTRY_PROJECT;
const sentryAuthToken = process.env.SENTRY_AUTH_TOKEN;

const config =
  !sentryOrg || !sentryProject || !sentryAuthToken
    ? nextConfig
    : withSentryConfig(nextConfig, {
        authToken: sentryAuthToken,
        org: sentryOrg,
        project: sentryProject,
        silent: !process.env.CI,
        webpack: {
          automaticVercelMonitors: true,
          treeshake: {
            removeDebugLogging: true,
          },
        },
        widenClientFileUpload: true,
      });

export default config;
