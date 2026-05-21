"use client";

import { UserButton } from "@clerk/nextjs";
import { Bell } from "lucide-react";

import { ThemeToggle } from "./theme-toggle";

export function TopBar() {
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
        <UserButton afterSignOutUrl="/sign-in" />
      </div>
    </header>
  );
}
