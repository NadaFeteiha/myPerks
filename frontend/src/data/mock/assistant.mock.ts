// TODO: Delete when AI assistant API is ready

export type SuggestionCard = {
  emoji: string;
  id: string;
  prompt: string;
  title: string;
};

export const MOCK_SUGGESTIONS: SuggestionCard[] = [
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

export const MOCK_PROMPT_CHIPS = [
  '"How many PTO days do I have?"',
  '"Does dental cover braces?"',
  '"Draft a leave email"',
] as const;
