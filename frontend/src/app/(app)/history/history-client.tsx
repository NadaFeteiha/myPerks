"use client";

import { useAuth } from "@clerk/nextjs";
import { useCallback, useEffect, useState } from "react";

import type { ConversationSummary } from "@/types/conversation";

import { ConversationList } from "@/components/history/conversation-list";

export function HistoryClient() {
  const { getToken } = useAuth();

  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<null | string>(null);

  const loadConversations = useCallback(async () => {
    setError(null);
    setIsLoading(true);
    try {
      const token = await getToken();
      if (!token) throw new Error("Not authenticated");

      const res = await fetch("/api/backend/conversations", {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (!res.ok) {
        throw new Error(`Failed to load conversations (${res.status})`);
      }

      const data = (await res.json()) as ConversationSummary[];
      setConversations(data);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Could not load conversations",
      );
    } finally {
      setIsLoading(false);
    }
  }, [getToken]);

  useEffect(() => {
    void loadConversations();
  }, [loadConversations]);

  return (
    <div className="flex flex-1 flex-col overflow-hidden">
      <div className="flex shrink-0 items-center justify-between border-b border-border px-5 py-2.5">
        <span className="text-[13px] font-semibold text-foreground">
          History
        </span>
      </div>

      <div className="flex flex-1 flex-col overflow-y-auto px-6 py-8">
        {isLoading ? (
          <p className="text-center text-sm text-muted-foreground">
            Loading conversations…
          </p>
        ) : error ? (
          <p className="text-center text-sm text-destructive">{error}</p>
        ) : conversations.length === 0 ? (
          <p className="text-center text-sm text-muted-foreground">
            No conversations yet. Start chatting with the AI Assistant to see
            them here.
          </p>
        ) : (
          <ConversationList conversations={conversations} />
        )}
      </div>
    </div>
  );
}
