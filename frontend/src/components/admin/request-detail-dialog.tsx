"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import type { AdminEmployeeDetail } from "@/lib/api.client";
import type { AdminRequestListItem } from "@/lib/api.server";

import { StatusBadge } from "@/components/shared/status-badge";
import { useApi } from "@/lib/api.client";
import {
  formatDepartment,
  formatIsoDate,
  formatRequestType,
  getRequestDate,
  getRequestDescription,
} from "@/lib/format";

export function RequestDetailDialog({
  item,
  onApprove,
  onClose,
  onReject,
}: {
  item: AdminRequestListItem | null;
  onApprove: () => void;
  onClose: () => void;
  onReject: () => void;
}) {
  const api = useApi();
  const [employee, setEmployee] = useState<AdminEmployeeDetail | null>(null);
  const [error, setError] = useState<null | string>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!item) return;

    let cancelled = false;

    void (async () => {
      setLoading(true);
      setError(null);

      try {
        const data = await api.getAdminEmployeeDetail(item.employee_id);
        if (!cancelled) setEmployee(data);
      } catch (err: unknown) {
        if (!cancelled) {
          setError(
            err instanceof Error
              ? err.message
              : "Could not load employee details.",
          );
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [api, item]);

  useEffect(() => {
    if (!item) return;

    function handleKey(event: KeyboardEvent) {
      if (event.key === "Escape") onClose();
    }

    document.addEventListener("keydown", handleKey);
    return () => document.removeEventListener("keydown", handleKey);
  }, [item, onClose]);

  if (!item) return null;

  const relevantBalance = employee?.balances.find(
    (b) => b.leave_type === item.type,
  );

  return (
    <div
      aria-labelledby="request-detail-title"
      aria-modal="true"
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
      role="dialog"
    >
      <div className="w-full max-w-lg rounded-2xl border border-border bg-card p-5 shadow-lg">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h2
              className="text-sm font-semibold text-foreground"
              id="request-detail-title"
            >
              {formatRequestType(item.type)} request
            </h2>
            <p className="mt-1 text-xs text-muted-foreground">
              From {item.employee_name}
            </p>
          </div>
          <StatusBadge status={item.status} />
        </div>

        <div className="mt-4 grid grid-cols-2 gap-3 text-[13px]">
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-[0.07em] text-muted-foreground">
              Dates
            </p>
            <p className="mt-0.5">{getRequestDate(item)}</p>
          </div>
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-[0.07em] text-muted-foreground">
              Submitted
            </p>
            <p className="mt-0.5">{formatIsoDate(item.created_at)}</p>
          </div>
          <div className="col-span-2">
            <p className="text-[10px] font-semibold uppercase tracking-[0.07em] text-muted-foreground">
              Description
            </p>
            <p className="mt-0.5">{getRequestDescription(item.body)}</p>
          </div>
        </div>

        <div className="mt-5 border-t border-border pt-4">
          <p className="mb-2 text-[10px] font-semibold uppercase tracking-[0.07em] text-muted-foreground">
            Employee
          </p>

          {loading ? (
            <p className="text-sm text-muted-foreground">Loading…</p>
          ) : error ? (
            <p className="text-sm text-destructive">{error}</p>
          ) : employee ? (
            <div className="space-y-2 text-[13px]">
              <p>
                {employee.email} · {formatDepartment(employee.department)}
              </p>
              <p className="text-muted-foreground">
                Joined {formatIsoDate(employee.joined_date)}
              </p>

              {relevantBalance && (
                <div className="mt-2 rounded-lg border border-border bg-muted/30 p-3">
                  <p className="text-[10px] font-semibold uppercase tracking-[0.07em] text-muted-foreground">
                    {formatRequestType(relevantBalance.leave_type)} balance
                  </p>
                  <p className="mt-1 text-[18px] font-bold leading-none tracking-tight text-foreground">
                    {relevantBalance.remaining_days}{" "}
                    <span className="text-[12px] font-normal text-muted-foreground">
                      / {relevantBalance.total_days} days left
                    </span>
                  </p>
                </div>
              )}

              <Link
                className="inline-block text-xs font-medium text-brand-purple-600 hover:underline dark:text-brand-purple-400"
                href={`/admin/employees/${item.employee_id}`}
              >
                View full profile
              </Link>
            </div>
          ) : null}
        </div>

        <div className="mt-5 flex justify-end gap-2">
          <button
            className="rounded-lg border border-border px-3 py-1.5 text-[13px] font-medium text-foreground transition-colors hover:bg-surface-2"
            onClick={onClose}
            type="button"
          >
            Close
          </button>
          {item.status === "pending" && (
            <>
              <button
                className="rounded-lg border border-border px-3 py-1.5 text-[13px] font-medium text-destructive transition-colors hover:bg-destructive/10"
                onClick={onReject}
                type="button"
              >
                Reject
              </button>
              <button
                className="rounded-lg bg-brand-purple-600 px-3 py-1.5 text-[13px] font-medium text-white transition-colors hover:bg-brand-purple-700"
                onClick={onApprove}
                type="button"
              >
                Approve
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
