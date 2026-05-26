"use client";

import { ArrowUp } from "lucide-react";
import { useState } from "react";

import { cn } from "@/lib/cn";

type ChatInputProps = {
  disabled?: boolean;
  onSendMessage: (content: string) => void;
};

export function ChatInput({ disabled = false, onSendMessage }: ChatInputProps) {
  const [value, setValue] = useState("");
  const hasValue = value.trim().length > 0;
  const canSubmit = hasValue && !disabled;

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (canSubmit) {
      onSendMessage(value.trim());
      setValue("");
    }
  };

  return (
    <form
      className="flex shrink-0 items-center gap-2.5 border-t border-border bg-white px-5 py-3.5 dark:bg-card"
      onSubmit={handleSubmit}
    >
      <input
        className="h-10 flex-1 rounded-xl border border-border bg-surface-2 px-3.5 text-[13px] text-foreground placeholder:text-muted-foreground focus:border-brand-purple-600 focus:outline-none disabled:opacity-50"
        disabled={disabled}
        onChange={(e) => setValue(e.target.value)}
        placeholder={
          disabled
            ? "Waiting for response…"
            : "Ask anything about your benefits…"
        }
        type="text"
        value={value}
      />
      <button
        aria-label="Send message"
        className={cn(
          "flex h-9 w-9 shrink-0 items-center justify-center rounded-lg transition-colors",
          canSubmit
            ? "bg-brand-purple-600 text-white hover:bg-brand-purple-800"
            : "bg-brand-purple-100 text-brand-purple-800",
        )}
        disabled={!canSubmit}
        type="submit"
      >
        <ArrowUp className="h-4 w-4" />
      </button>
    </form>
  );
}
