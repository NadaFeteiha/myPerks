import json
from collections.abc import AsyncGenerator
from typing import cast

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import select

from agent.graph import run_agent
from api.auth import get_current_user
from db.models import Employee
from db.session import AsyncSessionLocal

router = APIRouter(prefix="/chat", tags=["chat"])


async def get_current_employee(
    clerk_user_id: str = Depends(get_current_user),
) -> Employee:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Employee).where(Employee.clerk_user_id == clerk_user_id)
        )
        employee = result.scalar_one_or_none()

    if employee is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found",
        )

    return employee


class ChatRequest(BaseModel):
    question: str


@router.post("")
async def chat(
    body: ChatRequest,
    employee: Employee = Depends(get_current_employee),  # noqa: B008
) -> StreamingResponse:
    """Stream the agent's answer """
    employee_id = cast(int, employee.id)

    async def event_stream() -> AsyncGenerator[str, None]:
        async for chunk in run_agent(employee_id, body.question):
            yield f"data: {json.dumps({'text': chunk})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
