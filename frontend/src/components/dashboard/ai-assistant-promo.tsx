import Link from "next/link";
import { MessageCircle, Sparkles } from "lucide-react";

const PROMPT_CHIPS = [
  '"How many PTO days do I have?"',
  '"Does dental cover braces?"',
  '"Draft a leave email"',
] as const;

export function AIAssistantPromo() {
  return (
    <div className="flex items-center justify-between gap-4 rounded-xl border border-brand-purple-200 bg-brand-purple-50 px-5 py-5">
      <div className="flex items-start gap-3">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-brand-purple-600">
          <Sparkles className="h-[18px] w-[18px] text-white" />
        </div>
        <div>
          <p className="mb-0.5 text-[14px] font-semibold text-brand-purple-900">
            Benefits AI Assistant
          </p>
          <p className="max-w-sm text-[12px] leading-relaxed text-brand-purple-800 opacity-80">
            Ask anything about your benefits — vacation balance, insurance coverage, salary
            advances, or generate a ready-to-send HR email in seconds.
          </p>
          <div className="mt-2.5 flex flex-wrap gap-1.5">
            {PROMPT_CHIPS.map((chip) => (
              <span
                key={chip}
                className="rounded-full border border-brand-purple-200 bg-brand-purple-50 px-2.5 py-0.5 text-[11px] text-brand-purple-800"
              >
                {chip}
              </span>
            ))}
          </div>
        </div>
      </div>
      <Link
        href="/assistant"
        className="flex shrink-0 items-center gap-1.5 rounded-lg bg-brand-purple-600 px-4 py-2 text-[12px] font-semibold text-white transition-colors hover:bg-brand-purple-800"
      >
        <MessageCircle className="h-3.5 w-3.5" />
        Open assistant
      </Link>
    </div>
  );
}
