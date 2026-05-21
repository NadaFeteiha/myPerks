import json
from typing import AsyncGenerator, cast

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from agent.graph import run_agent
from db.models import Employee

from .deps import get_current_employee

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    question: str


@router.post("")
async def chat(
    body: ChatRequest,
    employee: Employee = Depends(get_current_employee),
) -> StreamingResponse:
    """Stream the agent's answer as Server-Sent Events (SSE).

    Each event:  data: {"text": "<token>"}\n\n
    Final event: data: [DONE]\n\n
    """
    employee_id = cast(int, employee.id)

    async def event_stream() -> AsyncGenerator[str, None]:
        async for chunk in run_agent(employee_id, body.question):
            yield f"data: {json.dumps({'text': chunk})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
