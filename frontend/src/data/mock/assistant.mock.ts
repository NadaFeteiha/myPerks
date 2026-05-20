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

// TODO: Delete when AI assistant API is ready — replace with real LLM API call
export function getMockAIResponse(userMessage: string): string {
  const msg = userMessage.toLowerCase();

  if (msg.includes("pto") || msg.includes("vacation") || msg.includes("leave")) {
    return "You have **15 PTO days** remaining this year. Your next accrual of 1.25 days will be on July 1st. You've used 5 days so far in 2024.";
  }
  if (msg.includes("insurance") || msg.includes("dental") || msg.includes("cover")) {
    return "Your **Premium Dental Plan** does cover orthodontic treatment including braces at **50% coverage** up to a lifetime maximum of $2,500. You'll need to pay the remaining 50% out-of-pocket or use your FSA funds.";
  }
  if (msg.includes("email") || msg.includes("draft") || msg.includes("request")) {
    return "Here's a draft email for you:\n\n**Subject:** Time Off Request - June 1–5\n\nHi [Manager's Name],\n\nI would like to request time off from **June 1st to June 5th** for personal reasons. I'll make sure all my tasks are completed or delegated before my departure.\n\nPlease let me know if this works for the team schedule.\n\nBest regards,\n[Your Name]";
  }
  if (msg.includes("wellness") || msg.includes("budget")) {
    return "Your **wellness budget** of $500 expires on **December 31st, 2024**. You've currently used $320, leaving you with $180 remaining. Eligible expenses include gym memberships, fitness classes, and wellness apps.";
  }
  if (msg.includes("salary") || msg.includes("advance")) {
    return "You're eligible for a **salary advance** of up to $1,000, which would be repaid over 6 months through payroll deductions. The current interest rate is 0%. Would you like me to initiate the application process?";
  }

  return "I can help you with questions about your PTO balance, insurance coverage, wellness budget, salary advances, or draft HR emails. What would you like to know?";
}
