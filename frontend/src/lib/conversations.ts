import type {
  ConversationDetail,
  ConversationSummary,
} from "@/types/conversation";

export async function deleteConversation(
  id: number,
  token: string,
): Promise<void> {
  const res = await authedFetch(`/api/backend/conversations/${id}`, token, {
    method: "DELETE",
  });
  if (!res.ok) {
    throw new Error(`Failed to delete conversation (${res.status})`);
  }
}

export async function getConversation(
  id: number,
  token: string,
): Promise<ConversationDetail> {
  const res = await authedFetch(`/api/backend/conversations/${id}`, token);
  if (!res.ok) {
    throw new Error(`Failed to load conversation (${res.status})`);
  }
  return (await res.json()) as ConversationDetail;
}

export async function listConversations(
  token: string,
): Promise<ConversationSummary[]> {
  const res = await authedFetch("/api/backend/conversations", token);
  if (!res.ok) {
    throw new Error(`Failed to load conversations (${res.status})`);
  }
  return (await res.json()) as ConversationSummary[];
}

export async function renameConversation(
  id: number,
  title: string,
  token: string,
): Promise<ConversationSummary> {
  const res = await authedFetch(`/api/backend/conversations/${id}`, token, {
    body: JSON.stringify({ title }),
    method: "PATCH",
  });
  if (!res.ok) {
    const detail = await res
      .json()
      .then((j: { detail?: string }) => j.detail)
      .catch(() => undefined);
    throw new Error(detail ?? `Failed to rename conversation (${res.status})`);
  }
  return (await res.json()) as ConversationSummary;
}

async function authedFetch(
  path: string,
  token: string,
  init: RequestInit = {},
): Promise<Response> {
  const headers = new Headers(init.headers);
  headers.set("Authorization", `Bearer ${token}`);
  if (init.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  return fetch(path, { ...init, headers });
}
