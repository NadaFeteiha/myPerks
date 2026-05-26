"use client";

import { useAuth, useUser } from "@clerk/nextjs";
import { Pencil } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";

import type { Message } from "@/types/chat";

import { ChatInput } from "@/components/assistant/chat-input";
import { ChatMessages } from "@/components/assistant/chat-messages";
import { WelcomeScreen } from "@/components/assistant/welcome-screen";
import { streamChat } from "@/lib/chat-stream";

export function AssistantClient() {
  const { getToken } = useAuth();
  const { user } = useUser();

  const [messages, setMessages] = useState<Message[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<null | string>(null);

  // Persisted across turns within the same conversation session
  const conversationIdRef = useRef<null | number>(null);
  // Ensure only one registration attempt per mount
  const registeredRef = useRef(false);

  // Auto-register the employee row on first load so POST /chat never 404s
  useEffect(() => {
    if (!user || registeredRef.current) return;
    registeredRef.current = true;

    void (async () => {
      try {
        const token = await getToken();
        if (!token) return;
        await fetch("/api/backend/employees/me", {
          body: JSON.stringify({
            department: null,
            email: user.primaryEmailAddress?.emailAddress ?? "",
            name: user.fullName ?? user.firstName ?? "Employee",
          }),
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
          method: "POST",
        });
      } catch {
        // Non-critical — chat will show a clearer error if needed
      }
    })();
  }, [user, getToken]);

  const handleSendMessage = useCallback(
    async (content: string) => {
      setError(null);

      const userMessage: Message = {
        content,
        id: crypto.randomUUID(),
        role: "user",
      };

      const assistantId = crypto.randomUUID();
      const assistantPlaceholder: Message = {
        content: "",
        id: assistantId,
        role: "assistant",
        streaming: true,
      };

      setMessages((prev) => [...prev, userMessage, assistantPlaceholder]);
      setIsStreaming(true);

      try {
        const token = await getToken();
        if (!token) throw new Error("Not authenticated");

        await streamChat({
          conversationId: conversationIdRef.current,
          onConversationId: (id) => {
            conversationIdRef.current = id;
          },
          onToken: (chunk) => {
            setMessages((prev) =>
              prev.map((m) =>
                m.id === assistantId
                  ? { ...m, content: m.content + chunk }
                  : m,
              ),
            );
          },
          question: content,
          token,
        });

        // Mark streaming done
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantId ? { ...m, streaming: false } : m,
          ),
        );
      } catch (err) {
        const message =
          err instanceof Error ? err.message : "Something went wrong";
        setError(message);
        // Remove the empty placeholder on error
        setMessages((prev) => prev.filter((m) => m.id !== assistantId));
      } finally {
        setIsStreaming(false);
      }
    },
    [getToken],
  );

  const handleNewConversation = useCallback(() => {
    conversationIdRef.current = null;
    setMessages([]);
    setError(null);
  }, []);

  return (
    <div className="flex flex-1 flex-col overflow-hidden">
      <div className="flex shrink-0 items-center justify-between border-b border-border px-5 py-2.5">
        <div className="flex items-center gap-2">
          <span
            className={`h-2 w-2 rounded-full ${isStreaming ? "animate-pulse bg-brand-teal-400" : "bg-brand-teal-400"}`}
          />
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

      {error && (
        <p className="shrink-0 px-5 pb-1 text-center text-[12px] text-destructive">
          {error}
        </p>
      )}

      <ChatInput disabled={isStreaming} onSendMessage={handleSendMessage} />
    </div>
  );
}
