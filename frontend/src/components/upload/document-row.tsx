"use client";

import { FileText } from "lucide-react";
import Link from "next/link";

import { formatIsoDate } from "@/lib/format";

type DocumentRowProps = {
  department?: string;
  extraction_status?: null | string;
  filename: string;
  id: number;
  uploaded_at: string;
};

const STATUS_STYLES: Record<
  string,
  { label: string; className: string }
> = {
  approved: {
    label: "Approved",
    className:
      "bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300",
  },
  extracted: {
    label: "Ready to Review",
    className:
      "bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300",
  },
  extracting: {
    label: "Extracting…",
    className:
      "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/40 dark:text-yellow-300",
  },
  failed: {
    label: "Failed",
    className: "bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300",
  },
  pending: {
    label: "Not Extracted",
    className:
      "bg-muted text-muted-foreground",
  },
};

export function DocumentRow({
  department,
  extraction_status,
  filename,
  id,
  uploaded_at,
}: DocumentRowProps) {
  const statusKey = extraction_status ?? "pending";
  const statusStyle = STATUS_STYLES[statusKey] ?? STATUS_STYLES.pending!;

  return (
    <div className="flex items-start gap-2 rounded-xl border border-border bg-white p-4 dark:bg-card">
      <FileText className="mt-px h-4 w-4 shrink-0 text-brand-purple-600 dark:text-brand-purple-400" />
      <div className="min-w-0 flex-1">
        <p className="truncate text-[13px] font-medium text-foreground">
          {filename}
        </p>
        <p className="mt-0.5 text-[11px] text-muted-foreground">
          {formatIsoDate(uploaded_at)}
        </p>
      </div>

      <div className="flex shrink-0 items-center gap-2">
        <span
          className={`rounded-full px-2 py-0.5 text-[11px] font-medium ${statusStyle.className}`}
        >
          {statusStyle.label}
        </span>

        {department && (
          <span className="rounded-full bg-brand-purple-100 px-2 py-0.5 text-[11px] font-medium capitalize text-brand-purple-700 dark:bg-brand-purple-900/40 dark:text-brand-purple-300">
            {department}
          </span>
        )}

        <Link
          href={`/admin/documents/review/${id}`}
          className="rounded-lg border border-border px-2.5 py-1 text-[11px] font-medium text-foreground hover:bg-muted"
        >
          Review
        </Link>
      </div>
    </div>
  );
}
