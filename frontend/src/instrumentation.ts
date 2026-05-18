export async function register() {
  if (process.env.NEXT_RUNTIME === "nodejs" && process.env.SENTRY_AUTH_TOKEN) {
    const { init } = await import("@sentry/nextjs");
    init({ dsn: process.env.SENTRY_DSN });
  }
}
