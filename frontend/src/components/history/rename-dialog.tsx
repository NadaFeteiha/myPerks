"use client";

import { useEffect, useRef, useState } from "react";

type RenameDialogProps = {
  error?: null | string;
  initialTitle: string;
  isOpen: boolean;
  isPending?: boolean;
  onCancel: () => void;
  onSubmit: (newTitle: string) => void;
};

export function RenameDialog({
  error,
  initialTitle,
  isOpen,
  isPending = false,
  onCancel,
  onSubmit,
}: RenameDialogProps) {
  const [value, setValue] = useState(initialTitle);
  const inputRef = useRef<HTMLInputElement>(null);

  // Reset value when opening / when initialTitle changes
  useEffect(() => {
    if (isOpen) {
      queueMicrotask(() => {
        inputRef.current?.focus();
        inputRef.current?.select();
      });
    }
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

  const trimmed = value.trim();
  const canSubmit = trimmed.length > 0 && trimmed.length <= 255 && !isPending;

  return (
    <div
      aria-labelledby="rename-dialog-title"
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
          id="rename-dialog-title"
        >
          Rename conversation
        </h2>

        <input
          className="mt-3 w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground outline-none transition-colors placeholder:text-muted-foreground focus:border-brand-purple-400 disabled:opacity-50"
          disabled={isPending}
          maxLength={255}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && canSubmit) onSubmit(trimmed);
          }}
          placeholder="Conversation title"
          ref={inputRef}
          type="text"
          value={value}
        />

        {error && <p className="mt-2 text-[12px] text-destructive">{error}</p>}

        <div className="mt-5 flex justify-end gap-2">
          <button
            className="rounded-lg border border-border px-3 py-1.5 text-[13px] font-medium text-foreground transition-colors hover:bg-surface-2 disabled:opacity-50"
            disabled={isPending}
            onClick={onCancel}
            type="button"
          >
            Cancel
          </button>
          <button
            className="rounded-lg bg-brand-purple-600 px-3 py-1.5 text-[13px] font-medium text-white transition-colors hover:bg-brand-purple-700 disabled:opacity-50"
            disabled={!canSubmit}
            onClick={() => onSubmit(trimmed)}
            type="button"
          >
            {isPending ? "…" : "Save"}
          </button>
        </div>
      </div>
    </div>
  );
}
