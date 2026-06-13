"use client";

import { FileText } from "lucide-react";

type DocumentRowProps = {
  department?: string;
  filename: string;
  uploaded_at: string;
};

export function DocumentRow({
  department,
  filename,
  uploaded_at,
}: DocumentRowProps) {
  return (
    <div className="flex items-start gap-2 rounded-xl border border-border bg-white p-4 dark:bg-card">
      <FileText className="mt-px h-4 w-4 shrink-0 text-brand-purple-600 dark:text-brand-purple-400" />
      <div className="min-w-0 flex-1">
        <p className="truncate text-[13px] font-medium text-foreground">
          {filename}
        </p>
        <p className="mt-0.5 text-[11px] text-muted-foreground">
          {uploaded_at}
        </p>
      </div>
      {department && (
        <span className="shrink-0 rounded-full bg-brand-purple-100 px-2 py-0.5 text-[11px] font-medium capitalize text-brand-purple-700 dark:bg-brand-purple-900/40 dark:text-brand-purple-300">
          {department}
        </span>
      )}
    </div>
  );
}
