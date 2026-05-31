"use client";

import { useAuth } from "@clerk/nextjs";
import { useEffect, useState } from "react";

import type { ConversationSummary } from "@/types/conversation";

import { ConversationList } from "@/components/history/conversation-list";
import { listConversations } from "@/lib/conversations";

export function HistoryClient() {
  const { getToken } = useAuth();

  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<null | string>(null);

  useEffect(() => {
    let cancelled = false;

    void (async () => {
      try {
        const token = await getToken();
        if (!token) throw new Error("Not authenticated");

        const data = await listConversations(token);

        if (!cancelled) {
          setConversations(data);
          setIsLoading(false);
        }
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof Error ? err.message : "Could not load conversations",
          );
          setIsLoading(false);
        }
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [getToken]);

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
