import { Bell } from "lucide-react";
import Link from "next/link";

import { ThemeToggle } from "./theme-toggle";

export function TopBar() {
  return (
    <header className="flex shrink-0 items-center justify-between border-b border-border bg-white px-5 py-3 dark:bg-card">
      <span className="text-[15px] font-semibold tracking-tight">
        My<span className="text-brand-purple-600">Perks</span>
      </span>
      <div className="flex items-center gap-3">
        <ThemeToggle />
        <div className="relative">
          <Bell className="h-[17px] w-[17px] text-muted-foreground" />
          <span className="absolute -right-0.5 -top-0.5 h-1.5 w-1.5 rounded-full border-[1.5px] border-white bg-brand-amber-400" />
        </div>
        <Link
          className="flex h-[30px] w-[30px] items-center justify-center rounded-full border border-brand-purple-200 bg-brand-purple-50 text-[11px] font-semibold text-brand-purple-800 transition-colors hover:bg-brand-purple-100 dark:border-brand-purple-700 dark:bg-brand-purple-900/50 dark:text-brand-purple-300 dark:hover:bg-brand-purple-900/70"
          href="/profile"
        >
          SM
        </Link>
      </div>
    </header>
  );
}
