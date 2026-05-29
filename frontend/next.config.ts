import type { NextConfig } from "next";

import { withSentryConfig } from "@sentry/nextjs";

const nextConfig: NextConfig = {
  experimental: {
    authInterrupts: true,
  },
  async redirects() {
    return [
      {
        destination: "/favicon.svg",
        permanent: false,
        source: "/favicon.png",
      },
      {
        destination: "/favicon.svg",
        permanent: false,
        source: "/favicon.ico",
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
