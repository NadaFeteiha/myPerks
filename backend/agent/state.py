from typing import Annotated, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """
    Shared state that travels through every node in the graph.

    Fields
    ------
    employee_id  : The logged-in employee's database ID.
    messages     : Full chat history. LangGraph merges new messages into this list automatically (via `add_messages`).
    intent       : What the router decided the user needs, e.g. ["rag", "db"].
    rag_context  : Policy/document text retrieved by the RAG node.
    db_context   : Live employee data (leave balances, recent requests) from the DB node.
    """

    employee_id: int
    messages: Annotated[list[BaseMessage], add_messages]
    intent: list[str]
    rag_context: str
    db_context: str
