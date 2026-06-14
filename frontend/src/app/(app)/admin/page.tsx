import { ClipboardCheck, Users } from "lucide-react";
import Link from "next/link";

import { api } from "@/lib/api.server";

export const metadata = {
  title: "HR Dashboard — MyPerks",
};

export default async function AdminHomePage() {
  let employeeCount: null | number = null;
  let pendingCount: null | number = null;
  let fetchError: null | string = null;

  try {
    const [employees, requests] = await Promise.all([
      api.getAdminEmployees(1, 1),
      api.getAdminRequests(1, 1, "pending"),
    ]);
    employeeCount = employees.total;
    pendingCount = requests.total;
  } catch (error: unknown) {
    console.error("[MyPerks] GET /admin overview failed:", error);
    fetchError =
      error instanceof Error ? error.message : "Could not load HR overview.";
  }

  return (
    <div className="p-6">
      <h1 className="text-xl font-semibold">HR Dashboard</h1>
      <p className="mb-6 mt-1 text-sm text-muted-foreground">
        Overview of employees and pending requests.
      </p>

      {fetchError ? (
        <div className="flex flex-col items-center justify-center rounded-lg border border-dashed border-destructive/40 py-16 text-center">
          <p className="text-sm font-medium text-destructive">
            Failed to load HR overview
          </p>
          <p className="mt-1 text-xs text-muted-foreground">{fetchError}</p>
          <a
            className="mt-4 text-xs font-medium text-brand-purple-600 hover:underline dark:text-brand-purple-400"
            href="/admin"
          >
            Try again
          </a>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2">
          <StatCard
            count={employeeCount}
            href="/admin/employees"
            icon={<Users className="h-5 w-5" />}
            label="Employees"
            linkLabel="View employee list"
          />
          <StatCard
            count={pendingCount}
            href="/admin/requests"
            icon={<ClipboardCheck className="h-5 w-5" />}
            label="Pending requests"
            linkLabel="Open request queue"
          />
        </div>
      )}
    </div>
  );
}

function StatCard({
  count,
  href,
  icon,
  label,
  linkLabel,
}: {
  count: null | number;
  href: string;
  icon: React.ReactNode;
  label: string;
  linkLabel: string;
}) {
  return (
    <Link
      className="rounded-xl border border-border bg-white p-4 transition-colors hover:border-brand-purple-300 dark:bg-card"
      href={href}
    >
      <div className="mb-2.5 flex items-center justify-between">
        <span className="text-[11px] font-semibold uppercase tracking-[0.05em] text-muted-foreground">
          {label}
        </span>
        <span className="text-brand-purple-600 dark:text-brand-purple-400">
          {icon}
        </span>
      </div>
      <p className="text-[28px] font-bold leading-none tracking-tight text-foreground">
        {count ?? "—"}
      </p>
      <p className="mt-3 text-[12px] font-medium text-brand-purple-600 dark:text-brand-purple-400">
        {linkLabel} →
      </p>
    </Link>
  );
}
