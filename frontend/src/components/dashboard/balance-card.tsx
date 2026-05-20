import { cn } from "@/lib/cn";

type BalanceCardProps = {
  icon: React.ReactNode;
  label: string;
  progress: number;
  progressColor: string;
  sub: string;
  unit: string;
  value: number | string;
};

export function BalanceCard({
  icon,
  label,
  progress,
  progressColor,
  sub,
  unit,
  value,
}: BalanceCardProps) {
  return (
    <div className="rounded-xl border border-border bg-white p-4 dark:bg-card">
      <div className="mb-2.5 flex items-center justify-between">
        <span className="text-[11px] font-semibold uppercase tracking-[0.05em] text-muted-foreground">
          {label}
        </span>
        <span className="text-base">{icon}</span>
      </div>
      <p className="text-[28px] font-bold leading-none tracking-tight text-foreground">
        {value}{" "}
        <span className="text-[13px] font-normal text-muted-foreground">{unit}</span>
      </p>
      <p className="mt-1 text-[11px] text-muted-foreground">{sub}</p>
      <div className="mt-3 h-1 overflow-hidden rounded-full bg-surface-3">
        <div
          className={cn("h-full rounded-full", progressColor)}
          style={{ width: `${progress}%` }}
        />
      </div>
    </div>
  );
}
