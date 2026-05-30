import Link from "next/link";

import type { ConversationSummary } from "@/types/conversation";

import { ConversationRow } from "./conversation-row";

type Props = {
  conversations: ConversationSummary[];
};

export function ConversationList({ conversations }: Props) {
  return (
    <ul className="mx-auto flex w-full max-w-3xl flex-col gap-2">
      {conversations.map((conversation) => (
        <li key={conversation.id}>
          <Link
            className="block"
            href={`/assistant?conversation=${conversation.id}`}
          >
            <ConversationRow conversation={conversation} />
          </Link>
        </li>
      ))}
    </ul>
  );
}
