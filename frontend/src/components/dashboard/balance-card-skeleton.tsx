export function BalanceCardSkeleton() {
    return (
        <div className="rounded-xl border border-border bg-white p-4 dark:bg-card">
            <div className="mb-2.5 flex items-center justify-between">
                <div className="h-2.5 w-16 animate-pulse rounded-full bg-muted" />
                <div className="h-4 w-4 animate-pulse rounded bg-muted" />
            </div>
            <div className="h-8 w-20 animate-pulse rounded-md bg-muted" />
            <div className="mt-1.5 h-2 w-28 animate-pulse rounded-full bg-muted" />
            <div className="mt-3 h-1 overflow-hidden rounded-full bg-surface-3">
                <div className="h-full w-1/2 animate-pulse rounded-full bg-muted" />
            </div>
        </div>
    )
}

export function BalanceCardsSkeleton() {
    return (
        <div className="mb-5 grid grid-cols-3 gap-2.5">
            <BalanceCardSkeleton />
            <BalanceCardSkeleton />
            <BalanceCardSkeleton />
        </div>
    )
}
