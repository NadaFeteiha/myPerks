import { AIAssistantPromo } from "@/components/dashboard/ai-assistant-promo";
import { BalanceCardsSection } from "@/components/dashboard/balance-cards-section";
import { HeroBanner } from "@/components/dashboard/hero-banner";

export const metadata = {
  title: "Dashboard — MyPerks",
};

export default function DashboardPage() {
  return (
    <div className="flex-1 overflow-y-auto p-6">
      <HeroBanner />
      <p className="mb-3 text-[10px] font-semibold uppercase tracking-[0.07em] text-muted-foreground">
        Leave balances
      </p>
      <BalanceCardsSection />
      <AIAssistantPromo />
    </div>
  );
}
