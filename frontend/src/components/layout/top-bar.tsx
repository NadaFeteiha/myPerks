import { Bell } from "lucide-react";

export function TopBar() {
  return (
    <header className="flex shrink-0 items-center justify-between border-b border-border bg-white px-5 py-3">
      <span className="text-[15px] font-semibold tracking-tight">
        My<span className="text-brand-purple-600">Perks</span>
      </span>
      <div className="flex items-center gap-3">
        <div className="relative">
          <Bell className="h-[17px] w-[17px] text-muted-foreground" />
          <span className="absolute -right-0.5 -top-0.5 h-1.5 w-1.5 rounded-full border-[1.5px] border-white bg-brand-amber-400" />
        </div>
        <div className="flex h-[30px] w-[30px] items-center justify-center rounded-full border border-brand-purple-200 bg-brand-purple-50 text-[11px] font-semibold text-brand-purple-800">
          SM
        </div>
      </div>
    </header>
  );
}
