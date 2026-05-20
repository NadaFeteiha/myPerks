"use client";

import { Pencil } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";

import type { Message } from "@/types/chat";

import { ChatInput } from "@/components/assistant/chat-input";
import { ChatMessages } from "@/components/assistant/chat-messages";
import { WelcomeScreen } from "@/components/assistant/welcome-screen";
import { getMockAIResponse } from "@/data/mock/assistant.mock";

export function AssistantClient() {
  const [messages, setMessages] = useState<Message[]>([]);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);

  useEffect(() => () => clearTimeout(timeoutRef.current), []);

  const handleSendMessage = useCallback((content: string) => {
    const userMessage: Message = {
      content,
      id: crypto.randomUUID(),
      role: "user",
    };
    setMessages((prev) => [...prev, userMessage]);

    // TODO: Replace with real AI API call
    clearTimeout(timeoutRef.current);
    timeoutRef.current = setTimeout(() => {
      const assistantMessage: Message = {
        content: getMockAIResponse(content),
        id: crypto.randomUUID(),
        role: "assistant",
      };
      setMessages((prev) => [...prev, assistantMessage]);
    }, 500);
  }, []);

  const handleNewConversation = useCallback(() => {
    clearTimeout(timeoutRef.current);
    setMessages([]);
  }, []);

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
          aria-label="New conversation"
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
