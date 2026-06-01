from __future__ import annotations

import json
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from typing import cast

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from agent.graph import run_agent
from api.auth import get_current_user
from db.models import Conversation, Employee, Message
from db.session import AsyncSessionLocal

router = APIRouter(prefix="/chat", tags=["chat"])


# ── Dependency ─────────────────────────────────────────────────────────────────


async def get_current_employee(
    clerk_user_id: str = Depends(get_current_user),
) -> Employee:
    async with AsyncSessionLocal() as session:
        employee = await session.scalar(
            select(Employee).where(Employee.clerk_user_id == clerk_user_id)
        )
    if employee is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "Employee record not found. "
                "Call POST /employees/me to register before using the chat."
            ),
        )
    return employee


# ── Schema ─────────────────────────────────────────────────────────────────────


class ChatRequest(BaseModel):
    question: str
    conversation_id: int | None = None


# ── Route ──────────────────────────────────────────────────────────────────────


@router.post("", summary="Stream an AI answer and persist the conversation turn")
async def chat(
    body: ChatRequest,
    employee: Employee = Depends(get_current_employee),  # noqa: B008
) -> StreamingResponse:
    employee_id = cast(int, employee.id)

    # ── 1. Resolve or create conversation + load history ───────────────────────
    async with AsyncSessionLocal() as session:
        if body.conversation_id is not None:
            conversation = await session.scalar(
                select(Conversation)
                .where(
                    Conversation.id == body.conversation_id,
                    Conversation.employee_id == employee_id,
                )
                .options(selectinload(Conversation.messages))
            )
            if conversation is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Conversation not found.",
                )
        else:
            conversation = Conversation(employee_id=employee_id)
            conversation.messages = []
            session.add(conversation)
            await session.flush()  # assigns conversation.id

        # Snapshot history as plain tuples before the session closes
        history: list[tuple[str, str]] = [
            (str(msg.role), str(msg.content)) for msg in (conversation.messages or [])
        ]
        conversation_id = cast(int, conversation.id)
        await session.commit()

    # ── 2. Stream + collect ────────────────────────────────────────────────────
    collected: list[str] = []

    async def event_stream() -> AsyncGenerator[str, None]:
        # First event carries the conversation_id so the client can track it
        yield f"data: {json.dumps({'conversation_id': conversation_id})}\n\n"

        async for item in run_agent(employee_id, body.question, history):
            if isinstance(item, str):
                collected.append(item)
                yield f"data: {json.dumps({'text': item})}\n\n"
            elif isinstance(item, dict):
                # Special event (e.g. request_confirmation) — pass through as-is
                yield f"data: {json.dumps(item)}\n\n"

        yield "data: [DONE]\n\n"

        # ── 3. Persist after streaming ─────────────────────────────────────────
        now = datetime.now(UTC)
        full_response = "".join(collected)
        async with AsyncSessionLocal() as session:
            session.add_all(
                [
                    Message(
                        conversation_id=conversation_id,
                        role="user",
                        content=body.question,
                        created_at=now,
                    ),
                    Message(
                        conversation_id=conversation_id,
                        role="assistant",
                        content=full_response,
                        created_at=now,
                    ),
                ]
            )
            await session.execute(
                update(Conversation)
                .where(Conversation.id == conversation_id)
                .values(updated_at=now)
            )
            await session.commit()

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"X-Conversation-Id": str(conversation_id)},
    )
