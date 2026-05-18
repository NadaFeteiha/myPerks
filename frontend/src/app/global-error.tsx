"use client";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <html lang="en">
      <body className="flex min-h-screen items-center justify-center">
        <div className="text-center">
          <h2 className="mb-2 text-xl font-semibold">Something went wrong</h2>
          <p className="mb-4 text-muted-foreground">{error.message}</p>
          <button
            className="rounded bg-primary px-4 py-2 text-primary-foreground"
            onClick={reset}
          >
            Try again
          </button>
        </div>
      </body>
    </html>
  );
}
