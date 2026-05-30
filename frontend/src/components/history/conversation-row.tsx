import type { ConversationSummary } from "@/types/conversation";

type Props = {
  conversation: ConversationSummary;
};

export function ConversationRow({ conversation }: Props) {
  return (
    <div className="flex items-center justify-between rounded-lg border border-border px-4 py-3 transition-colors hover:border-brand-purple-200 hover:bg-brand-purple-50 dark:hover:border-brand-purple-700 dark:hover:bg-brand-purple-950">
      <div className="flex flex-col gap-0.5 overflow-hidden">
        <span className="truncate text-sm font-medium text-foreground">
          {conversation.title}
        </span>
        <span className="text-xs text-muted-foreground">
          {conversation.message_count}{" "}
          {conversation.message_count === 1 ? "message" : "messages"}
        </span>
      </div>
      <span className="shrink-0 pl-4 text-xs text-muted-foreground">
        {formatRelativeTime(conversation.updated_at)}
      </span>
    </div>
  );
}

function formatRelativeTime(iso: string): string {
  const date = new Date(iso);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMin = Math.floor(diffMs / 60_000);
  const diffHr = Math.floor(diffMin / 60);
  const diffDay = Math.floor(diffHr / 24);

  if (diffMin < 1) return "just now";
  if (diffMin < 60) return `${diffMin}m ago`;
  if (diffHr < 24) return `${diffHr}h ago`;
  if (diffDay < 7) return `${diffDay}d ago`;
  return date.toLocaleDateString();
}
