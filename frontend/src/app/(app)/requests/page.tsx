import { api, type RequestHistoryItem } from "@/lib/api.server";
import { formatIsoDate } from "@/lib/format";

export const metadata = {
  title: "Request History — MyPerks",
};

const PAGE_SIZE = 10;

function formatType(type: string): string {
  if (type.toLowerCase() === "pto") return "PTO";
  return type.charAt(0).toUpperCase() + type.slice(1);
}

/**
 * For leave requests, return "Jun 6 – Jun 12, 2026" using start/end from body.
 * For reimbursements (no start_date), fall back to the submission date.
 */
function getRequestDate(item: RequestHistoryItem): string {
  if (item.body) {
    try {
      const parsed = JSON.parse(item.body) as Record<string, unknown>;
      if (typeof parsed.start_date === "string") {
        const start = formatIsoDate(parsed.start_date);
        if (typeof parsed.end_date === "string") {
          const end = formatIsoDate(parsed.end_date);
          return start === end ? start : `${start} – ${end}`;
        }
        return start;
      }
    } catch {
      // fall through
    }
  }
  return formatIsoDate(item.created_at);
}

function getShortDescription(body: null | string): string {
  if (!body) return "—";
  try {
    const parsed = JSON.parse(body) as Record<string, unknown>;
    const text = parsed.reason ?? parsed.description;
    return typeof text === "string" ? text : "—";
  } catch {
    return "—";
  }
}

const STATUS_STYLES = new Map([
  ["approved", "bg-green-100 text-green-800"],
  ["cancelled", "bg-muted text-muted-foreground"],
  ["pending", "bg-yellow-100 text-yellow-800"],
  ["rejected", "bg-red-100 text-red-800"],
]);

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

          <Pagination page={page} pageSize={PAGE_SIZE} total={data.total} />
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
// Pagination
// ---------------------------------------------------------------------------
function Pagination({
  page,
  pageSize,
  total,
}: {
  page: number;
  pageSize: number;
  total: number;
}) {
  const totalPages = Math.ceil(total / pageSize);
  if (totalPages <= 1) return null;

  return (
    <div className="mt-4 flex items-center justify-between text-sm">
      <p className="text-muted-foreground">
        Page {page} of {totalPages}
      </p>
      <div className="flex gap-2">
        {page > 1 && (
          <a
            className="rounded-md border border-border px-3 py-1.5 text-sm font-medium hover:bg-muted"
            href={`?page=${page - 1}`}
          >
            Previous
          </a>
        )}
        {page < totalPages && (
          <a
            className="rounded-md border border-border px-3 py-1.5 text-sm font-medium hover:bg-muted"
            href={`?page=${page + 1}`}
          >
            Next
          </a>
        )}
      </div>
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
        {formatType(item.type)}
      </td>
      <td className="py-3 pr-4 text-center">
        <StatusBadge status={item.status} />
      </td>
      <td className="py-3 pr-4 text-sm text-center text-muted-foreground">
        {getRequestDate(item)}
      </td>
      <td className="py-3 text-sm text-center text-muted-foreground">
        {getShortDescription(item.body)}
      </td>
    </tr>
  );
}

// ---------------------------------------------------------------------------
// Status badge
// ---------------------------------------------------------------------------
function StatusBadge({ status }: { status: string }) {
  const classes = STATUS_STYLES.get(status) ?? "bg-muted text-muted-foreground";
  return (
    <span
      className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium capitalize ${classes}`}
    >
      {status}
    </span>
  );
}
