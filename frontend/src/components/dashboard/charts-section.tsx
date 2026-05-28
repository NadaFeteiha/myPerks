import { api } from "@/lib/api.server";

import { BenefitsBarChart } from "./benefits-bar-chart";
import { RequestsPieChart } from "./requests-pie-chart";

export async function ChartsSection() {
  const [benefitsSummary, requestHistory] = await Promise.all([
    api.getBenefitsSummary(),
    api.getRequestHistory(1, 100),
  ]);

  return (
    <div className="mb-5 grid grid-cols-2 gap-2.5">
      <div className="rounded-xl border border-border bg-white p-4 dark:bg-card">
        <p className="mb-3 text-[10px] font-semibold uppercase tracking-[0.07em] text-muted-foreground">
          Benefits usage
        </p>
        <BenefitsBarChart data={benefitsSummary.summary} />
      </div>
      <div className="rounded-xl border border-border bg-white p-4 dark:bg-card">
        <p className="mb-3 text-[10px] font-semibold uppercase tracking-[0.07em] text-muted-foreground">
          Request types
        </p>
        <RequestsPieChart data={requestHistory.items} />
      </div>
    </div>
  );
}
