"""
RAG retrieval — the other half of the ingestion pipeline.

`search_chunks` is the function the LangGraph RAG node calls at query time:
embed the user's question with the same model used during ingestion, then
return the top-k most similar DocumentChunk rows via pgvector cosine distance.
"""

from __future__ import annotations

from dataclasses import dataclass

from langchain_openai import OpenAIEmbeddings
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db import DocumentChunk
from rag.ingest import EMBEDDING_MODEL
from settings import settings

_embeddings = OpenAIEmbeddings(  # type: ignore[call-arg]
    model=EMBEDDING_MODEL,
    api_key=settings.openai_api_key,
    max_retries=3,
)


@dataclass
class ChunkResult:
    chunk_id: int
    document_id: int
    filename: str
    chunk_index: int
    content: str
    page_start: int | None
    page_end: int | None


async def search_chunks(
    query: str, session: AsyncSession, top_k: int = 5
) -> list[ChunkResult]:
    """
    Embed ``query`` and return the ``top_k`` most relevant chunks by cosine
    distance.  Returns a plain dataclass list so callers never touch ORM
    internals after the session closes.

    Used by the LangGraph RAG node — call this, then pass the results to the
    synthesiser as grounding context.
    """
    query_vector = (await _embeddings.aembed_documents([query]))[0]

    stmt = (
        select(DocumentChunk)
        .where(DocumentChunk.embedding.isnot(None))
        .order_by(DocumentChunk.embedding.cosine_distance(query_vector))
        .limit(top_k)
        .options(selectinload(DocumentChunk.document))
    )
    chunks = list(await session.scalars(stmt))

    return [
        ChunkResult(
            chunk_id=c.id,
            document_id=c.document_id,
            filename=c.document.filename,
            chunk_index=c.chunk_index,
            content=c.content,
            page_start=c.page_start,
            page_end=c.page_end,
        )
        for c in chunks
    ]
