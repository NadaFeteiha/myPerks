import { Pencil } from "lucide-react";

import { ChatInput } from "@/components/assistant/chat-input";
import { WelcomeScreen } from "@/components/assistant/welcome-screen";

export const metadata = {
  title: "AI Assistant — MyPerks",
};

export default function AssistantPage() {
  return (
    <div className="flex flex-1 flex-col overflow-hidden">
      <div className="flex shrink-0 items-center justify-between border-b border-border px-5 py-2.5">
        <div className="flex items-center gap-2">
          <span className="h-2 w-2 rounded-full bg-brand-teal-400" />
          <span className="text-[13px] font-semibold text-foreground">New conversation</span>
        </div>
        <button
          type="button"
          className="flex h-7 w-7 items-center justify-center rounded-lg border border-border text-muted-foreground transition-colors hover:border-brand-purple-200 hover:text-brand-purple-600"
        >
          <Pencil className="h-3.5 w-3.5" />
        </button>
      </div>

      <div className="flex flex-1 items-center justify-center overflow-y-auto px-6 py-8">
        <WelcomeScreen />
      </div>

      <ChatInput />
    </div>
  );
}
