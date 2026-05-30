export type ConversationDetail = {
  created_at: string;
  id: number;
  messages: MessageOut[];
  title: string;
  updated_at: string;
};
export type ConversationSummary = {
  id: number;
  message_count: number;
  title: string;
  updated_at: string;
};

type MessageOut = {
  content: string;
  created_at: string;
  id: number;
  role: "assistant" | "user";
};
