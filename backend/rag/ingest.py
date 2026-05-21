"""
backend/rag/ingest.py

RAG ingestion pipeline (T5).

Accepts a PDF (path or bytes), extracts text with pypdf, splits it into
~500-token chunks with overlap (token counts via tiktoken), embeds each chunk
with OpenAI ``text-embedding-3-small`` (1536 dims) through langchain-openai,
and stores chunks + embeddings in the ``document_chunks`` table using the
project's own SQLAlchemy ORM models.

Design note on the ticket wording ("store ... via langchain-postgres PGVector
store"): langchain-postgres' PGVector manages its *own* tables
(``langchain_pg_embedding`` / ``langchain_pg_collection``) and does not write
into the hand-defined ``document_chunks`` table. Since this project already
defines ``Document``/``DocumentChunk`` with a ``Vector(1536)`` column and a
unique ``(document_id, chunk_index)`` index, we honor that schema directly:
embeddings come from langchain-openai, persistence and similarity search use
the ORM + pgvector's ``<=>`` operator. This keeps the documents table, the
relationship, and cascade deletes intact.

Dedup: the raw PDF bytes are SHA-256 hashed and stored on
``documents.content_sha256``. Re-ingesting identical bytes is skipped (the
existing Document is returned). Changed bytes are treated as a new document.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import tiktoken
from langchain_openai import OpenAIEmbeddings
from pypdf import PdfReader
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db import Document, DocumentChunk
from settings import settings

# ── Tunables ─────────────────────────────────────────────────────────────────
EMBEDDING_MODEL = "text-embedding-3-small"  # 1536 dims, matches Vector(1536)
MAX_TOKENS = 500
OVERLAP_TOKENS = 50
# text-embedding-3-small uses the cl100k_base encoding.
_ENCODING = "cl100k_base"


# ── Text extraction ────────────────────────────────────────────────────────--
def _read_pdf_bytes(source: str | bytes | Path) -> bytes:
    """Return raw PDF bytes from a path or bytes input."""
    if isinstance(source, bytes):
        return source
    return Path(source).read_bytes()


def _extract_text(pdf_bytes: bytes) -> str:
    """Extract and concatenate text from all pages of a PDF."""
    import io

    reader = PdfReader(io.BytesIO(pdf_bytes))
    parts = [(page.extract_text() or "") for page in reader.pages]
    return "\n".join(parts).strip()


# ── Chunking ─────────────────────────────────────────────────────────────────
def _chunk_text(
    text: str, max_tokens: int = MAX_TOKENS, overlap: int = OVERLAP_TOKENS
) -> list[str]:
    """Split text into ~max_tokens chunks with token overlap, using tiktoken."""
    if not text:
        return []
    enc = tiktoken.get_encoding(_ENCODING)
    tokens = enc.encode(text)
    n = len(tokens)
    if n == 0:
        return []
    step = max_tokens - overlap
    if step <= 0:
        raise ValueError("overlap must be smaller than max_tokens")
    chunks: list[str] = []
    start = 0
    while start < n:
        end = min(start + max_tokens, n)
        chunks.append(enc.decode(tokens[start:end]))
        if end == n:
            break
        start += step
    return chunks


# ── Hashing ──────────────────────────────────────────────────────────────────
def _sha256(pdf_bytes: bytes) -> str:
    return hashlib.sha256(pdf_bytes).hexdigest()


# ── Main entry point ─────────────────────────────────────────────────────────
async def ingest_pdf(
    source: str | bytes | Path,
    filename: str,
    uploaded_by: int | None,
    session: AsyncSession,
) -> Document:
    """
    Ingest a PDF into the RAG store.

    Returns the persisted (or pre-existing, on dedup) ``Document``.
    Importable and callable from the upload endpoint.
    """
    pdf_bytes = _read_pdf_bytes(source)
    content_hash = _sha256(pdf_bytes)

    # Dedup: skip if identical bytes already ingested.
    existing = await session.scalar(
        select(Document).where(Document.content_sha256 == content_hash)
    )
    if existing is not None:
        return existing

    text = _extract_text(pdf_bytes)
    chunks = _chunk_text(text)

    embeddings = OpenAIEmbeddings(
        model=EMBEDDING_MODEL,
        openai_api_key=settings.openai_api_key,
    )
    # embed_documents handles batching; returns a 1536-dim vector per chunk.
    vectors = await embeddings.aembed_documents(chunks) if chunks else []

    document = Document(
        filename=filename,
        uploaded_by=uploaded_by,
        content_sha256=content_hash,
    )
    document.chunks = [
        DocumentChunk(
            chunk_index=i,
            content=chunk,
            embedding=vector,
        )
        for i, (chunk, vector) in enumerate(zip(chunks, vectors, strict=True))
    ]
    session.add(document)
    await session.commit()
    await session.refresh(document)
    return document
