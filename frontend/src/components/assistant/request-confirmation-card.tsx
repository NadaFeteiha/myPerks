"use client";

import { Ban, CheckCircle, ExternalLink, Loader2, X } from "lucide-react";
import Link from "next/link";

import type { BreakdownDay, PendingRequest } from "@/lib/chat-stream";

import { cn } from "@/lib/cn";

interface Props {
  cancelled: boolean;
  isSubmitting: boolean;
  onCancel: () => void;
  onDismiss: () => void;
  onSubmit: () => void;
  request: PendingRequest;
  submitted: boolean;
}

export function RequestConfirmationCard({
  cancelled,
  isSubmitting,
  onCancel,
  onDismiss,
  onSubmit,
  request,
  submitted,
}: Props) {
  const body = request.body;
  const typeLabel = formatType(request.type);
  const isDone = submitted || cancelled;

  return (
    <div className="mx-auto w-full max-w-160 overflow-hidden rounded-xl border border-border bg-card shadow-sm">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-border px-4 py-3">
        <div className="flex items-center gap-2">
          <span className="inline-flex items-center rounded-full bg-brand-purple-100 px-2.5 py-0.5 text-[11px] font-semibold text-brand-purple-700 dark:bg-brand-purple-900/30 dark:text-brand-purple-300">
            {typeLabel}
          </span>
          <span className="text-[13px] font-semibold text-foreground">
            Request confirmation
          </span>
        </div>
        {isDone && (
          <button
            aria-label="Dismiss"
            className="flex h-6 w-6 items-center justify-center rounded-md text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
            onClick={onDismiss}
            type="button"
          >
            <X className="h-3.5 w-3.5" />
          </button>
        )}
      </div>

      {/* Body */}
      <div className="space-y-2 px-4 py-3">
        {submitted && (
          <div className="flex items-center gap-2 text-green-700 dark:text-green-400">
            <CheckCircle className="h-4 w-4 shrink-0" />
            <span className="text-[13px] font-medium">
              Request submitted successfully — status is{" "}
              <span className="font-semibold">pending</span>.
            </span>
          </div>
        )}

        {cancelled && (
          <div className="flex items-center gap-2 text-muted-foreground">
            <Ban className="h-4 w-4 shrink-0" />
            <span className="text-[13px] font-medium">
              Request cancelled. No submission was made.
            </span>
          </div>
        )}

        {!isDone && (
          <>
            <p className="mb-3 text-[12px] text-muted-foreground">
              {request.summary}
            </p>

            {/* Leave request fields */}
            {typeof body.start_date === "string" && (
              <RequestDetail
                label="Start date"
                value={formatDate(body.start_date)}
              />
            )}
            {typeof body.end_date === "string" && (
              <RequestDetail
                label="End date"
                value={formatDate(body.end_date)}
              />
            )}
            {typeof body.days === "number" && (
              <RequestDetail
                label="Days"
                value={`${body.days} day${body.days !== 1 ? "s" : ""}`}
              />
            )}
            {typeof body.reason === "string" && (
              <RequestDetail label="Reason" value={body.reason} />
            )}

            {/* Reimbursement fields */}
            {typeof body.amount === "number" && (
              <RequestDetail
                label="Amount"
                value={`${body.currency ?? "USD"} ${body.amount.toFixed(2)}`}
              />
            )}
            {typeof body.description === "string" && (
              <RequestDetail label="Description" value={body.description} />
            )}

            {/* Working-day breakdown (leave requests only) */}
            {request.breakdown && request.breakdown.length > 0 && (
              <WorkingDaysBreakdown breakdown={request.breakdown} />
            )}
          </>
        )}
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between border-t border-border px-4 py-3">
        {submitted && (
          <Link
            className="flex items-center gap-1.5 text-[12px] font-medium text-brand-purple-600 hover:underline dark:text-brand-purple-400"
            href="/requests"
          >
            View in Request History
            <ExternalLink className="h-3 w-3" />
          </Link>
        )}

        {cancelled && (
          <span className="text-[12px] text-muted-foreground">
            You can start a new request anytime.
          </span>
        )}

        {!isDone && (
          <>
            <button
              className="text-[12px] font-medium text-muted-foreground transition-colors hover:text-foreground"
              onClick={onCancel}
              type="button"
            >
              Cancel
            </button>
            <button
              className={cn(
                "flex items-center gap-1.5 rounded-lg px-4 py-1.5 text-[12px] font-semibold text-white transition-colors",
                isSubmitting
                  ? "cursor-not-allowed bg-brand-purple-400"
                  : "bg-brand-purple-600 hover:bg-brand-purple-800",
              )}
              disabled={isSubmitting}
              onClick={onSubmit}
              type="button"
            >
              {isSubmitting && <Loader2 className="h-3 w-3 animate-spin" />}
              {isSubmitting ? "Submitting…" : "Submit Request"}
            </button>
          </>
        )}
      </div>
    </div>
  );
}

function formatDate(iso: string): string {
  const [year, month, day] = iso.split("-").map(Number);
  return new Date(year, month - 1, day).toLocaleDateString("en-US", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

function formatType(type: string): string {
  if (type.toLowerCase() === "pto") return "PTO";
  return type.charAt(0).toUpperCase() + type.slice(1);
}

function RequestDetail({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-start gap-2">
      <span className="min-w-22.5 text-[11px] font-semibold uppercase tracking-[0.06em] text-muted-foreground">
        {label}
      </span>
      <span className="text-[13px] text-foreground">{value}</span>
    </div>
  );
}

function WorkingDaysBreakdown({ breakdown }: { breakdown: BreakdownDay[] }) {
  if (!breakdown.length) return null;
  return (
    <div className="mt-3 border-t border-border pt-3">
      <p className="mb-2 text-[11px] font-semibold uppercase tracking-[0.06em] text-muted-foreground">
        Day breakdown
      </p>
      <div className="flex flex-wrap gap-1">
        {breakdown.map((d) => {
          const [year, month, day] = d.date.split("-").map(Number);
          const label = new Date(year, month - 1, day).toLocaleDateString(
            "en-US",
            {
              day: "numeric",
              month: "short",
            },
          );
          return (
            <span
              className={cn(
                "inline-flex items-center rounded-md px-2 py-0.5 text-[11px] font-medium",
                d.status === "work" &&
                  "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300",
                d.status === "weekend" &&
                  "bg-muted text-muted-foreground line-through",
                d.status === "holiday" &&
                  "bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-300",
              )}
              key={d.date}
              title={
                d.name ?? (d.status === "weekend" ? "Weekend" : "Working day")
              }
            >
              {d.day} {label}
              {d.status === "holiday" && " 🏛️"}
            </span>
          );
        })}
      </div>
      <p className="mt-1.5 text-[11px] text-muted-foreground">
        <span className="mr-3">🟩 working day</span>
        <span className="mr-3">⬜ weekend</span>
        <span>🟨 public holiday</span>
      </p>
    </div>
  );
}
