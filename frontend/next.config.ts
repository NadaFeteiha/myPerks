import type { NextConfig } from "next";

import { withSentryConfig } from "@sentry/nextjs";
import path from "path";

const nextConfig: NextConfig = {
  experimental: {
    authInterrupts: true,
  },
  reactCompiler: true,
  turbopack: {
    root: path.resolve(__dirname),
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
