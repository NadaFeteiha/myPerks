"use client";

import { Bell } from "lucide-react";
import Link from "next/link";

import { useAuth } from "@/contexts/auth-context";

import { ThemeToggle } from "./theme-toggle";

export function TopBar() {
  const { user } = useAuth();

  return (
    <header className="flex shrink-0 items-center justify-between border-b border-border bg-white px-5 py-3 dark:bg-card">
      <span className="text-[15px] font-semibold tracking-tight">
        My<span className="text-brand-purple-600">Perks</span>
      </span>
      <div className="flex items-center gap-3">
        <ThemeToggle />
        <button
          aria-label="Notifications"
          className="relative text-muted-foreground"
          type="button"
        >
          <Bell className="h-[17px] w-[17px]" />
          <span
            aria-hidden="true"
            className="absolute -right-0.5 -top-0.5 h-1.5 w-1.5 rounded-full border-[1.5px] border-white bg-brand-amber-400"
          />
        </button>
        <Link
          aria-label={`Profile — ${user?.name ?? "Account"}`}
          className="flex h-[30px] w-[30px] items-center justify-center rounded-full border border-brand-purple-200 bg-brand-purple-50 text-[11px] font-semibold text-brand-purple-800 transition-colors hover:bg-brand-purple-100 dark:border-brand-purple-700 dark:bg-brand-purple-900/50 dark:text-brand-purple-300 dark:hover:bg-brand-purple-900/70"
          href="/profile"
        >
          {user?.initials ?? "?"}
        </Link>
      </div>
    </header>
  );
}
