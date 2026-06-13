"""
Tests for the upload endpoint — department tagging and admin gating.

backend/tests/test_upload.py
"""

from __future__ import annotations

import hashlib
import io
from collections.abc import AsyncGenerator
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from api.auth import get_current_user, require_admin
from api.upload import router
from db.models import Document, Employee

# ── Fixtures ──────────────────────────────────────────────────────────────────

ADMIN_EMPLOYEE = Employee(
    id=1,
    clerk_user_id="user_admin",
    name="HR Admin",
    email="admin@example.com",
    role="hr_admin",
    department="hr",
    joined_date=date(2023, 1, 1),
    benefits_year_reset=date(2024, 1, 1),
)

REGULAR_EMPLOYEE = Employee(
    id=2,
    clerk_user_id="user_emp",
    name="Regular Employee",
    email="emp@example.com",
    role="employee",
    department="engineering",
    joined_date=date(2023, 6, 1),
    benefits_year_reset=date(2024, 1, 1),
)


def _make_minimal_pdf() -> bytes:
    """Return a minimal valid-looking PDF byte string for testing."""
    return (
        b"%PDF-1.4\n"
        b"1 0 obj\n<< /Type /Catalog >>\nendobj\n"
        b"xref\n0 2\n"
        b"trailer\n<< /Size 2 /Root 1 0 R >>\n"
        b"startxref\n9\n%%EOF"
    )


def _app_with_override(admin_override: Employee | None = ADMIN_EMPLOYEE) -> FastAPI:
    """Build a minimal FastAPI app with the upload router and auth overrides."""
    app = FastAPI()
    app.include_router(router)

    if admin_override is not None:
        # Successful admin auth
        app.dependency_overrides[require_admin] = lambda: admin_override
        app.dependency_overrides[get_current_user] = lambda: admin_override.clerk_user_id
    else:
        # No override — require_admin will fire for real (we mock it to 403 below)
        pass

    return app


# ── Department tagging tests ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_ingest_persists_department() -> None:
    """ingest_pdf is called with the department from the payload."""
    pdf_bytes = _make_minimal_pdf()
    content_hash = hashlib.sha256(pdf_bytes).hexdigest()

    fake_document = MagicMock(spec=Document)
    fake_document.id = 42
    fake_document.content_sha256 = content_hash

    app = _app_with_override(ADMIN_EMPLOYEE)

    mock_session = AsyncMock()
    mock_session.commit = AsyncMock()
    app.dependency_overrides[
        __import__("db.session", fromlist=["get_session"]).get_session
    ] = lambda: mock_session

    with (
        patch("api.upload._download_pdf", new=AsyncMock(return_value=(pdf_bytes, "test.pdf"))),
        patch("api.upload.ingest_pdf", new=AsyncMock(return_value=fake_document)) as mock_ingest,
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/upload/callback",
                json={
                    "files": [{"url": "https://cdn.example.com/test.pdf", "name": "test.pdf", "size": 1024, "key": "abc123"}],
                    "department": "engineering",
                },
                headers={"Authorization": "Bearer fake-token"},
            )

    assert response.status_code == 200
    mock_ingest.assert_awaited_once()
    call_kwargs = mock_ingest.call_args.kwargs
    assert call_kwargs["department"] == "engineering"


@pytest.mark.asyncio
async def test_invalid_department_returns_422() -> None:
    """Unknown department value is rejected before ingestion."""
    app = _app_with_override(ADMIN_EMPLOYEE)

    with patch("api.upload._download_pdf", new=AsyncMock(return_value=(b"%PDF", "f.pdf"))):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/upload/callback",
                json={
                    "files": [{"url": "https://cdn.example.com/f.pdf", "name": "f.pdf", "size": 100, "key": "k"}],
                    "department": "narnia",
                },
                headers={"Authorization": "Bearer fake-token"},
            )

    assert response.status_code == 422
    assert "narnia" in response.json()["detail"]


@pytest.mark.asyncio
async def test_department_case_insensitive() -> None:
    """department is lowercased before validation — 'Engineering' is valid."""
    pdf_bytes = _make_minimal_pdf()
    fake_document = MagicMock(spec=Document)
    fake_document.id = 7
    fake_document.content_sha256 = hashlib.sha256(pdf_bytes).hexdigest()

    app = _app_with_override(ADMIN_EMPLOYEE)

    mock_session = AsyncMock()
    app.dependency_overrides[
        __import__("db.session", fromlist=["get_session"]).get_session
    ] = lambda: mock_session

    with (
        patch("api.upload._download_pdf", new=AsyncMock(return_value=(pdf_bytes, "t.pdf"))),
        patch("api.upload.ingest_pdf", new=AsyncMock(return_value=fake_document)) as mock_ingest,
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/upload/callback",
                json={
                    "files": [{"url": "https://cdn.example.com/t.pdf", "name": "t.pdf", "size": 512, "key": "k2"}],
                    "department": "Engineering",
                },
                headers={"Authorization": "Bearer fake-token"},
            )

    assert response.status_code == 200
    assert mock_ingest.call_args.kwargs["department"] == "engineering"


# ── Admin gating tests ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_employee_upload_returns_403() -> None:
    """A non-admin employee hitting /upload/callback gets 403."""
    app = FastAPI()
    app.include_router(router)

    # Override require_admin to raise 403, simulating a regular employee
    from fastapi import HTTPException as FastAPIHTTPException

    def _deny() -> None:
        raise FastAPIHTTPException(status_code=403, detail="HR admin access required")

    app.dependency_overrides[require_admin] = _deny

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/upload/callback",
            json={
                "files": [{"url": "https://cdn.example.com/t.pdf", "name": "t.pdf", "size": 512, "key": "k"}],
                "department": "engineering",
            },
            headers={"Authorization": "Bearer employee-token"},
        )

    assert response.status_code == 403
    assert "HR admin" in response.json()["detail"]


@pytest.mark.asyncio
async def test_unauthenticated_upload_returns_401() -> None:
    """No Authorization header → 401 before any business logic runs."""
    app = FastAPI()
    app.include_router(router)
    # No overrides — real require_admin → real get_current_user → 401

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/upload/callback",
            json={
                "files": [{"url": "https://cdn.example.com/t.pdf", "name": "t.pdf", "size": 100, "key": "k"}],
                "department": "hr",
            },
            # No Authorization header
        )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_documents_employee_returns_403() -> None:
    """GET /upload/documents is also admin-only — employee gets 403."""
    app = FastAPI()
    app.include_router(router)

    from fastapi import HTTPException as FastAPIHTTPException

    def _deny() -> None:
        raise FastAPIHTTPException(status_code=403, detail="HR admin access required")

    app.dependency_overrides[require_admin] = _deny

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(
            "/upload/documents",
            headers={"Authorization": "Bearer employee-token"},
        )

    assert response.status_code == 403
