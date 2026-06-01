from typing import Annotated, Any, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """
    Shared state that travels through every node in the graph.

    Fields
    ------
    employee_id      : The logged-in employee's database ID.
    messages         : Full chat history. LangGraph merges new messages automatically
                        (via `add_messages`).
    intent           : What the router decided the user needs, e.g. ["rag", "db"].
    rag_context      : Policy/document text retrieved by the RAG node.
    db_context       : Live employee data (leave balances, recent requests) from the DB
                        node.
    pending_request       : Structured request data extracted by request_node when
                            the user wants to submit an HR request. None when not
                            applicable.
    clarification_question: Follow-up question request_node needs answered before the
                            request can be completed. None when not applicable.
    cancelled_request     : Summary of the request cancelled by cancel_request_node.
                            None when no cancellation occurred.
    """

    employee_id: int
    messages: Annotated[list[BaseMessage], add_messages]
    intent: list[str]
    rag_context: str
    db_context: str
    pending_request: dict[str, Any] | None
    clarification_question: str | None
    cancelled_request: dict[str, Any] | None
