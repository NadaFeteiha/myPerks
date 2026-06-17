"use client";

import { type ReactNode, useEffect, useRef } from "react";

import { cn } from "@/lib/cn";

type ConfirmDialogProps = {
  cancelLabel?: string;
  confirmLabel?: string;
  description?: ReactNode;
  isOpen: boolean;
  isPending?: boolean;
  onCancel: () => void;
  onConfirm: () => void;
  title: string;
  variant?: "default" | "destructive";
};

export function ConfirmDialog({
  cancelLabel = "Cancel",
  confirmLabel = "Confirm",
  description,
  isOpen,
  isPending = false,
  onCancel,
  onConfirm,
  title,
  variant = "default",
}: ConfirmDialogProps) {
  const confirmButtonRef = useRef<HTMLButtonElement>(null);

  // Focus the confirm button when opened
  useEffect(() => {
    if (isOpen) confirmButtonRef.current?.focus();
  }, [isOpen]);

  // Close on ESC
  useEffect(() => {
    if (!isOpen) return;

    function handleKey(event: KeyboardEvent) {
      if (event.key === "Escape" && !isPending) onCancel();
    }

    document.addEventListener("keydown", handleKey);
    return () => document.removeEventListener("keydown", handleKey);
  }, [isOpen, isPending, onCancel]);

  if (!isOpen) return null;

  return (
    <div
      aria-labelledby="confirm-dialog-title"
      aria-modal="true"
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4"
      onClick={(e) => {
        if (e.target === e.currentTarget && !isPending) onCancel();
      }}
      role="dialog"
    >
      <div className="w-full max-w-sm rounded-2xl border border-border bg-card p-5 shadow-lg">
        <h2
          className="text-sm font-semibold text-foreground"
          id="confirm-dialog-title"
        >
          {title}
        </h2>
        {description && (
          <div className="mt-2 text-[13px] text-muted-foreground">
            {description}
          </div>
        )}

        <div className="mt-5 flex justify-end gap-2">
          <button
            className="rounded-lg border border-border px-3 py-1.5 text-[13px] font-medium text-foreground transition-colors hover:bg-surface-2 disabled:opacity-50"
            disabled={isPending}
            onClick={onCancel}
            type="button"
          >
            {cancelLabel}
          </button>
          <button
            className={cn(
              "rounded-lg px-3 py-1.5 text-[13px] font-medium text-white transition-colors disabled:opacity-50",
              variant === "destructive"
                ? "bg-destructive hover:bg-destructive/90"
                : "bg-brand-purple-600 hover:bg-brand-purple-700",
            )}
            disabled={isPending}
            onClick={onConfirm}
            ref={confirmButtonRef}
            type="button"
          >
            {isPending ? "…" : confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
