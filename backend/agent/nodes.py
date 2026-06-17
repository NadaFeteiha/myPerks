"""
Five processing steps of our agent.

Flow:
    1. router_node     — classify what the user needs (policy docs / live data / email / request)
    2. rag_node        — fetch relevant HR policy snippets from the vector store
    3. db_node         — fetch the employee's live leave balances and request history
    4. request_node    — extract structured request details when user wants to submit a request
    5. responder_node — combine all context and produce the final answer
"""

import json
import logging
import re
from datetime import UTC, datetime, timedelta
from datetime import date as _date
from typing import Any, Literal, cast

import holidays as _holidays
from langchain_core.messages import AIMessage, SystemMessage
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from sqlalchemy import select

from db.models import Employee, RequestHistory, VacationBalance
from db.session import AsyncSessionLocal
from rag.search import search_chunks
from settings import settings

from .state import AgentState

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Working-day helpers
# ---------------------------------------------------------------------------


def _count_working_days(start: _date, end: _date) -> int:
    """Count Mon–Fri days between start and end (inclusive), excluding US federal holidays."""
    if end < start:
        return 0
    federal_holidays = _holidays.country_holidays(
        "US", years=range(start.year, end.year + 1)
    )
    count = 0
    current = start
    while current <= end:
        if current.weekday() < 5 and current not in federal_holidays:
            count += 1
        current += timedelta(days=1)
    return count


def _add_working_days(start: _date, num_days: int) -> _date:
    """Return the date that is exactly `num_days` working days from start (inclusive)."""
    if num_days <= 0:
        return start
    federal_holidays = _holidays.country_holidays(
        "US", years=range(start.year, start.year + 2)
    )
    count = 0
    current = start
    while True:
        if current.weekday() < 5 and current not in federal_holidays:
            count += 1
            if count == num_days:
                return current
        current += timedelta(days=1)


def _build_breakdown(start: _date, end: _date) -> list[dict[str, str]]:
    """
    Return a day-by-day breakdown from start to end, marking each day as
    "work", "weekend", or "holiday" (with the holiday name when applicable).
    """
    if end < start:
        return []
    federal_holidays = _holidays.country_holidays(
        "US", years=range(start.year, end.year + 1)
    )
    rows: list[dict[str, str]] = []
    current = start
    while current <= end:
        if current.weekday() >= 5:
            entry: dict[str, str] = {
                "date": current.isoformat(),
                "day": current.strftime("%a"),
                "status": "weekend",
            }
        elif current in federal_holidays:
            entry = {
                "date": current.isoformat(),
                "day": current.strftime("%a"),
                "status": "holiday",
                "name": str(federal_holidays[current]),
            }
        else:
            entry = {
                "date": current.isoformat(),
                "day": current.strftime("%a"),
                "status": "work",
            }
        rows.append(entry)
        current += timedelta(days=1)
    return rows


async def _get_remaining_leave(employee_id: int, leave_type: str) -> float | None:
    """Return remaining leave days for the employee for the current year, or None if unknown."""
    current_year = datetime.now(UTC).year
    try:
        async with AsyncSessionLocal() as db:
            balance = (
                await db.execute(
                    select(VacationBalance).where(
                        VacationBalance.employee_id == employee_id,
                        VacationBalance.leave_type == leave_type,
                        VacationBalance.year == current_year,
                    )
                )
            ).scalar_one_or_none()
        return float(balance.remaining_days) if balance is not None else None
    except Exception:
        logger.exception("Balance check failed")
        return None


async def _find_leave_conflict(
    employee_id: int,
    req_type: str,
    start: _date,
    end: _date,
) -> dict[str, str] | None:
    """
    Return the first pending/approved leave request that overlaps [start, end],
    or None if no conflict exists.
    """
    leave_types = {"vacation", "sick", "pto"}
    if req_type not in leave_types:
        return None  # reimbursements can't overlap

    try:
        async with AsyncSessionLocal() as db:
            rows = (
                (
                    await db.execute(
                        select(RequestHistory).where(
                            RequestHistory.employee_id == employee_id,
                            RequestHistory.status.in_(["pending", "approved"]),
                            RequestHistory.type.in_(list(leave_types)),
                            # Bound to requests submitted in the previous year or later;
                            # leave requests for the target date range can't predate that.
                            RequestHistory.created_at
                            >= datetime(start.year - 1, 1, 1, tzinfo=UTC),
                        )
                    )
                )
                .scalars()
                .all()
            )
    except Exception:
        logger.exception("Conflict check DB query failed")
        return None

    for row in rows:
        if not row.body:
            continue
        try:
            body = json.loads(cast(str, row.body))
            ex_start = _date.fromisoformat(body["start_date"])
            ex_end = _date.fromisoformat(body["end_date"])
        except (KeyError, ValueError):
            continue
        # Overlap: the ranges share at least one calendar day
        if max(start, ex_start) <= min(end, ex_end):
            return {
                "type": str(row.type),
                "status": str(row.status),
                "start_date": ex_start.isoformat(),
                "end_date": ex_end.isoformat(),
            }
    return None


# ---------------------------------------------------------------------------
# LLM and embedding model instances
# ---------------------------------------------------------------------------

if settings.ai_backend == "ollama":
    _llm: ChatOllama | ChatOpenAI = ChatOllama(
        model=settings.ollama_chat_model,
        base_url=settings.ollama_base_url,
        temperature=0,
    )
elif settings.ai_backend == "groq":
    _llm = ChatOpenAI(
        model=settings.groq_chat_model,
        api_key=settings.groq_api_key.get_secret_value(),
        base_url="https://api.groq.com/openai/v1",
        temperature=0,
    )
else:  # openai
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
- "request": user explicitly wants to submit a NEW HR request (vacation, sick leave, PTO, or reimbursement)
- "cancel_request": user explicitly wants to cancel an EXISTING pending request \
  (clear phrases only: "cancel it", "cancel the old one", "cancel my request", "remove it", \
  "delete it", "withdraw it", "cancel the existing one")

Rules:
- Only use "cancel_request" when the user uses an explicit cancellation verb ("cancel", "remove", \
  "delete", "withdraw") aimed at an existing request. Short replies like "yes", "okay", "sure", \
  "no", a number, or a date are NEVER "cancel_request" — they are continuations of the active flow.
- Use "request" when the user is continuing to provide details for a new request (dates, day counts, \
  reasons) — even if prior turns contained a conflict or balance warning.
- Use "request" only when the user wants to submit something NEW.
- "request" almost always also needs "db" context (leave balances, employee info).
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

# Tells the LLM how to extract structured request details
_REQUEST_PROMPT = """\
You are an HR request parser for MyPerks. Extract the structured details of the \
employee's HR request from the full conversation below.

Today's date: {today}

DATE PARSING RULES:
- "June 25" or "jun 25" → {year}-06-25
- "25/6" or "25-6" → {year}-06-25 (DAY/MONTH order)
- Always use current year ({year}) unless the date would be in the past.
- Output dates as YYYY-MM-DD.

For leave requests (vacation, sick, pto) — TWO steps only:

  STEP 1 — start_date unknown:
    Set is_complete=false.
    If requested_days is known: clarification_question="When would you like to start your {{N}}-day leave?" (replace {{N}} with the actual number)
    If requested_days is also unknown: clarification_question="When would you like to start, and how many days do you need?"

  STEP 2 — start_date known → COMPLETE immediately:
    Set is_complete=true, clarification_question=null.
    If the employee gave a number of days → set requested_days, leave end_date null.
    If the employee gave an end date → set end_date, leave requested_days null.
    If neither → leave both null (system defaults to 1 day).
    Do NOT ask for a reason. Do NOT ask for an end date when requested_days is already known.

For reimbursement requests — TWO steps only:

  STEP 1 — amount unknown:
    Set is_complete=false, clarification_question="How much would you like to claim?"

  STEP 2 — amount known → COMPLETE immediately:
    Set is_complete=true, clarification_question=null.

Generate a short summary:
  "5 days vacation starting June 25"
  "3-day sick leave from June 10"
  "$200 reimbursement"\
"""

# ---------------------------------------------------------------------------
# Router helpers
# ---------------------------------------------------------------------------


class _RouterOutput(BaseModel):
    """Structured output the router LLM must return."""

    intent: list[Literal["rag", "db", "email", "request", "cancel_request"]]


# Bind the LLM to always return a _RouterOutput object
_router_runnable = _llm.with_structured_output(_RouterOutput)


class _RequestBody(BaseModel):
    """Fields for a structured HR request, all optional to cover both leave and reimbursement."""

    start_date: str | None = Field(
        None, description="Start date (YYYY-MM-DD) for leave requests"
    )
    end_date: str | None = Field(
        None,
        description="Explicit end date (YYYY-MM-DD) — only set if the employee stated it directly",
    )
    requested_days: int | None = Field(
        None,
        description="Number of days the employee asked for (e.g. '5 days off') — set instead of end_date when the employee gives a count, not a date range",
    )
    reason: str | None = Field(None, description="Reason or notes for leave")
    amount: float | None = Field(None, description="Amount for reimbursement requests")
    currency: str = Field("USD", description="Currency code, default USD")
    description: str | None = Field(
        None, description="Description for reimbursement requests"
    )


class _RequestOutput(BaseModel):
    """Structured output the request extraction LLM must return."""

    type: Literal["vacation", "sick", "pto", "reimbursement"]
    body: _RequestBody
    summary: str = Field(description="Brief human-readable summary of the request")
    is_complete: bool = Field(description="True if all required fields are present")
    skip_reason: bool = Field(
        False,
        description="True if the user explicitly declined to provide a reason/description",
    )
    clarification_question: str | None = Field(
        None,
        description="Question to ask the user when a required field is missing",
    )


_request_runnable = _llm.with_structured_output(_RequestOutput)


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

    The full conversation history is passed so that short follow-up messages
    (e.g. "jun 8" after being asked for a start date) are classified correctly
    as continuations of the ongoing intent.
    """
    messages_for_router: list[Any] = [SystemMessage(content=_ROUTER_PROMPT)]
    for msg in state["messages"]:
        if msg.type == "human":
            messages_for_router.append({"role": "user", "content": str(msg.content)})
        elif msg.type == "ai":
            messages_for_router.append(
                {"role": "assistant", "content": str(msg.content)}
            )

    try:
        result = cast(
            _RouterOutput,
            await _router_runnable.ainvoke(messages_for_router),
        )
        # Only keep valid intent values; discard anything unexpected
        intent = [
            i
            for i in result.intent
            if i in ("rag", "db", "email", "request", "cancel_request")
        ]
        logger.info("Router intent: %s", intent)
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
        department: str = state["department"]
        async with AsyncSessionLocal() as db:
            chunks = await search_chunks(
                query=question, session=db, department=department, top_k=5
            )

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


async def request_node(state: AgentState) -> dict[str, Any]:
    """
    Step 2c — Structured request extraction.

    When the user expresses intent to submit an HR request, this node uses an LLM
    with structured output to extract the request type and details (dates, reason,
    amount, etc.) into a dict stored as state["pending_request"].

    The responder_node then generates a confirmation message, and the frontend
    renders a card with Submit/Cancel buttons.
    """
    now = datetime.now(UTC)
    today_str = now.strftime("%Y-%m-%d")
    year_str = str(now.year)

    # Pass full message history so multi-turn clarifications are visible to the LLM
    messages_for_llm: list[Any] = [
        SystemMessage(content=_REQUEST_PROMPT.format(today=today_str, year=year_str))
    ]
    for msg in state["messages"]:
        if msg.type == "human":
            messages_for_llm.append({"role": "user", "content": str(msg.content)})
        elif msg.type == "ai":
            messages_for_llm.append({"role": "assistant", "content": str(msg.content)})

    try:
        last_exc: Exception | None = None
        result = None
        for _attempt in range(3):
            try:
                result = cast(
                    _RequestOutput,
                    await _request_runnable.ainvoke(messages_for_llm),
                )
                break
            except Exception as exc:
                last_exc = exc
                logger.warning("Request extraction attempt %d failed: %s", _attempt + 1, exc)
        if result is None:
            raise last_exc or RuntimeError("Request extraction failed after retries")

        logger.info("Request extraction: type=%s is_complete=%s clarification=%r start=%s days=%s",
                    result.type, result.is_complete, result.clarification_question,
                    result.body.start_date, result.body.requested_days)

        if not result.is_complete:
            return {
                "pending_request": None,
                "clarification_question": result.clarification_question,
            }

        body = result.body
        today = now.date()

        # Guard: leave requests must have a start date — LLMs sometimes mark
        # is_complete=True prematurely when only day-count was given.
        if result.type in ("vacation", "sick", "pto") and not body.start_date:
            days = body.requested_days
            question = (
                f"What date would you like your {days}-day {result.type} leave to start?"
                if days
                else "What date would you like your leave to start, and how many days do you need?"
            )
            return {"pending_request": None, "clarification_question": question}

        # Validate and enrich leave-request dates in Python
        if body.start_date:
            try:
                start = _date.fromisoformat(body.start_date)
            except ValueError:
                return {
                    "pending_request": None,
                    "clarification_question": "I couldn't parse that date. Could you give the start date in a format like 'June 8' or '8/6'?",
                }

            if start < today:
                return {
                    "pending_request": None,
                    "clarification_question": (
                        f"{start.strftime('%B %-d')} has already passed. "
                        "Please provide a future start date."
                    ),
                }

            if body.requested_days and body.requested_days > 0:
                # Employee said "N days off" — compute end date from that count
                end = _add_working_days(start, body.requested_days)
                working_days = body.requested_days
            elif body.end_date:
                # Employee gave an explicit date range — count working days between them
                try:
                    end = _date.fromisoformat(body.end_date)
                except ValueError:
                    end = start
                working_days = _count_working_days(start, end)
            else:
                # No end info — default to a single day
                end = start
                working_days = _count_working_days(start, end)

            # Check leave balance — reject if requested days exceed what's remaining
            if result.type in ("vacation", "sick", "pto"):
                remaining = await _get_remaining_leave(
                    state["employee_id"], result.type
                )
                if remaining is not None and working_days > remaining:
                    remaining_int = int(remaining)
                    return {
                        "pending_request": None,
                        "clarification_question": (
                            f"You only have {remaining_int} remaining {result.type} "
                            f"day{'s' if remaining_int != 1 else ''} this year, but this request "
                            f"covers {working_days} working days. "
                            f"How many days would you like to request instead? (maximum: {remaining_int})"
                        ),
                    }

            # Check for overlapping existing leave requests (pending or approved)
            conflict = await _find_leave_conflict(
                employee_id=state["employee_id"],
                req_type=result.type,
                start=start,
                end=end,
            )
            if conflict:
                existing_start = _date.fromisoformat(conflict["start_date"]).strftime(
                    "%-d %B"
                )
                existing_end = _date.fromisoformat(conflict["end_date"]).strftime(
                    "%-d %B"
                )
                return {
                    "pending_request": None,
                    "clarification_question": (
                        f"You already have a {conflict['status']} {conflict['type']} request "
                        f"from {existing_start} to {existing_end} that overlaps with these dates. "
                        "Would you like to choose different dates or cancel the existing request?"
                    ),
                }

            body_dict = body.model_dump(exclude_none=True)
            body_dict.pop("requested_days", None)  # internal field, not stored in DB
            body_dict["start_date"] = start.isoformat()
            body_dict["end_date"] = end.isoformat()
            body_dict["days"] = working_days
            breakdown = _build_breakdown(start, end)
        else:
            body_dict = body.model_dump(exclude_none=True)
            breakdown = []

        return {
            "pending_request": {
                "type": result.type,
                "body": body_dict,
                "summary": result.summary,
                "breakdown": breakdown,  # UI only — not persisted to DB
            },
            "clarification_question": None,
        }

    except Exception:
        logger.exception("Request node failed — skipping request extraction")
        return {"pending_request": None, "clarification_question": None}


async def cancel_request_node(state: AgentState) -> dict[str, Any]:
    """
    Step 2d — Cancel an existing pending leave request.

    Looks at the conversation history to find dates that were mentioned in a
    conflict warning (e.g. "you have a pending request from Jun 6 to Jun 12").
    Cancels the matching request, or falls back to the most recent pending leave
    request if no specific match is found.
    """
    employee_id = state["employee_id"]

    # Extract date hints from the AI messages in conversation history so we can
    # match the specific request the user is referring to.
    mentioned_dates: list[str] = []
    for msg in state["messages"]:
        if msg.type != "ai":
            continue
        content = str(msg.content)
        # Scan for ISO dates like 2026-06-06 or keywords the conflict node emits
        mentioned_dates.extend(re.findall(r"\d{4}-\d{2}-\d{2}", content))

    try:
        async with AsyncSessionLocal() as db:
            rows = (
                (
                    await db.execute(
                        select(RequestHistory)
                        .where(
                            RequestHistory.employee_id == employee_id,
                            RequestHistory.status == "pending",
                            RequestHistory.type.in_(["vacation", "sick", "pto"]),
                        )
                        .order_by(RequestHistory.created_at.desc())
                    )
                )
                .scalars()
                .all()
            )

        if not rows:
            return {"cancelled_request": None}

        # Try to find the request whose dates were mentioned in the conversation
        target = None
        for row in rows:
            if not row.body:
                continue
            try:
                body = json.loads(cast(str, row.body))
                if (
                    body.get("start_date") in mentioned_dates
                    or body.get("end_date") in mentioned_dates
                ):
                    target = row
                    break
            except (json.JSONDecodeError, KeyError):
                continue

        # Fall back to the most recent pending request
        if target is None:
            target = rows[0]

        async with AsyncSessionLocal() as db:
            row_to_cancel = await db.get(RequestHistory, target.id)
            if row_to_cancel is None:
                return {"cancelled_request": None}
            if row_to_cancel.status != "pending":
                return {"cancelled_request": None}
            row_to_cancel.status = "cancelled"
            await db.commit()
            await db.refresh(row_to_cancel)

        cancelled_body = (
            json.loads(cast(str, row_to_cancel.body)) if row_to_cancel.body else {}
        )
        return {
            "cancelled_request": {
                "id": row_to_cancel.id,
                "type": str(row_to_cancel.type),
                "start_date": cancelled_body.get("start_date"),
                "end_date": cancelled_body.get("end_date"),
                "days": cancelled_body.get("days"),
            },
        }

    except Exception:
        logger.exception("Cancel request node failed")
        return {"cancelled_request": None}


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
    pending_request = state.get("pending_request") or {}
    clarification_question = state.get("clarification_question") or ""
    cancelled_request = state.get("cancelled_request")

    # Cancel-request flow: confirm the cancellation to the user
    if "cancel_request" in intent:
        if cancelled_request:
            req_type = cancelled_request.get("type", "request")
            start = cancelled_request.get("start_date") or ""
            end = cancelled_request.get("end_date") or ""
            days = cancelled_request.get("days")

            date_range = ""
            if start:
                try:
                    s = _date.fromisoformat(start).strftime("%-d %B")
                    e = _date.fromisoformat(end).strftime("%-d %B") if end else s
                    date_range = f" from {s}" + (f" to {e}" if e != s else "")
                except ValueError:
                    pass
            days_str = f" ({days} days)" if days else ""

            prompt = (
                f"You are MyPerks, a friendly HR assistant. "
                f"The employee's pending {req_type} request{date_range}{days_str} "
                "has just been successfully cancelled in the system. "
                "Confirm this warmly in one sentence and offer to help them submit a new request if they wish."
            )
        else:
            prompt = (
                "You are MyPerks, a friendly HR assistant. "
                "The employee asked to cancel a request but no matching pending request was found. "
                "Let them know politely in one sentence."
            )
        response = await _llm.ainvoke([{"role": "user", "content": prompt}])
        return {"messages": [AIMessage(content=str(response.content))]}

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

    # Request flow: bypass the "ONLY the context below" constraint entirely so the
    # LLM doesn't refuse when RAG/DB context is empty.
    if "request" in intent and not clarification_question and not pending_request:
        # request_node failed to extract details — ask for start date directly
        prompt = (
            "You are MyPerks, a friendly HR assistant. "
            f"The employee said: \"{question}\". "
            "They want to submit a leave request. Ask them in one short sentence: "
            "when would they like their leave to start?"
        )
        response = await _llm.ainvoke([{"role": "user", "content": prompt}])
        return {"messages": [AIMessage(content=str(response.content))]}

    if "request" in intent and (clarification_question or pending_request):
        if clarification_question:
            prompt = (
                f"You are MyPerks, a friendly HR assistant. "
                f"The employee wants to submit an HR request but you need one more detail. "
                f"Ask them this in a single, warm sentence: {clarification_question}"
            )
        else:
            summary = pending_request.get("summary", "HR request")
            req_type = pending_request.get("type", "request")
            prompt = (
                f"You are MyPerks, a friendly HR assistant. "
                f"The employee's {req_type} request has been prepared: {summary}. "
                "Acknowledge it warmly in 1–2 sentences and tell them to review the "
                "confirmation card below and click 'Submit Request' to send it to HR."
            )

        response = await _llm.ainvoke([{"role": "user", "content": prompt}])
        return {"messages": [AIMessage(content=str(response.content))]}

    # Standard flow: use the full context + system prompt
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
