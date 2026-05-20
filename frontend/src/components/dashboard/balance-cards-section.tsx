import { Plane, Stethoscope } from "lucide-react";

import { BalanceCard } from "./balance-card";

type BalanceData = {
  icon: React.ReactNode;
  id: string;
  label: string;
  progress: number;
  progressColor: string;
  sub: string;
  unit: string;
  value: number | string;
};

const BALANCES: BalanceData[] = [
  {
    icon: <Plane className="h-4 w-4 text-brand-purple-600" />,
    id: "pto",
    label: "PTO",
    progress: 67,
    progressColor: "bg-brand-teal-400",
    sub: "18 total · 6 used this year",
    unit: "days",
    value: 12,
  },
  {
    icon: <Stethoscope className="h-4 w-4 text-blue-500" />,
    id: "sick",
    label: "Sick Days",
    progress: 80,
    progressColor: "bg-blue-400",
    sub: "10 total · 2 used this year",
    unit: "days",
    value: 8,
  },
];

export function BalanceCardsSection() {
  return (
    <div className="mb-5 grid grid-cols-3 gap-2.5">
      {BALANCES.map((item) => (
        <BalanceCard key={item.id} {...item} />
      ))}
    </div>
  );
}
