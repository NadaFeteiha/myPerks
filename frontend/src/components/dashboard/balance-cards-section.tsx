import { Plane, Stethoscope } from "lucide-react";

import { MOCK_BALANCES } from "@/data/mock/dashboard.mock";

import { BalanceCard } from "./balance-card";

const ICON_MAP: Record<string, React.ReactNode> = {
  pto: <Plane className="h-4 w-4 text-brand-purple-600" />,
  sick: <Stethoscope className="h-4 w-4 text-blue-500" />,
};

export function BalanceCardsSection() {
  return (
    <div className="mb-5 grid grid-cols-3 gap-2.5">
      {MOCK_BALANCES.map((item) => (
        <BalanceCard key={item.id} {...item} icon={ICON_MAP[item.iconType]} />
      ))}
    </div>
  );
}
