import { Plane, Stethoscope } from "lucide-react";

import { api } from "@/lib/api";

import { BalanceCard } from "./balance-card";

const ICON_MAP: Record<string, React.ReactNode> = {
  pto: <Plane className="h-4 w-4 text-brand-purple-600" />,
  sick: <Stethoscope className="h-4 w-4 text-blue-500" />,
};

export async function BalanceCardsSection() {
  const data = await api.getVacationBalance();

  if (!data.balances.length) {
    return (
      <div className="mb-5 rounded-xl border border-border bg-white p-6 text-center dark:bg-card">
        <p className="text-[12px] text-muted-foreground">No leave balances found for {data.year}.</p>
      </div>
    );
  }

  return (
    <div className="mb-5 grid grid-cols-3 gap-2.5">
      {data.balances.map((balance) => {
        const iconType = getIconType(balance.leave_type);
        const progress = balance.total_days > 0
          ? Math.round((balance.remaining_days / balance.total_days) * 100)
          : 0;

          return (
            <BalanceCard
              icon={ICON_MAP[iconType]}
              key={balance.leave_type}
              label={balance.leave_type}
              progress={progress}
              progressColor={getProgressColor(balance.leave_type)}
              sub={`${balance.total_days} total · ${balance.used_days} used this year`}
              unit="days"
              value={balance.remaining_days}
            />
          );
      })}
    </div>
  )
}

function getIconType(leaveType: string): string {
  return leaveType.toLowerCase().includes("sick") ? "sick" :"pto";
}

function getProgressColor(leaveType: string) {
  return leaveType.toLowerCase().includes("sick") ? "blue" :"teal";
}
