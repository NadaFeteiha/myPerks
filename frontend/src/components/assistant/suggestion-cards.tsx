type SuggestionCard = {
  emoji: string;
  id: string;
  prompt: string;
  title: string;
};

const SUGGESTIONS: SuggestionCard[] = [
  {
    emoji: "🏖️",
    id: "pto",
    prompt: "How many vacation days do I have left?",
    title: "Check PTO balance",
  },
  {
    emoji: "🏥",
    id: "insurance",
    prompt: "Does my plan cover physiotherapy?",
    title: "Insurance coverage",
  },
  {
    emoji: "✉️",
    id: "email",
    prompt: "Write an email requesting June 1–5 off",
    title: "Draft leave email",
  },
  {
    emoji: "💰",
    id: "wellness",
    prompt: "When does my wellness budget expire?",
    title: "Wellness budget",
  },
];

type SuggestionCardsProps = {
  onSelectPrompt: (prompt: string) => void;
};

export function SuggestionCards({ onSelectPrompt }: SuggestionCardsProps) {
  return (
    <div className="grid w-full max-w-[520px] grid-cols-2 gap-2">
      {SUGGESTIONS.map((card) => (
        <button
          className="rounded-xl border border-border bg-surface-2 p-3.5 text-left transition-colors hover:border-brand-purple-200 hover:bg-brand-purple-50 dark:hover:border-brand-purple-700 dark:hover:bg-brand-purple-900/30"
          key={card.id}
          onClick={() => onSelectPrompt(card.prompt)}
          type="button"
        >
          <p className="mb-1 text-[13px]">{card.emoji}</p>
          <p className="mb-0.5 text-[12px] font-medium text-foreground">{card.title}</p>
          <p className="text-[11px] text-muted-foreground">{card.prompt}</p>
        </button>
      ))}
    </div>
  );
}
