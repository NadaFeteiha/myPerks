"""
backend/tests/test_upload.py

Unit tests for POST /upload/callback.

Auth and session dependencies are overridden via app.dependency_overrides.
Remaining collaborators are mocked with patch:
  - _resolve_employee — controls whether an Employee is found
  - httpx.AsyncClient — controls the PDF download response
  - ingest_pdf        — controls ingestion success / failure

Test matrix:
  ✓ Happy path — valid payload, PDF downloads, ingestion succeeds → 200
  ✓ Duplicate — ingest_pdf returns existing document → 200 same document_id
  ✓ No Authorization header → 401
  ✓ Empty files list → 422
  ✓ Employee not found for Clerk user → 403
  ✓ PDF download upstream error (CDN 404) → 502
  ✓ Wrong content-type (not PDF) → 422
  ✓ File exceeds size limit → 422
  ✓ Ingestion pipeline raises → 500
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.auth import get_current_user
from api.upload import router
from db.session import get_session

# ── Constants ──────────────────────────────────────────────────────────────────

CLERK_USER_ID = "user_test123"
EMPLOYEE_ID = 1
DOCUMENT_ID = 7

VALID_PAYLOAD = {
    "files": [
        {
            "url": "https://cdn.uploadthing.com/policy.pdf",
            "name": "policy.pdf",
            "size": 12345,
            "key": "abc123",
        }
    ]
}

AUTH_HEADER = {"Authorization": "Bearer valid.jwt.token"}

# ── Mock factories ─────────────────────────────────────────────────────────────


def _make_employee() -> MagicMock:
    emp = MagicMock()
    emp.id = EMPLOYEE_ID
    return emp


def _make_document(doc_id: int = DOCUMENT_ID) -> MagicMock:
    doc = MagicMock()
    doc.id = doc_id
    return doc


def _make_session() -> MagicMock:
    session = MagicMock()
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=False)
    return session


def _make_http_response(
    content: bytes = b"%PDF-1.4 fake pdf content",
    content_type: str = "application/pdf",
    status_code: int = 200,
) -> MagicMock:
    resp = MagicMock()
    resp.status_code = status_code
    resp.content = content
    resp.headers = {"content-type": content_type}
    if status_code >= 400:
        import httpx

        resp.raise_for_status.side_effect = httpx.HTTPStatusError(
            "upstream error", request=MagicMock(), response=resp
        )
    else:
        resp.raise_for_status = MagicMock()
    return resp


def _make_async_http_client(response: MagicMock) -> MagicMock:
    mock_client = MagicMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(return_value=response)
    return mock_client


# ── App setup with dependency overrides ───────────────────────────────────────

app = FastAPI()
app.include_router(router)


async def _fake_get_current_user() -> str:
    return CLERK_USER_ID


async def _fake_get_session() -> AsyncGenerator[MagicMock, None]:
    yield _make_session()


app.dependency_overrides[get_current_user] = _fake_get_current_user
app.dependency_overrides[get_session] = _fake_get_session

client = TestClient(app, raise_server_exceptions=False)

# ── Patch helper ───────────────────────────────────────────────────────────────


_SENTINEL = object()


def _patches(
    *,
    employee: MagicMock | None | object = _SENTINEL,
    http_response: MagicMock | None = None,
    ingest_return: MagicMock | None = None,
    ingest_side_effect: Exception | None = None,
) -> tuple[list[Any], AsyncMock]:
    _employee = _make_employee() if employee is _SENTINEL else employee
    if http_response is None:
        http_response = _make_http_response()
    if ingest_return is None:
        ingest_return = _make_document()

    ingest_mock = AsyncMock(
        return_value=ingest_return,
        side_effect=ingest_side_effect,
    )

    async def _fake_resolve(_clerk_user_id: str, _session: Any) -> Any:
        return _employee

    return [
        patch("api.upload._resolve_employee", new=_fake_resolve),
        patch("httpx.AsyncClient", return_value=_make_async_http_client(http_response)),
        patch("api.upload.ingest_pdf", ingest_mock),
    ], ingest_mock


# ── Tests ──────────────────────────────────────────────────────────────────────


class TestUploadCallback:
    def test_happy_path_returns_200_and_document_id(self) -> None:
        """Valid upload → ingestion succeeds → 200 with document_id."""
        patches, ingest_mock = _patches()
        with patches[0], patches[1], patches[2]:
            response = client.post(
                "/upload/callback", json=VALID_PAYLOAD, headers=AUTH_HEADER
            )

        assert response.status_code == 200
        assert response.json() == {"status": "ingested", "document_id": DOCUMENT_ID}
        ingest_mock.assert_called_once()

    def test_duplicate_pdf_returns_existing_document_id(self) -> None:
        """ingest_pdf returns an existing Document on SHA-256 match → 200."""
        existing_doc = _make_document(doc_id=99)
        patches, _ = _patches(ingest_return=existing_doc)
        with patches[0], patches[1], patches[2]:
            response = client.post(
                "/upload/callback", json=VALID_PAYLOAD, headers=AUTH_HEADER
            )

        assert response.status_code == 200
        assert response.json()["document_id"] == 99

    def test_missing_auth_header_returns_401(self) -> None:
        """No Authorization header → 401 before any business logic runs."""
        # Remove the override temporarily so real auth runs
        app.dependency_overrides.pop(get_current_user)
        try:
            response = client.post("/upload/callback", json=VALID_PAYLOAD)
            assert response.status_code == 401
        finally:
            app.dependency_overrides[get_current_user] = _fake_get_current_user

    def test_empty_files_list_returns_422(self) -> None:
        """Payload with no files → 422."""
        patches, _ = _patches()
        with patches[0]:
            response = client.post(
                "/upload/callback",
                json={"files": []},
                headers=AUTH_HEADER,
            )

        assert response.status_code == 422
        assert "no files" in response.json()["detail"].lower()

    def test_employee_not_found_returns_403(self) -> None:
        """Clerk user has no matching Employee row → 403."""
        patches, _ = _patches(employee=None)
        with patches[0]:
            response = client.post(
                "/upload/callback", json=VALID_PAYLOAD, headers=AUTH_HEADER
            )

        assert response.status_code == 403
        assert "employee record" in response.json()["detail"].lower()

    def test_cdn_error_returns_502(self) -> None:
        """UploadThing CDN returns 404 → 502."""
        bad_response = _make_http_response(status_code=404)
        patches, _ = _patches(http_response=bad_response)
        with patches[0], patches[1], patches[2]:
            response = client.post(
                "/upload/callback", json=VALID_PAYLOAD, headers=AUTH_HEADER
            )

        assert response.status_code == 502

    def test_non_pdf_content_type_returns_422(self) -> None:
        """CDN returns HTML instead of PDF → 422."""
        bad_response = _make_http_response(
            content=b"<html>not a pdf</html>",
            content_type="text/html",
        )
        patches, _ = _patches(http_response=bad_response)
        with patches[0], patches[1], patches[2]:
            response = client.post(
                "/upload/callback", json=VALID_PAYLOAD, headers=AUTH_HEADER
            )

        assert response.status_code == 422
        assert "pdf" in response.json()["detail"].lower()

    def test_oversized_file_returns_422(self) -> None:
        """PDF exceeds 20 MB limit → 422."""
        big_response = _make_http_response(content=b"x" * (21 * 1024 * 1024))
        patches, _ = _patches(http_response=big_response)
        with patches[0], patches[1], patches[2]:
            response = client.post(
                "/upload/callback", json=VALID_PAYLOAD, headers=AUTH_HEADER
            )

        assert response.status_code == 422
        assert "size limit" in response.json()["detail"].lower()

    def test_ingestion_failure_returns_500(self) -> None:
        """ingest_pdf raises → 500."""
        patches, _ = _patches(ingest_side_effect=RuntimeError("embedding API down"))
        with patches[0], patches[1], patches[2]:
            response = client.post(
                "/upload/callback", json=VALID_PAYLOAD, headers=AUTH_HEADER
            )

        assert response.status_code == 500
        assert "ingestion pipeline failed" in response.json()["detail"].lower()
