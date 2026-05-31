"use client";

import { MoreVertical } from "lucide-react";
import {
  type ReactNode,
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";

import { cn } from "@/lib/cn";

type DropdownMenuItemProps = {
  children: ReactNode;
  onSelect: () => void;
  variant?: "default" | "destructive";
};

type DropdownMenuProps = {
  children: ReactNode;
  label?: string;
};

export function DropdownMenu({
  children,
  label = "Open menu",
}: DropdownMenuProps) {
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const close = useCallback(() => setIsOpen(false), []);

  // Close on outside click
  useEffect(() => {
    if (!isOpen) return;

    function handlePointerDown(event: PointerEvent) {
      if (
        containerRef.current &&
        !containerRef.current.contains(event.target as Node)
      ) {
        close();
      }
    }

    document.addEventListener("pointerdown", handlePointerDown);
    return () => document.removeEventListener("pointerdown", handlePointerDown);
  }, [isOpen, close]);

  // Close on ESC
  useEffect(() => {
    if (!isOpen) return;

    function handleKey(event: KeyboardEvent) {
      if (event.key === "Escape") close();
    }

    document.addEventListener("keydown", handleKey);
    return () => document.removeEventListener("keydown", handleKey);
  }, [isOpen, close]);

  return (
    <div className="relative" ref={containerRef}>
      <button
        aria-expanded={isOpen}
        aria-haspopup="menu"
        aria-label={label}
        className="flex h-7 w-7 items-center justify-center rounded-lg text-muted-foreground transition-colors hover:bg-surface-2 hover:text-foreground"
        onClick={(e) => {
          e.preventDefault();
          e.stopPropagation();
          setIsOpen((prev) => !prev);
        }}
        type="button"
      >
        <MoreVertical className="h-4 w-4" />
      </button>

      {isOpen && (
        <div
          className="absolute right-0 top-full z-10 mt-1 min-w-[140px] overflow-hidden rounded-lg border border-border bg-card shadow-md"
          onClick={() => close()}
          role="menu"
        >
          {children}
        </div>
      )}
    </div>
  );
}

export function DropdownMenuItem({
  children,
  onSelect,
  variant = "default",
}: DropdownMenuItemProps) {
  return (
    <button
      className={cn(
        "block w-full px-3 py-2 text-left text-sm transition-colors",
        variant === "destructive"
          ? "text-destructive hover:bg-destructive/10"
          : "text-foreground hover:bg-surface-2",
      )}
      onClick={(e) => {
        e.preventDefault();
        e.stopPropagation();
        onSelect();
      }}
      role="menuitem"
      type="button"
    >
      {children}
    </button>
  );
}
