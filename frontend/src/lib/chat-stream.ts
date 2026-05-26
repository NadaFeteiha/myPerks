
export interface StreamChatOptions {
  question: string;
  conversationId: number | null;
  token: string;
  onConversationId: (id: number) => void;
  onToken: (token: string) => void;
}

export async function streamChat({
  question,
  conversationId,
  token,
  onConversationId,
  onToken,
}: StreamChatOptions): Promise<void> {
  const res = await fetch("/api/backend/chat", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({
      question,
      conversation_id: conversationId ?? undefined,
    }),
  });

  if (!res.ok) {
    throw new Error(`Chat request failed: ${res.status} ${res.statusText}`);
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
        // Malformed SSE data — skip silently
      }
    }
  }
}
