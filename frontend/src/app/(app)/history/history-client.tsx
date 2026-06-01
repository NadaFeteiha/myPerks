"use client";

import { useAuth } from "@clerk/nextjs";
import { Search } from "lucide-react";
import { useEffect, useRef, useState } from "react";

import type { ConversationSummary } from "@/types/conversation";

import { ConfirmDialog } from "@/components/history/confirm-dialog";
import { ConversationList } from "@/components/history/conversation-list";
import { RenameDialog } from "@/components/history/rename-dialog";
import {
  deleteConversation,
  listConversations,
  renameConversation,
} from "@/lib/conversations";

const SEARCH_DEBOUNCE_MS = 300;

export function HistoryClient() {
  const { getToken } = useAuth();

  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<null | string>(null);

  const [query, setQuery] = useState("");
  const [activeQuery, setActiveQuery] = useState("");

  const [renameTarget, setRenameTarget] = useState<ConversationSummary | null>(
    null,
  );
  const [isRenaming, setIsRenaming] = useState(false);
  const [renameError, setRenameError] = useState<null | string>(null);

  const [deleteTarget, setDeleteTarget] = useState<ConversationSummary | null>(
    null,
  );
  const [isDeleting, setIsDeleting] = useState(false);

  // Track the most recent request so older ones don't clobber newer state
  const requestIdRef = useRef(0);

  // Debounce: 300ms after the user stops typing, treat query as the active one
  useEffect(() => {
    const handle = setTimeout(() => {
      setActiveQuery(query);
    }, SEARCH_DEBOUNCE_MS);
    return () => clearTimeout(handle);
  }, [query]);

  // Fetch whenever activeQuery changes
  useEffect(() => {
    const requestId = ++requestIdRef.current;

    void (async () => {
      setIsLoading(true);
      setError(null);

      try {
        const token = await getToken();
        if (!token) throw new Error("Not authenticated");

        const data = await listConversations(token, activeQuery);
        if (requestId === requestIdRef.current) {
          setConversations(data);
          setIsLoading(false);
        }
      } catch (err) {
        if (requestId === requestIdRef.current) {
          setError(
            err instanceof Error ? err.message : "Could not load conversations",
          );
          setIsLoading(false);
        }
      }
    })();
  }, [activeQuery, getToken]);

  async function handleRenameConfirm(newTitle: string) {
    if (!renameTarget) return;
    setIsRenaming(true);
    setRenameError(null);

    try {
      const token = await getToken();
      if (!token) throw new Error("Not authenticated");

      const updated = await renameConversation(
        renameTarget.id,
        newTitle,
        token,
      );
      setConversations((prev) =>
        prev.map((c) => (c.id === updated.id ? updated : c)),
      );
      setRenameTarget(null);
    } catch (err) {
      setRenameError(
        err instanceof Error ? err.message : "Could not rename conversation",
      );
    } finally {
      setIsRenaming(false);
    }
  }

  async function handleDeleteConfirm() {
    if (!deleteTarget) return;
    setIsDeleting(true);

    try {
      const token = await getToken();
      if (!token) throw new Error("Not authenticated");

      await deleteConversation(deleteTarget.id, token);
      setConversations((prev) => prev.filter((c) => c.id !== deleteTarget.id));
      setDeleteTarget(null);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Could not delete conversation",
      );
      setDeleteTarget(null);
    } finally {
      setIsDeleting(false);
    }
  }

  const hasActiveQuery = activeQuery.trim().length > 0;

  return (
    <div className="flex flex-1 flex-col overflow-hidden">
      <div className="flex shrink-0 items-center justify-between border-b border-border px-5 py-2.5">
        <span className="text-[13px] font-semibold text-foreground">
          History
        </span>
      </div>

      <div className="mx-auto w-full max-w-3xl px-6 pt-6">
        <div className="relative">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <input
            className="w-full rounded-lg border border-border bg-background py-2 pl-9 pr-3 text-sm text-foreground outline-none transition-colors placeholder:text-muted-foreground focus:border-brand-purple-400"
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                e.preventDefault();
                setActiveQuery(query);
              }
            }}
            placeholder="Search conversations…"
            type="text"
            value={query}
          />
        </div>
      </div>

      <div className="flex flex-1 flex-col overflow-y-auto px-6 pb-8 pt-4">
        {isLoading ? (
          <p className="text-center text-sm text-muted-foreground">
            Loading conversations…
          </p>
        ) : error ? (
          <p className="text-center text-sm text-destructive">{error}</p>
        ) : conversations.length === 0 ? (
          <p className="text-center text-sm text-muted-foreground">
            {hasActiveQuery
              ? `No conversations match "${activeQuery}".`
              : "No conversations yet. Start chatting with the AI Assistant to see them here."}
          </p>
        ) : (
          <ConversationList
            conversations={conversations}
            onDelete={(c) => setDeleteTarget(c)}
            onRename={(c) => {
              setRenameError(null);
              setRenameTarget(c);
            }}
          />
        )}
      </div>

      <RenameDialog
        error={renameError}
        initialTitle={renameTarget?.title ?? ""}
        isOpen={renameTarget !== null}
        isPending={isRenaming}
        key={renameTarget?.id ?? "closed"}
        onCancel={() => {
          if (!isRenaming) {
            setRenameTarget(null);
            setRenameError(null);
          }
        }}
        onSubmit={handleRenameConfirm}
      />

      <ConfirmDialog
        confirmLabel="Delete"
        description={
          deleteTarget
            ? `"${deleteTarget.title}" and all its messages will be permanently deleted. This can't be undone.`
            : undefined
        }
        isOpen={deleteTarget !== null}
        isPending={isDeleting}
        onCancel={() => {
          if (!isDeleting) setDeleteTarget(null);
        }}
        onConfirm={handleDeleteConfirm}
        title="Delete this conversation?"
        variant="destructive"
      />
    </div>
  );
}
