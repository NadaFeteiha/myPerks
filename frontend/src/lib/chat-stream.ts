import { logger } from "@sentry/nextjs";

export interface StreamChatOptions {
  conversationId: null | number;
  onConversationId: (id: number) => void;
  onToken: (token: string) => void;
  question: string;
  token: string;
}

export async function streamChat({
  conversationId,
  onConversationId,
  onToken,
  question,
  token,
}: StreamChatOptions): Promise<void> {
  const res = await fetch("/api/backend/chat", {
    body: JSON.stringify({
      conversation_id: conversationId ?? undefined,
      question,
    }),
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    method: "POST",
  });

  if (!res.ok) {
    const detail = await res
      .json()
      .then((j: { detail?: string }) => j.detail)
      .catch(() => undefined);
    throw new Error(
      `Chat request failed: ${res.status}${detail ? ` – ${detail}` : ` ${res.statusText}`}`,
    );
  }

  if (!res.body) {
    throw new Error("Response body is empty");
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });

    // SSE lines are separated by \n; events by \n\n
    const lines = buffer.split("\n");
    // Keep the incomplete last line in the buffer
    buffer = lines.pop() ?? "";

    for (const line of lines) {
      if (!line.startsWith("data: ")) continue;
      const data = line.slice(6).trim();

      if (data === "[DONE]") return;

      try {
        const parsed = JSON.parse(data) as Record<string, unknown>;
        if (typeof parsed.conversation_id === "number") {
          onConversationId(parsed.conversation_id);
        }
        if (typeof parsed.text === "string") {
          onToken(parsed.text);
        }
      } catch {
        logger.warn("Failed to parse SSE data", { data });
      }
    }
  }
}
