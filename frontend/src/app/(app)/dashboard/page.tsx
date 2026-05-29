import { redirect } from "next/navigation";

import { AIAssistantPromo } from "@/components/dashboard/ai-assistant-promo";
import { BalanceCardsSection } from "@/components/dashboard/balance-cards-section";
import { ChartsSection } from "@/components/dashboard/charts-section";
import { HeroBanner } from "@/components/dashboard/hero-banner";
import { api } from "@/lib/api.server";

export const metadata = {
  title: "Dashboard — MyPerks",
};

export default async function DashboardPage() {
  try {
    await api.getMe();
  } catch (error: unknown) {
    const isNotFound = error instanceof Error && error.message.includes("404");

    if (isNotFound) {
      redirect("/onboarding");
    }

    console.error("[MyPerks] GET /me failed:", error);
  }
  return (
    <div className="flex-1 overflow-y-auto p-6">
      <HeroBanner />
      <p className="mb-3 text-[10px] font-semibold uppercase tracking-[0.07em] text-muted-foreground">
        Leave balances
      </p>
      <BalanceCardsSection />
      <p className="mb-3 text-[10px] font-semibold uppercaes tracking-[0.07em] text-muted-foreground">
        Benefits overview
      </p>
      <ChartsSection />
      <AIAssistantPromo />
    </div>
  );
}
