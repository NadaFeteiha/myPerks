export function ChartSkeleton() {
  return (
    <div className="rounded-xl border border-border bg-white p-4 dark:bg-card">
      <div className="mb-3 h-2.5 w-24 animate-pulse rounded-full bg-muted" />
      <div className="flex h-48 items-end justify-around gap-2 pt-4">
        {[60, 90, 45, 75, 55, 80].map((h, i) => (
          <div
            className="w-full animate-pulse rounded-t bg-muted"
            key={i}
            style={{ height: `${h}%` }}
          />
        ))}
      </div>
    </div>
  );
}

export function ChartsSectionSkeleton() {
  return (
    <div className="mb-5 grid grid-cols-2 gap-2.5">
      <ChartSkeleton />
      <ChartSkeleton />
    </div>
  );
}
