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
import io
from pathlib import Path

import tiktoken
from langchain_openai import OpenAIEmbeddings
from pypdf import PdfReader
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

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

def _extract_pages(pdf_bytes: bytes) -> list[tuple[int, str]]:
    """Return [(1-based page_num, text), ...] for every page in the PDF."""
    reader = PdfReader(io.BytesIO(pdf_bytes))
    return [(i + 1, page.extract_text() or "") for i, page in enumerate(reader.pages)]

# ── Chunking ─────────────────────────────────────────────────────────────────
def _chunk_text_(
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

def _chunk_text(
    pages: list[tuple[int, str]],
    max_tokens: int = MAX_TOKENS,
    overlap: int = OVERLAP_TOKENS,
) -> list[tuple[str, int, int]]:
    """
    Split page text into token-budget chunks with overlap.

    Returns [(chunk_text, page_start, page_end), ...]
    Each chunk carries the first and last page number
    it spans so callers can surface citations.
    """
    if overlap >= max_tokens:
        raise ValueError("overlap must be smaller than max_tokens")

    enc = tiktoken.get_encoding(_ENCODING)

    # Build a flat list of (token_id, page_num) across all pages.
    annotated: list[tuple[int, int]] = []
    for page_num, text in pages:
        for token in enc.encode(text):
            annotated.append((token, page_num))

    if not annotated:
        return []

    step = max_tokens - overlap
    result: list[tuple[str, int, int]] = []
    n = len(annotated)
    start = 0
    while start < n:
        end = min(start + max_tokens, n)
        window = annotated[start:end]
        token_ids = [t for t, _ in window]
        page_nums = [p for _, p in window]
        result.append((enc.decode(token_ids), page_nums[0], page_nums[-1]))
        if end == n:
            break
        start += step
    return result


# ── Hashing ───────────────────────────────────────────────────────────────────
def _sha256(pdf_bytes: bytes) -> str:
    return hashlib.sha256(pdf_bytes).hexdigest()


# ── Main entry point ──────────────────────────────────────────────────────────
async def ingest_pdf(
    pdf_bytes: bytes,
    filename: str,
    uploaded_by: int | None,
    session: AsyncSession,
) -> Document:
    """
    Ingest a PDF into the RAG store.

    ``pdf_bytes`` is the raw upload content received from the server.
    Returns the persisted (or pre-existing, on dedup) ``Document`` with its
    ``chunks`` relationship eagerly loaded.
    """
    content_hash = _sha256(pdf_bytes)

    # Dedup: return early if identical bytes were already ingested.
    existing = await session.scalar(
        select(Document)
        .where(Document.content_sha256 == content_hash)
        .options(selectinload(Document.chunks))
    )
    if existing is not None:
        return existing

    pages = _extract_pages(pdf_bytes)
    all_text = "\n".join(text for _, text in pages).strip()
    if not all_text:
        raise ValueError( f"No extractable text in {filename!r}. ")

    chunk_data = _chunk_text(pages)

    embeddings_client = OpenAIEmbeddings(
        model=EMBEDDING_MODEL,
        api_key=settings.openai_api_key,
        max_retries=3,
    )
    # aembed_documents handles batching internally.
    vectors = await embeddings_client.aembed_documents(
        [text for text, _, _ in chunk_data]
    )

    document = Document(
        filename=filename,
        uploaded_by=uploaded_by,
        content_sha256=content_hash,
    )
    document.chunks = [
        DocumentChunk(
            chunk_index=i,
            content=text,
            page_start=pg_start,
            page_end=pg_end,
            embedding=vector,
        )
        for i, ((text, pg_start, pg_end), vector) in enumerate(
            zip(chunk_data, vectors, strict=True)
        )
    ]
    session.add(document)
    await session.flush()
    await session.commit()
    refreshed = await session.scalar(
        select(Document)
        .where(Document.id == document.id)
        .options(selectinload(Document.chunks))
    )
    assert refreshed is not None
    return refreshed
