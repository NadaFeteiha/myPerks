import { Bot, User } from "lucide-react";
import { useEffect, useRef } from "react";

import type { Message } from "@/types/chat";

import { cn } from "@/lib/cn";

type ChatMessagesProps = {
  messages: Message[];
};

export function ChatMessages({ messages }: ChatMessagesProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div className="flex w-full flex-col gap-6">
      {messages.map((message) => (
        <div
          className={cn(
            "flex w-full gap-3",
            message.role === "user" && "flex-row-reverse",
          )}
          key={message.id}
        >
          <div
            className={cn(
              "flex h-8 w-8 shrink-0 items-center justify-center rounded-lg",
              message.role === "user"
                ? "bg-brand-purple-600 text-white"
                : "bg-brand-purple-100 text-brand-purple-800",
            )}
          >
            {message.role === "user" ? (
              <User className="h-4 w-4" />
            ) : (
              <Bot className="h-4 w-4" />
            )}
          </div>
          <div
            className={cn(
              "flex max-w-[80%] rounded-2xl px-4 py-3 text-[13px] leading-relaxed",
              message.role === "user"
                ? "bg-brand-purple-600 text-white"
                : "bg-surface-2 text-foreground",
            )}
          >
            <div className="whitespace-pre-wrap">
              {renderContent(message.content)}
            </div>
          </div>
        </div>
      ))}
      <div className="pb-4" ref={bottomRef} />
    </div>
  );
}

function renderContent(text: string) {
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  return parts.map((part, i) =>
    part.startsWith("**") && part.endsWith("**") ? (
      <strong key={i}>{part.slice(2, -2)}</strong>
    ) : (
      part
    ),
  );
}
