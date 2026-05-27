export type Message = {
  content: string;
  id: string;
  role: "assistant" | "user";
  streaming?: boolean;
};
