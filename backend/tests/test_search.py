"""
backend/tests/test_search.py

Unit tests for RAG department-scoped retrieval (T28).

All tests run without a real DB or OpenAI key — embeddings are mocked by
replacing the module-level _embeddings singleton.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from rag.search import ChunkResult, search_chunks

_FAKE_VECTOR = [0.1] * 1536


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_chunk(
    chunk_id: int,
    document_id: int,
    filename: str,
    department: str,
    content: str = "some text",
) -> MagicMock:
    doc = MagicMock()
    doc.filename = filename
    doc.department = department

    chunk = MagicMock()
    chunk.id = chunk_id
    chunk.document_id = document_id
    chunk.document = doc
    chunk.chunk_index = 0
    chunk.content = content
    chunk.page_start = 1
    chunk.page_end = 1
    return chunk


def _make_session(scalars_result: list[MagicMock]) -> MagicMock:
    session = MagicMock()
    session.scalars = AsyncMock(return_value=scalars_result)
    return session


def _mock_embeddings() -> MagicMock:
    mock = MagicMock()
    mock.aembed_documents = AsyncMock(return_value=[_FAKE_VECTOR])
    return mock


def _capture_session() -> tuple[MagicMock, list[object]]:
    """Session that records the stmt passed to scalars(); returns (session, captured)."""
    captured: list[object] = []
    session = MagicMock()

    async def _scalars(stmt: object) -> list[object]:
        captured.append(stmt)
        return []

    session.scalars = _scalars
    return session, captured


# ---------------------------------------------------------------------------
# WHERE-clause inspection helper
# ---------------------------------------------------------------------------


def _where_sql(stmt: object) -> str:
    """
    Compile only the WHERE clause to a plain SQL string with literal values.
    The WHERE clause contains no vector parameters so literal_binds always works.
    """
    whereclause = stmt.whereclause  # type: ignore[attr-defined]
    return str(whereclause.compile(compile_kwargs={"literal_binds": True}))


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_department_filter_in_where_clause() -> None:
    """
    The SQL WHERE clause must contain the department value — verified by
    inspecting the compiled WHERE clause directly, not the mock return value.
    Prevents regressions where the filter is removed but mock tests still pass.
    """
    session, captured = _capture_session()

    with patch("rag.search._embeddings", _mock_embeddings()):
        await search_chunks(query="policy", session=session, department="marketing")

    assert len(captured) == 1
    sql = _where_sql(captured[0])
    assert "marketing" in sql, f"Expected 'marketing' in WHERE clause, got: {sql}"
    assert "department" in sql.lower(), f"Expected department column in WHERE: {sql}"


@pytest.mark.asyncio
async def test_search_chunks_only_returns_matching_department() -> None:
    """
    Only chunks from the requested department come back — a chunk from another
    department is invisible (filtered by the DB WHERE clause).
    """
    eng_chunk = _make_chunk(1, 10, "eng_policy.pdf", "engineering")
    session = _make_session([eng_chunk])

    with patch("rag.search._embeddings", _mock_embeddings()):
        results = await search_chunks(
            query="vacation policy",
            session=session,
            department="engineering",
        )

    assert len(results) == 1
    assert results[0].filename == "eng_policy.pdf"


@pytest.mark.asyncio
async def test_search_chunks_empty_when_no_docs_in_department() -> None:
    """
    If no documents belong to the requested department, an empty list is
    returned — no chunks from other departments leak through.
    """
    session = _make_session([])

    with patch("rag.search._embeddings", _mock_embeddings()):
        results = await search_chunks(
            query="anything",
            session=session,
            department="finance",
        )

    assert results == []


@pytest.mark.asyncio
async def test_search_chunks_returns_correct_fields() -> None:
    """ChunkResult is populated correctly from the ORM mock."""
    chunk = _make_chunk(7, 3, "sales_doc.pdf", "sales", "sales content here")
    chunk.chunk_index = 2
    chunk.page_start = 4
    chunk.page_end = 5
    session = _make_session([chunk])

    with patch("rag.search._embeddings", _mock_embeddings()):
        results = await search_chunks(
            query="sales",
            session=session,
            department="sales",
        )

    assert len(results) == 1
    r = results[0]
    assert isinstance(r, ChunkResult)
    assert r.chunk_id == 7
    assert r.document_id == 3
    assert r.filename == "sales_doc.pdf"
    assert r.chunk_index == 2
    assert r.content == "sales content here"
    assert r.page_start == 4
    assert r.page_end == 5
