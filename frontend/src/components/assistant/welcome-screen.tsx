import { Sparkles } from "lucide-react";

import { SuggestionCards } from "./suggestion-cards";

type WelcomeScreenProps = {
  onSelectPrompt: (prompt: string) => void;
};

export function WelcomeScreen({ onSelectPrompt }: WelcomeScreenProps) {
  return (
    <div className="flex flex-col items-center gap-6">
      <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-brand-purple-600 shadow-[0_4px_16px_rgba(83,74,183,0.25)]">
        <Sparkles className="h-6 w-6 text-white" />
      </div>
      <div className="text-center">
        <h1 className="mb-1.5 text-[18px] font-semibold tracking-tight text-foreground">
          How can I help you today?
        </h1>
        <p className="max-w-[380px] text-[13px] leading-relaxed text-muted-foreground">
          Ask anything about your benefits, check balances, or get a ready-to-send HR email in
          seconds.
        </p>
      </div>
      <SuggestionCards onSelectPrompt={onSelectPrompt} />
    </div>
  );
}
