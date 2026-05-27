"""
Four processing steps of our agent.

Flow:
    1. router_node     — classify what the user needs (policy docs / live data / email)
    2. rag_node        — fetch relevant HR policy snippets from the vector store
    3. db_node         — fetch the employee's live leave balances and request history
    4. responder_node — combine all context and produce the final answer
"""

import logging
from datetime import UTC, datetime
from typing import Any, Literal, cast

from langchain_core.messages import AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel
from sqlalchemy import select

from db.models import Employee, VacationBalance
from db.session import AsyncSessionLocal
from rag.search import search_chunks
from settings import settings

from .state import AgentState

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# LLM and embedding model instances
# ---------------------------------------------------------------------------

_llm = ChatOpenAI(
    model="gpt-4o",
    api_key=settings.openai_api_key,
)

# ---------------------------------------------------------------------------
# System prompts
# ---------------------------------------------------------------------------

# Tells the LLM how to classify the user's intent
_ROUTER_PROMPT = """\
You are an intent classifier for an HR assistant called MyPerks.
Classify the user's question into one or more of these intents:
- "rag": needs information from HR policy or benefits documents
- "db": needs the employee's live data (vacation balance, request history)
- "email": user wants a ready-to-send HR email or request letter drafted

Rules:
- Email requests almost always also need "db" and/or "rag" context.
- Always return at least one intent.\
"""

# Tells the LLM how to write the final answer
_RESPONDER_PROMPT = """\
You are MyPerks, an AI-powered HR assistant. Answer the employee's question using \
ONLY the context provided below.

Guidelines:
- Be concise and accurate. Use exact numbers from HR data.
- Cite policy documents when quoting them (e.g. "According to the PTO Policy...").
- If the intent includes "email", format your entire response as a complete, \
ready-to-send professional email with Subject line, salutation, body, and sign-off.
- If context is empty or insufficient, say so honestly — never invent information.\
"""

# ---------------------------------------------------------------------------
# Router helpers
# ---------------------------------------------------------------------------


class _RouterOutput(BaseModel):
    """Structured output the router LLM must return."""

    intent: list[Literal["rag", "db", "email"]]


# Bind the LLM to always return a _RouterOutput object
_router_runnable = _llm.with_structured_output(_RouterOutput)


def _last_human_message(state: AgentState) -> str:
    """
    Return the text of the most recent human message in the conversation.

    We scan in reverse so we always get the latest question, even in
    multi-turn conversations.
    """
    for message in reversed(state["messages"]):
        if message.type == "human" and isinstance(message.content, str):
            return message.content
    return ""


# ---------------------------------------------------------------------------
# Node functions  (each receives the current AgentState and returns a partial
#                  update dict that LangGraph merges back into the state)
# ---------------------------------------------------------------------------


async def router_node(state: AgentState) -> dict[str, Any]:
    """
    Step 1 — Intent classification.

    Ask the LLM which data sources are needed to answer the user's question.
    The result (e.g. ["rag", "email"]) is stored in state["intent"] and used
    by the graph to decide which nodes to run next.
    """
    question = _last_human_message(state)
    try:
        result = cast(
            _RouterOutput,
            await _router_runnable.ainvoke(
                [
                    SystemMessage(content=_ROUTER_PROMPT),
                    {"role": "user", "content": question},
                ]
            ),
        )
        # Only keep valid intent values; discard anything unexpected
        intent = [i for i in result.intent if i in ("rag", "db", "email")]
    except Exception:
        logger.exception("Router failed — defaulting to rag")
        intent = ["rag"]

    # Always return at least one intent so the graph never gets stuck
    return {"intent": intent or ["rag"]}


async def rag_node(state: AgentState) -> dict[str, Any]:
    """
    Step 2a — Policy document retrieval (RAG = Retrieval-Augmented Generation).

    Calls search_chunks to embed the question and return the top-5 most
    relevant DocumentChunk rows from documents uploaded via POST /upload/callback.
    Includes filename and page numbers so the responder can cite sources.
    """
    question = _last_human_message(state)
    try:
        async with AsyncSessionLocal() as db:
            chunks = await search_chunks(query=question, session=db, top_k=5)

        if not chunks:
            return {"rag_context": ""}

        rag_context = "\n\n---\n\n".join(
            f"[{c.filename}, p.{c.page_start}–{c.page_end}]\n{c.content}"
            for c in chunks
        )
    except Exception:
        logger.exception("RAG node failed")
        rag_context = ""

    return {"rag_context": rag_context}


async def db_node(state: AgentState) -> dict[str, Any]:
    """
    Step 2b — Live employee data retrieval.

    Fetches three things for the logged-in employee:
    - Basic profile (name, department)
    - Leave balances for the current year
    - The 5 most recent HR requests

    The result is a human-readable text block stored in state["db_context"]
    that the responder can quote directly (e.g. "You have 5 PTO days left").
    """
    employee_id = state["employee_id"]
    current_year = datetime.now(UTC).year

    try:
        async with AsyncSessionLocal() as db:
            # Fetch the employee profile
            employee = (
                await db.execute(select(Employee).where(Employee.id == employee_id))
            ).scalar_one_or_none()

            # Fetch leave balances for the current calendar year
            balances = (
                (
                    await db.execute(
                        select(VacationBalance).where(
                            VacationBalance.employee_id == employee_id,
                            VacationBalance.year == current_year,
                        )
                    )
                )
                .scalars()
                .all()
            )

        # Build a plain-text summary the LLM can read directly
        lines: list[str] = []

        if employee:
            lines.append(f"Employee: {employee.name} ({employee.department or 'N/A'})")

        if balances:
            lines.append(f"\nLeave Balances ({current_year}):")
            for b in balances:
                used = f"{int(b.used_days)}/{int(b.total_days)} days used"
                remaining = f"({int(b.remaining_days)} remaining)"
                lines.append(f"  {b.leave_type}: {used} {remaining}")

        db_context = "\n".join(lines)

    except Exception:
        logger.exception("DB node failed")
        db_context = ""

    return {"db_context": db_context}


async def responder_node(state: AgentState) -> dict[str, Any]:
    """
    Step 3 — Final answer generation.

    Combines whatever context the earlier nodes collected (policy docs and/or
    employee data) into a single prompt and calls the LLM to produce the answer.

    If "email" is in the intent, the prompt instructs the LLM to format the
    entire response as a professional, ready-to-send email.
    """
    question = _last_human_message(state)
    intent = state.get("intent", [])
    rag_context = state.get("rag_context", "")
    db_context = state.get("db_context", "")

    # Build the context block from whichever sources were retrieved
    context_parts: list[str] = []
    if rag_context:
        context_parts.append(f"<policy_documents>\n{rag_context}\n</policy_documents>")
    if db_context:
        context_parts.append(f"<employee_data>\n{db_context}\n</employee_data>")

    # Add an extra instruction when the user wants an email draft
    email_note = (
        "\n\nThe employee wants an email draft. Format your entire response as a "
        "complete, ready-to-send professional email."
        if "email" in intent
        else ""
    )

    user_content = (
        f"{''.join(context_parts) or 'No additional context available.'}"
        f"{email_note}\n\nEmployee question: {question}"
    )

    response = await _llm.ainvoke(
        [
            SystemMessage(content=_RESPONDER_PROMPT),
            {"role": "user", "content": user_content},
        ]
    )

    return {"messages": [AIMessage(content=str(response.content))]}
