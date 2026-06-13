"""
backend/tests/test_ingest.py

Tests for the RAG ingestion pipeline (T5).

Three tiers:
- Pure unit tests for chunking — no DB, no API, always run (incl. CI).
- Dedup logic with a mocked async session + mocked embeddings — no DB, no
  API, always run. Proves "duplicate ingestion is handled (skip)".
- A real end-to-end ingest + pgvector similarity search, marked
  ``integration`` and SKIPPED unless OPENAI_API_KEY is set and a test DB is
  reachable. Proves "a PDF is fully ingested and queryable via pgvector".

The integration test writes to a SEPARATE database (myperks_test) so it never
touches dev data. Create it once:

    createdb -U postgres -h localhost myperks_test
    psql "postgresql://postgres:postgres@localhost:5432/myperks_test" \
        -c "CREATE EXTENSION IF NOT EXISTS vector;"
"""

from __future__ import annotations

import io
import os
from collections.abc import AsyncIterator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from rag.ingest import _chunk_text, ingest_pdf

# ── Pure unit tests: chunking (no DB, no API) ────────────────────────────────


def test_chunk_text_respects_token_budget_and_overlap() -> None:
    # ~1200 tokens of distinct words.
    text = " ".join(f"word{i}" for i in range(1200))
    chunks = _chunk_text([(1, text)], max_tokens=500, overlap=50)
    assert len(chunks) >= 2
    # No chunk should blow far past the budget (token != word, but close here).
    import tiktoken

    enc = tiktoken.get_encoding("cl100k_base")
    assert all(len(enc.encode(chunk_text)) <= 500 for chunk_text, _, _ in chunks)


def test_chunk_text_empty_returns_empty() -> None:
    assert _chunk_text([]) == []


def test_chunk_text_rejects_bad_overlap() -> None:
    with pytest.raises(ValueError):
        _chunk_text([(1, "some text here")], max_tokens=100, overlap=100)


# ── Dedup logic: mocked session + mocked embeddings (no DB, no API) ──────────


def test_ingest_skips_duplicate_without_embedding() -> None:
    """Identical content hash -> return existing Document, never embed."""
    existing_doc = MagicMock(name="ExistingDocument")

    session = MagicMock()
    # ingest_pdf calls: existing = await session.scalar(select(...))
    session.scalar = AsyncMock(return_value=existing_doc)
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()

    minimal_pdf = _make_minimal_pdf_bytes()

    # If embeddings were constructed/called, this patch would record it.
    with patch("rag.ingest.OpenAIEmbeddings") as mock_embeddings:
        import asyncio

        result = asyncio.run(
            ingest_pdf(
                pdf_bytes=minimal_pdf,
                filename="dup.pdf",
                uploaded_by=None,
                session=session,
                department="engineering"
            )
        )

    assert result is existing_doc
    mock_embeddings.assert_not_called()  # no embedding work on a duplicate
    session.add.assert_not_called()  # no new rows
    session.commit.assert_not_called()


# ── Integration: real ingest + similarity search (skipped by default) ────────

_RUN_INTEGRATION = bool(os.getenv("OPENAI_API_KEY")) and bool(
    os.getenv("RUN_DB_INTEGRATION")
)

integration = pytest.mark.skipif(
    not _RUN_INTEGRATION,
    reason="set OPENAI_API_KEY and RUN_DB_INTEGRATION=1 to run real ingest test",
)


@pytest.fixture
async def test_session() -> AsyncIterator[object]:
    """Async session against a dedicated test DB; tables created then dropped."""
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    from db import Base

    url = os.getenv(
        "TEST_DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/myperks_test",
    )
    engine = create_async_engine(url)
    async with engine.begin() as conn:
        await conn.exec_driver_sql("CREATE EXTENSION IF NOT EXISTS vector")
        await conn.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as session:
        yield session
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@integration
async def test_ingest_and_similarity_search(test_session: object) -> None:
    """Full pipeline: ingest a PDF, then retrieve it via pgvector search."""
    from langchain_openai import OpenAIEmbeddings
    from sqlalchemy import select

    from db import DocumentChunk
    from rag.ingest import EMBEDDING_MODEL
    from settings import settings

    pdf = _make_text_pdf_bytes(
        "Employees accrue vacation days monthly. "
        "Unused vacation rolls over up to a cap of ten days."
    )
    doc = await ingest_pdf(
        pdf_bytes=pdf,
        filename="policy.pdf",
        uploaded_by=None,
        session=test_session,  # type: ignore[arg-type]
        department="engineering"
    )
    assert doc.id is not None
    assert len(doc.chunks) >= 1

    # Query via pgvector cosine distance.
    qvec = (
        await OpenAIEmbeddings(
            model=EMBEDDING_MODEL, openai_api_key=settings.openai_api_key
        ).aembed_documents(["How does vacation rollover work?"])
    )[0]
    stmt = (
        select(DocumentChunk)
        .order_by(DocumentChunk.embedding.cosine_distance(qvec))
        .limit(3)
    )
    hits = list(await test_session.scalars(stmt))  # type: ignore[attr-defined]
    assert hits, "similarity search returned no chunks"
    assert any("vacation" in h.content.lower() for h in hits)


# ── helpers ──────────────────────────────────────────────────────────────────


def _make_minimal_pdf_bytes() -> bytes:
    """A tiny valid PDF (one blank page) for dedup test — content irrelevant."""
    from pypdf import PdfWriter

    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()


def _make_text_pdf_bytes(text: str) -> bytes:
    """A PDF containing the given text, using reportlab if available."""
    try:
        from reportlab.pdfgen import canvas
    except ImportError:  # pragma: no cover
        pytest.skip("reportlab not installed; needed to build a text PDF")
    buf = io.BytesIO()
    c = canvas.Canvas(buf)
    text_obj = c.beginText(40, 800)
    for line in text.split(". "):
        text_obj.textLine(line)
    c.drawText(text_obj)
    c.showPage()
    c.save()
    return buf.getvalue()
