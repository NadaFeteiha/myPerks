from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import desc, func, select
from sqlalchemy.orm import selectinload

from api.chat import get_current_employee
from db.models import Conversation, Employee, Message
from db.session import AsyncSessionLocal

router = APIRouter(prefix="/conversations", tags=["conversations"])

# ── Schemas ────────────────────────────────────────────────────────────────────


class ConversationSummary(BaseModel):
    id: int
    title: str
    updated_at: datetime
    message_count: int


class MessageOut(BaseModel):
    id: int
    role: str
    content: str
    created_at: datetime


class ConversationDetail(BaseModel):
    id: int
    title: str
    created_at: datetime
    updated_at: datetime
    messages: list[MessageOut]


# ── Helpers ────────────────────────────────────────────────────────────────────

TITLE_MAX_LEN = 60


def _derive_title(stored_title: str | None, first_user_message: str | None) -> str:
    """Use the stored title if present; otherwise fall back to the first user
    message truncated to TITLE_MAX_LEN chars. Final fallback: 'New conversation'."""
    if stored_title:
        return stored_title
    if first_user_message:
        cleaned = first_user_message.strip().replace("\n", " ")
        if len(cleaned) <= TITLE_MAX_LEN:
            return cleaned
        return cleaned[: TITLE_MAX_LEN - 1].rstrip() + "…"
    return "New conversation"


# ── Routes ─────────────────────────────────────────────────────────────────────


@router.get("", response_model=list[ConversationSummary])
async def list_conversations(
    employee: Employee = Depends(get_current_employee),
) -> list[ConversationSummary]:
    """List the current employee's conversations, newest first."""
    async with AsyncSessionLocal() as session:
        # Subquery: count messages per conversation
        msg_count_subq = (
            select(
                Message.conversation_id,
                func.count(Message.id).label("message_count"),
            )
            .group_by(Message.conversation_id)
            .subquery()
        )

        # Subquery: first user message per conversation (for title fallback)
        first_user_msg_subq = (
            select(
                Message.conversation_id,
                func.min(Message.id).label("first_msg_id"),
            )
            .where(Message.role == "user")
            .group_by(Message.conversation_id)
            .subquery()
        )

        stmt = (
            select(
                Conversation.id,
                Conversation.title,
                Conversation.updated_at,
                func.coalesce(msg_count_subq.c.message_count, 0).label("message_count"),
                Message.content.label("first_user_content"),
            )
            .outerjoin(
                msg_count_subq,
                msg_count_subq.c.conversation_id == Conversation.id,
            )
            .outerjoin(
                first_user_msg_subq,
                first_user_msg_subq.c.conversation_id == Conversation.id,
            )
            .outerjoin(Message, Message.id == first_user_msg_subq.c.first_msg_id)
            .where(Conversation.employee_id == employee.id)
            .order_by(desc(Conversation.updated_at))
        )

        rows = (await session.execute(stmt)).all()

    return [
        ConversationSummary(
            id=row.id,
            title=_derive_title(row.title, row.first_user_content),
            updated_at=row.updated_at,
            message_count=row.message_count,
        )
        for row in rows
    ]


@router.get("/{conversation_id}", response_model=ConversationDetail)
async def get_conversation(
    conversation_id: int,
    employee: Employee = Depends(get_current_employee),
) -> ConversationDetail:
    """Get a single conversation with all its messages, oldest first."""
    async with AsyncSessionLocal() as session:
        conversation = await session.scalar(
            select(Conversation)
            .where(
                Conversation.id == conversation_id,
                Conversation.employee_id == employee.id,
            )
            .options(selectinload(Conversation.messages))
        )

    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )
    first_user = next(
        (m.content for m in conversation.messages if m.role == "user"), None
    )

    return ConversationDetail(
        id=conversation.id,
        title=_derive_title(conversation.title, first_user),
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        messages=[
            MessageOut(
                id=m.id,
                role=m.role,
                content=m.content,
                created_at=m.created_at,
            )
            for m in conversation.messages
        ],
    )
