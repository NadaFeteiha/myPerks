"use client";

import { Pencil } from "lucide-react";
import { useState } from "react";

import { ChatInput } from "@/components/assistant/chat-input";
import { ChatMessages } from "@/components/assistant/chat-messages";
import { WelcomeScreen } from "@/components/assistant/welcome-screen";

type Message = {
  content: string;
  id: string;
  role: "assistant" | "user";
};

export function AssistantClient() {
  const [messages, setMessages] = useState<Message[]>([]);

  const handleSendMessage = (content: string) => {
    const userMessage: Message = {
      content,
      id: Date.now().toString(),
      role: "user",
    };
    setMessages((prev) => [...prev, userMessage]);

    // Simulate AI response with static data
    setTimeout(() => {
      const aiResponse = getStaticResponse(content);
      const assistantMessage: Message = {
        content: aiResponse,
        id: (Date.now() + 1).toString(),
        role: "assistant",
      };
      setMessages((prev) => [...prev, assistantMessage]);
    }, 500);
  };

  const handleNewConversation = () => {
    setMessages([]);
  };

  return (
    <div className="flex flex-1 flex-col overflow-hidden">
      <div className="flex shrink-0 items-center justify-between border-b border-border px-5 py-2.5">
        <div className="flex items-center gap-2">
          <span className="h-2 w-2 rounded-full bg-brand-teal-400" />
          <span className="text-[13px] font-semibold text-foreground">
            {messages.length === 0 ? "New conversation" : "Conversation"}
          </span>
        </div>
        <button
          className="flex h-7 w-7 items-center justify-center rounded-lg border border-border text-muted-foreground transition-colors hover:border-brand-purple-200 hover:text-brand-purple-600 dark:hover:border-brand-purple-700 dark:hover:text-brand-purple-400"
          onClick={handleNewConversation}
          type="button"
        >
          <Pencil className="h-3.5 w-3.5" />
        </button>
      </div>

      {messages.length === 0 ? (
        <div className="flex flex-1 items-center justify-center overflow-y-auto px-6 py-8">
          <WelcomeScreen onSelectPrompt={handleSendMessage} />
        </div>
      ) : (
        <div className="flex flex-1 flex-col items-center overflow-y-auto px-6 py-8">
          <ChatMessages messages={messages} />
        </div>
      )}

      <ChatInput onSendMessage={handleSendMessage} />
    </div>
  );
}

function getStaticResponse(userMessage: string): string {
  const lowerMessage = userMessage.toLowerCase();

  if (lowerMessage.includes("pto") || lowerMessage.includes("vacation") || lowerMessage.includes("leave")) {
    return "You have **15 PTO days** remaining this year. Your next accrual of 1.25 days will be on July 1st. You've used 5 days so far in 2024.";
  }

  if (lowerMessage.includes("insurance") || lowerMessage.includes("dental") || lowerMessage.includes("cover")) {
    return "Your **Premium Dental Plan** does cover orthodontic treatment including braces at **50% coverage** up to a lifetime maximum of $2,500. You'll need to pay the remaining 50% out-of-pocket or use your FSA funds.";
  }

  if (lowerMessage.includes("email") || lowerMessage.includes("draft") || lowerMessage.includes("request")) {
    return "Here's a draft email for you:\n\n**Subject:** Time Off Request - June 1–5\n\nHi [Manager's Name],\n\nI would like to request time off from **June 1st to June 5th** for personal reasons. I'll make sure all my tasks are completed or delegated before my departure.\n\nPlease let me know if this works for the team schedule.\n\nBest regards,\n[Your Name]";
  }

  if (lowerMessage.includes("wellness") || lowerMessage.includes("budget")) {
    return "Your **wellness budget** of $500 expires on **December 31st, 2024**. You've currently used $320, leaving you with $180 remaining. Eligible expenses include gym memberships, fitness classes, and wellness apps.";
  }

  if (lowerMessage.includes("salary") || lowerMessage.includes("advance")) {
    return "You're eligible for a **salary advance** of up to $1,000, which would be repaid over 6 months through payroll deductions. The current interest rate is 0%. Would you like me to initiate the application process?";
  }

  return "I can help you with questions about your PTO balance, insurance coverage, wellness budget, salary advances, or draft HR emails. What would you like to know?";
}
