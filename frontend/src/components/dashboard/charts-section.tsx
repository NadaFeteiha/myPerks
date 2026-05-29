"use client";

import { useAuth } from "@clerk/nextjs";
import { useEffect, useState } from "react";

import type {
  BenefitsSummaryResponse,
  RequestHistoryResponse,
} from "@/lib/api.server";

import { BenefitsBarChart } from "./benefits-bar-chart";
import { ChartsSectionSkeleton } from "./chart-skeleton";
import { RequestsPieChart } from "./requests-pie-chart";

export function ChartsSection() {
  const { getToken } = useAuth();
  const [benefits, setBenefits] = useState<BenefitsSummaryResponse | null>(
    null,
  );
  const [requests, setRequests] = useState<null | RequestHistoryResponse>(null);

  useEffect(() => {
    void (async () => {
      const token = await getToken();
      if (!token) return;
      const headers = { Authorization: `Bearer ${token}` };
      const [bRes, rRes] = await Promise.all([
        fetch("/api/backend/me/benefits-summary", { headers }),
        fetch("/api/backend/me/requests?page=1&page_size=100", { headers }),
      ]);
      if (bRes.ok) setBenefits((await bRes.json()) as BenefitsSummaryResponse);
      if (rRes.ok) setRequests((await rRes.json()) as RequestHistoryResponse);
    })();
  }, [getToken]);

  if (!benefits || !requests) return <ChartsSectionSkeleton />;

  return (
    <div className="mb-5 grid grid-cols-2 gap-2.5">
      <div className="rounded-xl border border-border bg-white p-4 dark:bg-card">
        <p className="mb-3 text-[10px] font-semibold uppercase tracking-[0.07em] text-muted-foreground">
          Benefits usage
        </p>
        <BenefitsBarChart data={benefits.summary} />
      </div>
      <div className="rounded-xl border border-border bg-white p-4 dark:bg-card">
        <p className="mb-3 text-[10px] font-semibold uppercase tracking-[0.07em] text-muted-foreground">
          Request types
        </p>
        <RequestsPieChart data={requests.items} />
      </div>
    </div>
  );
}
