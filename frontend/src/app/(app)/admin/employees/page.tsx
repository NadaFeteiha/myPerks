import Link from "next/link";

import { EmployeeSearch } from "@/components/admin/employee-search";
import { PreCreateEmployeeDialog } from "@/components/admin/pre-create-employee-dialog";
import { Pagination } from "@/components/shared/pagination";
import { type AdminEmployeeListItem, api } from "@/lib/api.server";
import { formatDepartment, formatIsoDate } from "@/lib/format";

export const metadata = {
  title: "Employees — MyPerks",
};

const PAGE_SIZE = 10;

export default async function AdminEmployeesPage({
  searchParams,
}: {
  searchParams: Promise<{ page?: string; q?: string }>;
}) {
  const { page: pageParam, q } = await searchParams;
  const page = Math.max(1, parseInt(pageParam ?? "1", 10) || 1);
  const query = q?.trim() ?? "";

  let data: Awaited<ReturnType<typeof api.getAdminEmployees>> | null = null;
  let fetchError: null | string = null;

  try {
    data = await api.getAdminEmployees(page, PAGE_SIZE, query || undefined);
  } catch (error: unknown) {
    console.error("[MyPerks] GET /admin/employees failed:", error);
    fetchError =
      error instanceof Error ? error.message : "Could not load employees.";
  }

  const makeHref = (p: number) =>
    query ? `?page=${p}&q=${encodeURIComponent(query)}` : `?page=${p}`;

  return (
    <div className="flex-1 overflow-y-auto p-6">
      <div className="mb-6 flex items-start justify-between">
        <div>
          <h1 className="mb-1 text-xl font-semibold">Employees</h1>
          <p className="text-sm text-muted-foreground">
            All employees with their department and role.
          </p>
        </div>
        <PreCreateEmployeeDialog />
      </div>

      <EmployeeSearch initialQuery={query} />

      {fetchError ? (
        <div className="flex flex-col items-center justify-center rounded-lg border border-dashed border-destructive/40 py-16 text-center">
          <p className="text-sm font-medium text-destructive">
            Failed to load employees
          </p>
          <p className="mt-1 text-xs text-muted-foreground">{fetchError}</p>
          <Link
            className="mt-4 text-xs font-medium text-brand-purple-600 hover:underline dark:text-brand-purple-400"
            href="/admin/employees"
          >
            Try again
          </Link>
        </div>
      ) : !data || data.items.length === 0 ? (
        <EmptyState query={query} />
      ) : (
        <>
          <div className="overflow-x-auto rounded-lg border border-border">
            <table className="w-full">
              <thead>
                <tr className="border-b border-border bg-muted/40">
                  <th className="py-3 pl-4 pr-4 text-left text-[10px] font-semibold uppercase tracking-[0.07em] text-muted-foreground">
                    Name
                  </th>
                  <th className="py-3 pr-4 text-left text-[10px] font-semibold uppercase tracking-[0.07em] text-muted-foreground">
                    Email
                  </th>
                  <th className="py-3 pr-4 text-center text-[10px] font-semibold uppercase tracking-[0.07em] text-muted-foreground">
                    Department
                  </th>
                  <th className="py-3 pr-4 text-center text-[10px] font-semibold uppercase tracking-[0.07em] text-muted-foreground">
                    Role
                  </th>
                  <th className="py-3 pr-4 text-center text-[10px] font-semibold uppercase tracking-[0.07em] text-muted-foreground">
                    Joined
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {data.items.map((item) => (
                  <EmployeeRow item={item} key={item.id} />
                ))}
              </tbody>
            </table>
          </div>

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

function EmployeeRow({ item }: { item: AdminEmployeeListItem }) {
  return (
    <tr className="border-b border-border last:border-0 hover:bg-muted/30">
      <td className="py-3 pl-4 pr-4 text-sm font-medium">
        <Link
          className="text-brand-purple-600 hover:underline dark:text-brand-purple-400"
          href={`/admin/employees/${item.id}`}
        >
          {item.name}
        </Link>
      </td>
      <td className="py-3 pr-4 text-sm text-muted-foreground">{item.email}</td>
      <td className="py-3 pr-4 text-center text-sm text-muted-foreground">
        {formatDepartment(item.department)}
      </td>
      <td className="py-3 pr-4 text-center text-sm capitalize text-muted-foreground">
        {item.role === "hr_admin" ? "HR Admin" : "Employee"}
      </td>
      <td className="py-3 pr-4 text-center text-sm text-muted-foreground">
        {formatIsoDate(item.joined_date)}
      </td>
    </tr>
  );
}

function EmptyState({ query }: { query: string }) {
  return (
    <div className="flex flex-col items-center justify-center rounded-lg border border-dashed border-border py-16 text-center">
      <p className="text-sm font-medium">No employees found</p>
      <p className="mt-1 text-xs text-muted-foreground">
        {query
          ? `No employees match "${query}".`
          : "Employees will appear here once added."}
      </p>
    </div>
  );
}
