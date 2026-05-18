export default async function HomePage() {
  const backend = await getBackendStatus();

  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-4 p-8">
      <h1 className="text-4xl font-bold">MyPerks</h1>
      <p className="text-muted-foreground">AI-powered HR assistant</p>
      <p className="text-sm text-muted-foreground">🚧 Coming soon</p>
      <div className="flex items-center gap-2 text-sm">
        <span
          className={`h-2 w-2 rounded-full ${backend ? "bg-green-500" : "bg-red-500"}`}
        />
        <span className="text-muted-foreground">
          {backend ? backend.message : "Backend unreachable"}
        </span>
      </div>
    </main>
  );
}

async function getBackendStatus() {
  try {
    const res = await fetch(
      process.env.NEXT_PUBLIC_API_URL ?? "https://myperks-backend.onrender.com",
      { next: { revalidate: 30 } },
    );
    if (!res.ok) return null;
    return (await res.json()) as { message: string };
  } catch {
    return null;
  }
}
