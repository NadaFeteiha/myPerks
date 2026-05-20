"use client";

import {
  FileText,
  History,
  LayoutDashboard,
  MessageCircle,
  Upload,
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { useAuth } from "@/contexts/auth-context";
import { MOCK_POLICY_FILES } from "@/data/mock/navigation.mock";
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

      <div className="mt-3">
        <p className="mb-2 px-2 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
          Policy documents
        </p>

        <label
          className="mb-2 flex cursor-pointer flex-col items-center rounded-lg border border-dashed border-border bg-background px-3 py-3 text-center transition-colors hover:bg-brand-purple-50 dark:hover:bg-brand-purple-900/30"
          htmlFor="policy-file-input"
        >
          <Upload className="mx-auto mb-1 h-4 w-4 text-muted-foreground" />
          <p className="text-[11px] text-muted-foreground">
            Drop a policy file here
          </p>
          <p className="text-[10px] text-muted-foreground/60">
            .txt or .md · MVP
          </p>
          <input
            accept=".txt,.md"
            className="hidden"
            id="policy-file-input"
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) {
                // TODO: Replace with UploadThing integration
                void file;
              }
            }}
            type="file"
          />
        </label>

        <div className="flex flex-col gap-1.5">
          {MOCK_POLICY_FILES.map((file) => (
            <div
              className="flex items-start gap-2 rounded-lg border border-border bg-background px-2.5 py-2"
              key={file.id}
            >
              <FileText className="mt-px h-3.5 w-3.5 shrink-0 text-brand-purple-600 dark:text-brand-purple-400" />
              <div>
                <p className="text-[12px] font-medium text-foreground">
                  {file.name}
                </p>
                <p className="text-[11px] text-muted-foreground">
                  {file.updatedAt}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>

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
