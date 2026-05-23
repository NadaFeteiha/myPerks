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
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from pydantic import BaseModel
from sqlalchemy import select

from db.models import DocumentChunk, Employee, VacationBalance
from db.session import AsyncSessionLocal
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

_embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small",
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

    1. Embed the user's question into a vector.
    2. Find the 5 document chunks whose embeddings are closest (cosine distance).
    3. Join them into a single text block stored in state["rag_context"].

    The responder node will inject this text into the LLM prompt as
    grounding context so answers are based on real HR policy documents.
    """
    question = _last_human_message(state)
    try:
        # Convert the question to a numeric vector for similarity search
        query_vector = await _embeddings.aembed_query(question)

        async with AsyncSessionLocal() as db:
            rows = (
                await db.execute(
                    select(DocumentChunk.content, DocumentChunk.document_id)
                    .where(DocumentChunk.embedding.is_not(None))
                    .order_by(DocumentChunk.embedding.cosine_distance(query_vector))
                    .limit(5)
                )
            ).fetchall()

        if not rows:
            return {"rag_context": ""}

        # Separate chunks with a divider so the LLM can tell them apart
        rag_context = "\n\n---\n\n".join(
            f"[Document {row.document_id}]\n{row.content}" for row in rows
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
                await db.execute(
                    select(VacationBalance).where(
                        VacationBalance.employee_id == employee_id,
                        VacationBalance.year == current_year,
                    )
                )
            ).scalars().all()

            # Fetch the 5 most recent HR requests (newest first)
            # recent_requests = (
            #     await db.execute(
            #         select(RequestHistory)
            #         .where(RequestHistory.employee_id == employee_id)
            #         .order_by(RequestHistory.created_at.desc())
            #         .limit(5)
            #     )
            # ).scalars().all()

        # Build a plain-text summary the LLM can read directly
        lines: list[str] = []

        if employee:
            lines.append(f"Employee: {employee.name} ({employee.department or 'N/A'})")

        if balances:
            lines.append(f"\nLeave Balances ({current_year}):")
            for b in balances:
                lines.append(
                    f"  {b.leave_type}: {b.used_days}/{b.total_days} days used"
                    f" ({b.remaining_days:.1f} remaining)"
                )

        # if recent_requests:
        #     lines.append("\nRecent Requests (last 5):")
        #     for r in recent_requests:
        #         date_str = (
        #             r.created_at.strftime("%Y-%m-%d")
        #             if r.created_at is not None else "N/A"
        #         )
        #         lines.append(f"  [{date_str}] {r.type} — {r.status}")

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
