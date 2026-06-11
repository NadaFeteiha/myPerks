import { Pagination } from "@/components/shared/pagination";
import { StatusBadge } from "@/components/shared/status-badge";
import { api, type RequestHistoryItem } from "@/lib/api.server";
import {
  formatRequestType,
  getRequestDate,
  getRequestDescription,
} from "@/lib/format";

export const metadata = {
  title: "Request History — MyPerks",
};

const PAGE_SIZE = 10;

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------
export default async function RequestsPage({
  searchParams,
}: {
  searchParams: Promise<{ page?: string }>;
}) {
  const { page: pageParam } = await searchParams;
  const page = Math.max(1, parseInt(pageParam ?? "1", 10) || 1);

  let data: Awaited<ReturnType<typeof api.getRequestHistory>> | null = null;
  let fetchError: null | string = null;

  try {
    data = await api.getRequestHistory(page, PAGE_SIZE);
  } catch (error: unknown) {
    console.error("[MyPerks] GET /me/requests failed:", error);
    fetchError =
      error instanceof Error ? error.message : "Could not load your requests.";
  }

  return (
    <div className="flex-1 overflow-y-auto p-6">
      <h1 className="mb-1 text-xl font-semibold">Request History</h1>
      <p className="mb-6 text-sm text-muted-foreground">
        A record of your submitted HR requests.
      </p>

      <p className="mb-3 text-[10px] font-semibold uppercase tracking-[0.07em] text-muted-foreground">
        Requests
      </p>

      {fetchError ? (
        <div className="flex flex-col items-center justify-center rounded-lg border border-dashed border-destructive/40 py-16 text-center">
          <p className="text-sm font-medium text-destructive">
            Failed to load requests
          </p>
          <p className="mt-1 text-xs text-muted-foreground">{fetchError}</p>
          <a
            className="mt-4 text-xs font-medium text-brand-purple-600 hover:underline dark:text-brand-purple-400"
            href="/requests"
          >
            Try again
          </a>
        </div>
      ) : !data || data.items.length === 0 ? (
        <EmptyState />
      ) : (
        <>
          <div className="overflow-x-auto rounded-lg border border-border">
            <table className="w-full">
              <thead>
                <tr className="border-b border-border bg-muted/40">
                  <th className="py-3 pr-4 text-center text-[10px] font-semibold uppercase tracking-[0.07em] text-muted-foreground">
                    Type
                  </th>
                  <th className="py-3 pr-4 text-center text-[10px] font-semibold uppercase tracking-[0.07em] text-muted-foreground">
                    Status
                  </th>
                  <th className="py-3 pr-4 text-center text-[10px] font-semibold uppercase tracking-[0.07em] text-muted-foreground">
                    Dates
                  </th>
                  <th className="py-3 text-center text-[10px] font-semibold uppercase tracking-[0.07em] text-muted-foreground">
                    Description
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border px-4">
                {data.items.map((item) => (
                  <RequestRow item={item} key={item.id} />
                ))}
              </tbody>
            </table>
          </div>

          <Pagination
            makeHref={(p) => `?page=${p}`}
            page={page}
            pageSize={PAGE_SIZE}
            total={data.total}
          />
        </>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Empty state
// ---------------------------------------------------------------------------
function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center rounded-lg border border-dashed border-border py-16 text-center">
      <p className="text-sm font-medium">No requests yet</p>
      <p className="mt-1 text-xs text-muted-foreground">
        Your submitted HR requests will appear here.
      </p>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Table row
// ---------------------------------------------------------------------------
function RequestRow({ item }: { item: RequestHistoryItem }) {
  return (
    <tr className="border-b border-border last:border-0">
      <td className="py-3 pr-4 text-sm text-center font-medium">
        {formatRequestType(item.type)}
      </td>
      <td className="py-3 pr-4 text-center">
        <StatusBadge status={item.status} />
      </td>
      <td className="py-3 pr-4 text-sm text-center text-muted-foreground">
        {getRequestDate(item)}
      </td>
      <td className="py-3 text-sm text-center text-muted-foreground">
        {getRequestDescription(item.body)}
      </td>
    </tr>
  );
}
