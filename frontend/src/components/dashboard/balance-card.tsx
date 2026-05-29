import { cn } from "@/lib/cn";

// Moved out of mock - this type belongs here
type ProgressColor = "blue" | "teal";

// Static map keeps class strings in source so Tailwind JIT can detect them
const PROGRESS_COLOR_MAP: Record<ProgressColor, string> = {
  blue: "bg-blue-400",
  teal: "bg-brand-teal-400",
};

type BalanceCardProps = {
  icon: React.ReactNode;
  label: string;
  progress: number;
  progressColor: ProgressColor;
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
  const clampedProgress = Math.min(Math.max(progress, 0), 100);

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
        <span className="text-[13px] font-normal text-muted-foreground">
          {unit}
        </span>
      </p>
      <p className="mt-1 text-[11px] text-muted-foreground">{sub}</p>
      <div className="mt-3 h-1 overflow-hidden rounded-full bg-surface-3">
        <div
          className={cn(
            "h-full rounded-full",
            // eslint-disable-next-line security/detect-object-injection
            PROGRESS_COLOR_MAP[progressColor],
          )}
          style={{ width: `${clampedProgress}%` }}
        />
      </div>
    </div>
  );
}
