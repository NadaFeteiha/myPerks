"use client";

import {
  ClipboardList,
  History,
  LayoutDashboard,
  MessageCircle,
  Upload,
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { useAuth } from "@/contexts/auth-context";
import { cn } from "@/lib/cn";

type NavItem = {
  href: string;
  icon: React.ElementType;
  label: string;
};

const NAV_ITEMS: NavItem[] = [
  { href: "/dashboard", icon: LayoutDashboard, label: "Dashboard" },
  { href: "/assistant", icon: MessageCircle, label: "AI Assistant" },
  { href: "/assistant/history", icon: History, label: "History" },
  { href: "/dashboard/upload", icon: Upload, label: "Documents" },
  { href: "/requests", icon: ClipboardList, label: "My Requests" },
];

export function LeftNav() {
  const pathname = usePathname();
  const { user } = useAuth();

  return (
    <nav className="flex w-[200px] shrink-0 flex-col gap-1 overflow-y-auto border-r border-border bg-surface-2 px-3 py-4">
      {NAV_ITEMS.map((item) => {
        const isActive = isNavItemActive(pathname, item.href);
        return (
          <Link
            className={cn(
              "flex items-center gap-2 rounded-lg px-2.5 py-[7px] text-[13px] text-muted-foreground transition-colors hover:bg-brand-purple-50 hover:text-brand-purple-800 dark:hover:bg-brand-purple-900/30 dark:hover:text-brand-purple-300",
              isActive &&
                "bg-brand-purple-50 font-medium text-brand-purple-800 dark:bg-brand-purple-900/30 dark:text-brand-purple-300",
            )}
            href={item.href}
            key={item.href}
          >
            <item.icon className="h-[15px] w-[15px] shrink-0" />
            {item.label}
          </Link>
        );
      })}

      <div className="mt-auto border-t border-border pt-3">
        <Link
          className="flex items-center gap-2 px-1.5 py-2 transition-colors hover:bg-brand-purple-50 dark:hover:bg-brand-purple-900/30"
          href="/profile"
        >
          <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full border border-brand-purple-200 bg-brand-purple-50 text-[11px] font-semibold text-brand-purple-800 dark:border-brand-purple-700 dark:bg-brand-purple-900/50 dark:text-brand-purple-300">
            {user?.initials ?? "?"}
          </div>
          <div>
            <p className="text-[12px] font-medium text-foreground">
              {user?.name ?? ""}
            </p>
            <p className="text-[11px] text-muted-foreground">
              {user?.role ?? ""}
            </p>
          </div>
        </Link>
      </div>
    </nav>
  );
}

function isNavItemActive(pathname: string, href: string): boolean {
  // /assistant must not activate when /assistant/history is the current route
  if (href === "/assistant") return pathname === href;
  return pathname.startsWith(href);
}
