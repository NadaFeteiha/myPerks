import { RequestQueueClient } from "@/components/admin/request-queue-client";
import { Pagination } from "@/components/shared/pagination";
import { api } from "@/lib/api.server";
import { cn } from "@/lib/cn";

export const metadata = {
  title: "Request Queue — MyPerks",
};

const PAGE_SIZE = 10;

const STATUS_TABS = [
  { label: "Pending", value: "pending" },
  { label: "Approved", value: "approved" },
  { label: "Rejected", value: "rejected" },
  { label: "All", value: "all" },
];

export default async function AdminRequestsPage({
  searchParams,
}: {
  searchParams: Promise<{ page?: string; status?: string }>;
}) {
  const { page: pageParam, status } = await searchParams;
  const page = Math.max(1, parseInt(pageParam ?? "1", 10) || 1);
  const statusFilter = status ?? "pending";

  let data: Awaited<ReturnType<typeof api.getAdminRequests>> | null = null;
  let fetchError: null | string = null;

  try {
    data = await api.getAdminRequests(
      page,
      PAGE_SIZE,
      statusFilter === "all" ? "" : statusFilter,
    );
  } catch (error: unknown) {
    console.error("[MyPerks] GET /admin/requests failed:", error);
    fetchError =
      error instanceof Error ? error.message : "Could not load requests.";
  }

  const makeHref = (p: number) =>
    `?${new URLSearchParams({ page: String(p), status: statusFilter })}`;

  return (
    <div className="flex-1 overflow-y-auto p-6">
      <h1 className="mb-1 text-xl font-semibold">Request Queue</h1>
      <p className="mb-6 text-sm text-muted-foreground">
        Review and act on employee HR requests.
      </p>

      <div className="mb-4 flex gap-2">
        {STATUS_TABS.map((tab) => (
          <a
            className={cn(
              "rounded-full px-3 py-1.5 text-xs font-medium transition-colors",
              statusFilter === tab.value
                ? "bg-brand-purple-600 text-white"
                : "bg-muted text-muted-foreground hover:bg-muted/70",
            )}
            href={`?status=${tab.value}`}
            key={tab.value}
          >
            {tab.label}
          </a>
        ))}
      </div>

      {fetchError ? (
        <div className="flex flex-col items-center justify-center rounded-lg border border-dashed border-destructive/40 py-16 text-center">
          <p className="text-sm font-medium text-destructive">
            Failed to load requests
          </p>
          <p className="mt-1 text-xs text-muted-foreground">{fetchError}</p>
          <a
            className="mt-4 text-xs font-medium text-brand-purple-600 hover:underline dark:text-brand-purple-400"
            href="/admin/requests"
          >
            Try again
          </a>
        </div>
      ) : !data ? null : (
        <>
          <RequestQueueClient
            initialItems={data.items}
            removeOnAction={statusFilter === "pending"}
          />

          <Pagination
            makeHref={makeHref}
            page={page}
            pageSize={PAGE_SIZE}
            total={data.total}
          />
        </>
      )}
    </div>
  );
}
