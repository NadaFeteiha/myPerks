"use client";

import { useRef, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { FileText, History, LayoutDashboard, MessageCircle, Upload } from "lucide-react";

import { cn } from "@/lib/cn";

type NavItem = {
  href: string;
  icon: React.ElementType;
  label: string;
  badge?: number;
};

const NAV_ITEMS: NavItem[] = [
  { href: "/dashboard", icon: LayoutDashboard, label: "Dashboard" },
  { href: "/assistant", icon: MessageCircle, label: "AI Assistant" },
  { href: "/assistant/history", icon: History, label: "History" },
];

type PolicyFile = {
  id: string;
  name: string;
  updatedAt: string;
};

const POLICY_FILES: PolicyFile[] = [
  { id: "1", name: "PTO Policy 2024", updatedAt: "Updated May 14" },
  { id: "2", name: "Parental Leave", updatedAt: "Updated May 15" },
  { id: "3", name: "Wellness Reimbursement", updatedAt: "Updated May 16" },
];

export function LeftNav() {
  const pathname = usePathname();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      console.log("Selected file:", file.name);
      // TODO: Handle file upload logic here
    }
  };

  return (
    <nav className="flex w-[200px] shrink-0 flex-col gap-1 overflow-y-auto border-r border-border bg-surface-2 px-3 py-4">
      {NAV_ITEMS.map((item) => {
        const isActive = pathname.startsWith(item.href);
        return (
          <Link
            key={item.href}
            href={item.href}
            className={cn(
              "flex items-center gap-2 rounded-lg px-2.5 py-[7px] text-[13px] text-muted-foreground transition-colors hover:bg-brand-purple-50 hover:text-brand-purple-800 dark:hover:bg-brand-purple-900/30 dark:hover:text-brand-purple-300",
              isActive && "bg-brand-purple-50 font-medium text-brand-purple-800 dark:bg-brand-purple-900/30 dark:text-brand-purple-300",
            )}
          >
            <item.icon className="h-[15px] w-[15px] shrink-0" />
            {item.label}
            {item.badge !== undefined && (
              <span className="ml-auto rounded-full bg-brand-purple-600 px-1.5 py-px text-[10px] font-semibold text-white">
                {item.badge}
              </span>
            )}
          </Link>
        );
      })}

      <div className="mt-3">
        <p className="mb-2 px-2 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
          Policy documents
        </p>

        <div
          className="mb-2 cursor-pointer rounded-lg border border-dashed border-border bg-background px-3 py-3 text-center transition-colors hover:bg-brand-purple-50 dark:hover:bg-brand-purple-900/30"
          onClick={handleFileSelect}
        >
          <Upload className="mx-auto mb-1 h-4 w-4 text-muted-foreground" />
          <p className="text-[11px] text-muted-foreground">Drop a policy file here</p>
          <p className="text-[10px] text-muted-foreground/60">.txt or .md · MVP</p>
          <input
            ref={fileInputRef}
            type="file"
            accept=".txt,.md"
            onChange={handleFileChange}
            className="hidden"
          />
        </div>

        <div className="flex flex-col gap-1.5">
          {POLICY_FILES.map((file) => (
            <div
              key={file.id}
              className="flex items-start gap-2 rounded-lg border border-border bg-background px-2.5 py-2"
            >
              <FileText className="mt-px h-3.5 w-3.5 shrink-0 text-brand-purple-600 dark:text-brand-purple-400" />
              <div>
                <p className="text-[12px] font-medium text-foreground">{file.name}</p>
                <p className="text-[11px] text-muted-foreground">{file.updatedAt}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="mt-auto border-t border-border pt-3">
        <div className="flex items-center gap-2 px-1.5 py-2">
          <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full border border-brand-purple-200 bg-brand-purple-50 text-[11px] font-semibold text-brand-purple-800">
            SM
          </div>
          <div>
            <p className="text-[12px] font-medium text-foreground">Sarah Miller</p>
            <p className="text-[11px] text-muted-foreground">Engineering</p>
          </div>
        </div>
      </div>
    </nav>
  );
}
