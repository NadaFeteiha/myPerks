import { ClipboardCheck, FileText, Users } from "lucide-react";
import Link from "next/link";

import type { DepartmentBalanceItem } from "@/lib/api.server";
import { api } from "@/lib/api.server";

export const metadata = {
  title: "HR Dashboard — MyPerks",
};

export default async function AdminHomePage() {
  let employeeCount: null | number = null;
  let pendingCount: null | number = null;
  let departments: DepartmentBalanceItem[] = [];
  let balanceYear: number = new Date().getFullYear();
  let fetchError: null | string = null;

  try {
    const [employees, requests, balancesRes] = await Promise.all([
      api.getAdminEmployees(1, 1),
      api.getAdminRequests(1, 1, "pending"),
      api.getDepartmentBalances(),
    ]);
    employeeCount = employees.total;
    pendingCount = requests.total;
    departments = balancesRes.departments;
    balanceYear = balancesRes.year;
  } catch (error: unknown) {
    console.error("[MyPerks] GET /admin overview failed:", error);
    fetchError =
      error instanceof Error ? error.message : "Could not load HR overview.";
  }

  return (
    <div className="h-full overflow-y-auto">
      <div className="p-6 space-y-8">
        <div>
          <h1 className="text-xl font-semibold">HR Dashboard</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Overview of employees, pending requests, and department leave balances.
          </p>
        </div>

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
          <>
            {/* Stat cards */}
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

            {/* Department balance cards */}
            <section>
              <div className="mb-3 flex items-center justify-between">
                <div>
                  <h2 className="text-[13px] font-semibold text-foreground">
                    Department Leave Balances
                  </h2>
                  <p className="text-[11px] text-muted-foreground">
                    Current policy totals from <code>vacation_balances</code> — year {balanceYear}
                  </p>
                </div>
                <Link
                  href="/admin/documents"
                  className="text-[12px] font-medium text-brand-purple-600 hover:underline dark:text-brand-purple-400"
                >
                  Manage documents →
                </Link>
              </div>

              {departments.length === 0 ? (
                <div className="rounded-xl border border-dashed border-border p-8 text-center">
                  <FileText className="mx-auto mb-2 h-6 w-6 text-muted-foreground" />
                  <p className="text-[13px] font-medium text-foreground">
                    No leave balances found for {balanceYear}
                  </p>
                  <p className="mt-1 text-[12px] text-muted-foreground">
                    Upload and approve HR policy documents to set department balances.
                  </p>
                  <Link
                    href="/admin/documents"
                    className="mt-3 inline-block text-[12px] font-medium text-brand-purple-600 hover:underline dark:text-brand-purple-400"
                  >
                    Go to Documents →
                  </Link>
                </div>
              ) : (
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                  {departments.map((d) => (
                    <DepartmentBalanceCard key={d.department} item={d} />
                  ))}
                </div>
              )}
            </section>
          </>
        )}
      </div>
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
        <span className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
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

function DepartmentBalanceCard({ item }: { item: DepartmentBalanceItem }) {
  const rows: { label: string; value: null | number }[] = [
    { label: "Vacation", value: item.vacation_days },
    { label: "Sick leave", value: item.sick_days },
    { label: "PTO", value: item.pto_days },
  ];

  return (
    <div className="rounded-xl border border-border bg-white p-4 dark:bg-card">
      <div className="mb-3 flex items-center justify-between">
        <span className="text-[12px] font-semibold capitalize text-foreground">
          {item.department}
        </span>
        <span className="text-[10px] text-muted-foreground">
          {item.employee_count} {item.employee_count === 1 ? "employee" : "employees"}
        </span>
      </div>

      <div className="space-y-2">
        {rows.map(({ label, value }) => (
          <div key={label} className="flex items-center justify-between">
            <span className="text-[12px] text-muted-foreground">{label}</span>
            {value !== null && value !== undefined ? (
              <span className="text-[13px] font-semibold text-foreground">
                {value}{" "}
                <span className="font-normal text-muted-foreground">days</span>
              </span>
            ) : (
              <span className="text-[12px] text-muted-foreground">—</span>
            )}
          </div>
        ))}
      </div>

      <div className="mt-3 border-t border-border pt-3">
        <Link
          href="/admin/documents"
          className="text-[11px] font-medium text-brand-purple-600 hover:underline dark:text-brand-purple-400"
        >
          Update policy →
        </Link>
      </div>
    </div>
  );
}
