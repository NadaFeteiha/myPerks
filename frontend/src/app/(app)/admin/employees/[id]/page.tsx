import { ArrowLeft } from "lucide-react";
import Link from "next/link";
import { notFound } from "next/navigation";

import { EditEmployeeDialog } from "@/components/admin/edit-employee-dialog";
import { StatusBadge } from "@/components/shared/status-badge";
import { api } from "@/lib/api.server";
import {
  formatDepartment,
  formatIsoDate,
  formatRequestType,
  getRequestDate,
  getRequestDescription,
} from "@/lib/format";

export const metadata = {
  title: "Employee — MyPerks",
};

export default async function AdminEmployeeDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const employeeId = Number(id);
  if (!Number.isInteger(employeeId)) notFound();

  let employee: Awaited<ReturnType<typeof api.getAdminEmployeeDetail>> | null =
    null;
  let fetchError: null | string = null;

  try {
    employee = await api.getAdminEmployeeDetail(employeeId);
  } catch (error: unknown) {
    if (error instanceof Error && error.message.includes("404")) notFound();
    console.error("[MyPerks] GET /admin/employees/:id failed:", error);
    fetchError =
      error instanceof Error ? error.message : "Could not load employee.";
  }

  return (
    <div className="flex-1 overflow-y-auto p-6">
      <Link
        className="mb-4 inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
        href="/admin/employees"
      >
        <ArrowLeft className="h-3.5 w-3.5" />
        Back to employees
      </Link>

      {fetchError || !employee ? (
        <div className="flex flex-col items-center justify-center rounded-lg border border-dashed border-destructive/40 py-16 text-center">
          <p className="text-sm font-medium text-destructive">
            Failed to load employee
          </p>
          <p className="mt-1 text-xs text-muted-foreground">{fetchError}</p>
        </div>
      ) : (
        <>
          <div className="mb-6 flex items-start justify-between">
            <div>
              <h1 className="text-xl font-semibold">{employee.name}</h1>
              <p className="mt-1 text-sm text-muted-foreground">
                {employee.email} · {formatDepartment(employee.department)} ·{" "}
                {employee.role === "hr_admin" ? "HR Admin" : "Employee"}
              </p>
              <p className="mt-1 text-xs text-muted-foreground">
                Joined {formatIsoDate(employee.joined_date)} · Benefits year
                resets {formatIsoDate(employee.benefits_year_reset)} ·{" "}
                {employee.linked ? "Linked to Clerk" : "Not yet linked"}
              </p>
            </div>
            <EditEmployeeDialog
              currentDepartment={employee.department}
              currentRole={employee.role}
              employeeId={employee.id}
              employeeName={employee.name}
            />
          </div>
          <p className="mb-3 mt-6 text-[10px] font-semibold uppercase tracking-[0.07em] text-muted-foreground">
            Leave balances
          </p>
          {employee.balances.length === 0 ? (
            <p className="text-sm text-muted-foreground">No balances yet.</p>
          ) : (
            <div className="grid gap-3 sm:grid-cols-3">
              {employee.balances.map((balance) => (
                <div
                  className="rounded-xl border border-border bg-white p-4 dark:bg-card"
                  key={balance.leave_type}
                >
                  <p className="text-[11px] font-semibold uppercase tracking-[0.05em] text-muted-foreground">
                    {formatRequestType(balance.leave_type)}
                  </p>
                  <p className="mt-1 text-[20px] font-bold leading-none tracking-tight text-foreground">
                    {balance.remaining_days}{" "}
                    <span className="text-[12px] font-normal text-muted-foreground">
                      / {balance.total_days} days left
                    </span>
                  </p>
                  <p className="mt-1 text-[11px] text-muted-foreground">
                    {balance.used_days} days used
                  </p>
                </div>
              ))}
            </div>
          )}

          <p className="mb-3 mt-6 text-[10px] font-semibold uppercase tracking-[0.07em] text-muted-foreground">
            Request history
          </p>
          {employee.request_history.length === 0 ? (
            <p className="text-sm text-muted-foreground">No requests yet.</p>
          ) : (
            <div className="overflow-x-auto rounded-lg border border-border">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-border bg-muted/40">
                    <th className="py-3 pl-4 pr-4 text-center text-[10px] font-semibold uppercase tracking-[0.07em] text-muted-foreground">
                      Type
                    </th>
                    <th className="py-3 pr-4 text-center text-[10px] font-semibold uppercase tracking-[0.07em] text-muted-foreground">
                      Status
                    </th>
                    <th className="py-3 pr-4 text-center text-[10px] font-semibold uppercase tracking-[0.07em] text-muted-foreground">
                      Dates
                    </th>
                    <th className="py-3 pr-4 text-center text-[10px] font-semibold uppercase tracking-[0.07em] text-muted-foreground">
                      Description
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {employee.request_history.map((item) => (
                    <tr
                      className="border-b border-border last:border-0"
                      key={item.id}
                    >
                      <td className="py-3 pl-4 pr-4 text-center text-sm font-medium">
                        {formatRequestType(item.type)}
                      </td>
                      <td className="py-3 pr-4 text-center">
                        <StatusBadge status={item.status} />
                      </td>
                      <td className="py-3 pr-4 text-center text-sm text-muted-foreground">
                        {getRequestDate(item)}
                      </td>
                      <td className="py-3 pr-4 text-center text-sm text-muted-foreground">
                        {getRequestDescription(item.body)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}
    </div>
  );
}
