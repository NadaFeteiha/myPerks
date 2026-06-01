"""
        LangGraph workflow

The execution flow looks like this:

        ┌──────────────┐
        │ router_node  │   ← classifies intent
        └───────┬──────┘
                │
        ┌───────┴────────┐   (run in parallel when both are needed)
        ▼                ▼
    ┌─────────┐    ┌─────────┐
    │ rag_node│    │ db_node │
    └───┬─────┘    └────┬────┘
        │               │
        └───────┬───────┘
                ▼
        ┌─────────────────┐
        │ responder_node  │   ← generates the final answer
        └───────┬─────────┘
                ▼
                [END]
"""

from collections.abc import AsyncGenerator, Hashable, Sequence
from typing import Any

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph

from .nodes import cancel_request_node, db_node, rag_node, request_node, responder_node, router_node
from .state import AgentState


def _route_after_router(state: AgentState) -> Sequence[Hashable]:
    """
    Decide which nodes to run after the router, based on the detected intent.

    Returns a list of node names so LangGraph can run them in parallel:
    - "rag"   → run rag_node  (fetch HR policy documents)
    - "db"    → run db_node   (fetch live employee data)
    - "email" → run both, because a good email needs full context

    If neither node is needed (shouldn't happen, but safe fallback),
    jump straight to responder_node.
    """
    intent = state.get("intent", [])
    nodes: list[str] = []

    if "rag" in intent or "email" in intent:
        nodes.append("rag_node")

    if "db" in intent or "email" in intent or "request" in intent:
        nodes.append("db_node")

    if "request" in intent:
        nodes.append("request_node")

    if "cancel_request" in intent:
        nodes.append("cancel_request_node")

    # Fallback: go directly to responder_node if intent is somehow empty
    return nodes or ["responder_node"]


def _build_graph() -> CompiledStateGraph:
    """
    Construct and compile the LangGraph state machine.

    Nodes are registered first, then edges define the allowed transitions.
    Conditional edges let the router fan out to one or both fetcher nodes.
    """
    workflow: StateGraph = StateGraph(AgentState)

    # Register every node by name
    workflow.add_node("router_node", router_node)
    workflow.add_node("rag_node", rag_node)
    workflow.add_node("db_node", db_node)
    workflow.add_node("request_node", request_node)
    workflow.add_node("cancel_request_node", cancel_request_node)
    workflow.add_node("responder_node", responder_node)

    # Entry point — always start with intent classification
    workflow.set_entry_point("router_node")

    # After routing, fan out to whichever fetcher nodes are needed
    workflow.add_conditional_edges("router_node", _route_after_router)

    # All fetcher nodes feed into the responder once they finish
    workflow.add_edge("rag_node", "responder_node")
    workflow.add_edge("db_node", "responder_node")
    workflow.add_edge("request_node", "responder_node")
    workflow.add_edge("cancel_request_node", "responder_node")

    # The responder is the last step
    workflow.add_edge("responder_node", END)

    return workflow.compile()


# Module-level singleton — built once when the module is first imported
graph: CompiledStateGraph = _build_graph()


async def run_agent(
    employee_id: int,
    question: str,
    history: list[tuple[str, str]] | None = None,
) -> AsyncGenerator[str | dict[str, Any], None]:
    """
    Entry point for running the agent with token-by-token streaming.

    This is an async generator — callers iterate with
    `async for chunk in run_agent(...)` to receive tokens as they are produced
    by the LLM (suitable for Server-Sent Events / SSE).

    Yields:
    - str chunks from the responder LLM (streamed text tokens)
    - A single dict {"type": "request_confirmation", "data": {...}} at the end
      when the agent detected an HR request submission intent.

    Only responder_node tokens are streamed; router, RAG, DB and request nodes run
    silently — they produce structured data, not user-facing text.

    Parameters
    ----------
    employee_id : Database ID of the logged-in employee.
    question    : The user's current question.
    history     : Prior conversation turns as (role, content) pairs — role is
                    "user" or "assistant".  Injected before the current question
                    so the LLM has multi-turn context.
    """
    messages: list[BaseMessage] = []
    for role, content in history or []:
        if role == "user":
            messages.append(HumanMessage(content=content))
        else:
            messages.append(AIMessage(content=content))
    messages.append(HumanMessage(content=question))

    initial_state: AgentState = {
        "employee_id": employee_id,
        "messages": messages,
        "intent": [],
        "rag_context": "",
        "db_context": "",
        "pending_request": None,
        "clarification_question": None,
        "cancelled_request": None,
    }

    pending_request: dict[str, Any] | None = None

    # astream_events yields low-level events for every step in the graph
    async for event in graph.astream_events(initial_state, version="v2"):
        # Capture pending_request output from request_node
        if event.get("event") == "on_chain_end":
            metadata = event.get("metadata", {})
            if metadata.get("langgraph_node") == "request_node":
                output = event.get("data", {}).get("output", {})
                if isinstance(output, dict) and output.get("pending_request"):
                    pending_request = output["pending_request"]

        # Stream text chunks from the responder LLM call
        is_llm_stream = event["event"] == "on_chat_model_stream"
        is_responder = (
            event.get("metadata", {}).get("langgraph_node") == "responder_node"
        )

        if is_llm_stream and is_responder:
            chunk = event["data"].get("chunk")
            if chunk and chunk.content:
                yield str(chunk.content)

    # After all text is streamed, emit the pending request if one was extracted
    if pending_request:
        yield {"type": "request_confirmation", "data": pending_request}
