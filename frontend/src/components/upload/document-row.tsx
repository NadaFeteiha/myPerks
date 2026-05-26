"use client"

import { FileText } from "lucide-react";

type DocumentRowProps = {
  filename: string;
  uploaded_at: string;
};

export function DocumentRow({ filename, uploaded_at }: DocumentRowProps) {
  return (
    <div className="flex items-start gap-2 rounded-xl border border-border bg-white p-4 dark:bg-card">
      <FileText className="mt-px h-4 w-4 shrink-0 text-brand-purple-600 dark:text-brand-purple-400" />
      <div className="min-w-0 flex-1">
        <p className="truncate text-[13px] font-medium text-foreground">
          {filename}
        </p>
        <p className="mt-0.5 text-[11px] text-muted-foreground">{uploaded_at}</p>
      </div>
    </div>
  );
}
