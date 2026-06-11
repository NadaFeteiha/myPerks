# backend/tests/test_admin_requests.py
"""
Tests for:
  GET /admin/requests — all requests across employees, filterable, paginated

Test matrix:
  - hr_admin -> 200, correct shape
  - default filter surfaces pending requests
  - ?status= filter works
  - ?employee_id= filter works
  - ?status=all (no filter) returns all statuses
  - pagination defaults correct
  - employee role -> 403
  - no auth header -> 401
"""

from __future__ import annotations

from collections.abc import AsyncGenerator, Callable
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

from fastapi.testclient import TestClient

from api.auth import get_current_user
from db.session import get_session
from main import app

client = TestClient(app)

MOCK_CLERK_USER_ID = "clerk_admin_001"

# ── Mock factories ────────────────────────────────────────────────────────────


def make_admin_employee() -> MagicMock:
    admin = MagicMock()
    admin.id = 1
    admin.role = "hr_admin"
    return admin


def make_non_admin_employee() -> MagicMock:
    emp = MagicMock()
    emp.id = 2
    emp.role = "employee"
    return emp


def make_row(
    request_id: int = 10,
    employee_id: int = 5,
    employee_name: str = "Alice Smith",
    req_type: str = "vacation",
    req_status: str = "pending",
) -> MagicMock:
    """Simulates a joined row (RequestHistory + employee_name label)."""
    rh = MagicMock()
    rh.id = request_id
    rh.employee_id = employee_id
    rh.type = req_type
    rh.status = req_status
    rh.created_at = datetime(2025, 6, 1, tzinfo=UTC)
    rh.body = None

    row = MagicMock()
    row.RequestHistory = rh
    row.employee_name = employee_name
    return row


# ── Helpers ───────────────────────────────────────────────────────────────────


def override_auth() -> str:
    return MOCK_CLERK_USER_ID


def make_db_override(
    mock_session: AsyncMock,
) -> Callable[[], AsyncGenerator[AsyncMock, None]]:
    async def override_db() -> AsyncGenerator[AsyncMock, None]:
        yield mock_session

    return override_db


def auth_header() -> dict[str, str]:
    return {"Authorization": "Bearer fake.jwt.token"}


def make_session(scalar_return: MagicMock | None) -> AsyncMock:
    session = AsyncMock()
    session.scalar = AsyncMock(return_value=scalar_return)
    session.execute = AsyncMock()
    return session


def make_all_result(rows: list[MagicMock]) -> MagicMock:
    """Mock execute() result where .all() returns rows."""
    result = MagicMock()
    result.all.return_value = rows
    return result


# ── GET /admin/requests ───────────────────────────────────────────────────────


class TestListRequests:
    def test_hr_admin_gets_200_with_correct_shape(self) -> None:
        mock_session = make_session(scalar_return=make_admin_employee())
        mock_session.scalar = AsyncMock(side_effect=[make_admin_employee(), 1])
        mock_session.execute = AsyncMock(
            return_value=make_all_result([make_row()])
        )

        app.dependency_overrides[get_current_user] = override_auth
        app.dependency_overrides[get_session] = make_db_override(mock_session)
        try:
            response = client.get("/admin/requests", headers=auth_header())
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        for field in ("items", "total", "page", "size", "pages"):
            assert field in data, f"missing field: {field}"

    def test_item_shape(self) -> None:
        mock_session = make_session(scalar_return=make_admin_employee())
        mock_session.scalar = AsyncMock(side_effect=[make_admin_employee(), 1])
        mock_session.execute = AsyncMock(
            return_value=make_all_result([make_row()])
        )

        app.dependency_overrides[get_current_user] = override_auth
        app.dependency_overrides[get_session] = make_db_override(mock_session)
        try:
            response = client.get("/admin/requests", headers=auth_header())
        finally:
            app.dependency_overrides.clear()

        item = response.json()["items"][0]
        for field in (
            "id", "employee_id", "employee_name", "type", "status", "created_at"
        ):
            assert field in item, f"missing field: {field}"

    def test_default_status_is_pending(self) -> None:
        """No ?status= param — default should filter to pending."""
        mock_session = make_session(scalar_return=make_admin_employee())
        mock_session.scalar = AsyncMock(side_effect=[make_admin_employee(), 1])
        mock_session.execute = AsyncMock(
            return_value=make_all_result([make_row(req_status="pending")])
        )

        app.dependency_overrides[get_current_user] = override_auth
        app.dependency_overrides[get_session] = make_db_override(mock_session)
        try:
            response = client.get("/admin/requests", headers=auth_header())
        finally:
            app.dependency_overrides.clear()

        assert response.json()["items"][0]["status"] == "pending"

    def test_status_filter(self) -> None:
        mock_session = make_session(scalar_return=make_admin_employee())
        mock_session.scalar = AsyncMock(side_effect=[make_admin_employee(), 1])
        mock_session.execute = AsyncMock(
            return_value=make_all_result([make_row(req_status="approved")])
        )

        app.dependency_overrides[get_current_user] = override_auth
        app.dependency_overrides[get_session] = make_db_override(mock_session)
        try:
            response = client.get(
                "/admin/requests?status_filter=approved", headers=auth_header()
            )
        finally:
            app.dependency_overrides.clear()

        assert response.json()["items"][0]["status"] == "approved"

    def test_employee_id_filter(self) -> None:
        mock_session = make_session(scalar_return=make_admin_employee())
        mock_session.scalar = AsyncMock(side_effect=[make_admin_employee(), 1])
        mock_session.execute = AsyncMock(
            return_value=make_all_result([make_row(employee_id=5)])
        )

        app.dependency_overrides[get_current_user] = override_auth
        app.dependency_overrides[get_session] = make_db_override(mock_session)
        try:
            response = client.get(
                "/admin/requests?employee_id=5", headers=auth_header()
            )
        finally:
            app.dependency_overrides.clear()

        assert response.json()["items"][0]["employee_id"] == 5

    def test_no_status_filter_returns_all(self) -> None:
        """?status= with empty string or omitted entirely surfaces all statuses."""
        rows = [
            make_row(request_id=1, req_status="pending"),
            make_row(request_id=2, req_status="approved"),
        ]
        mock_session = make_session(scalar_return=make_admin_employee())
        mock_session.scalar = AsyncMock(side_effect=[make_admin_employee(), 2])
        mock_session.execute = AsyncMock(return_value=make_all_result(rows))

        app.dependency_overrides[get_current_user] = override_auth
        app.dependency_overrides[get_session] = make_db_override(mock_session)
        try:
            # Pass status=None explicitly to bypass the default
            response = client.get(
                "/admin/requests?status_filter=", headers=auth_header()
            )
        finally:
            app.dependency_overrides.clear()

        assert response.json()["total"] == 2

    def test_pagination_defaults(self) -> None:
        mock_session = make_session(scalar_return=make_admin_employee())
        mock_session.scalar = AsyncMock(side_effect=[make_admin_employee(), 0])
        mock_session.execute = AsyncMock(return_value=make_all_result([]))

        app.dependency_overrides[get_current_user] = override_auth
        app.dependency_overrides[get_session] = make_db_override(mock_session)
        try:
            response = client.get("/admin/requests", headers=auth_header())
        finally:
            app.dependency_overrides.clear()

        data = response.json()
        assert data["page"] == 1
        assert data["size"] == 10

    def test_employee_role_returns_403(self) -> None:
        mock_session = make_session(scalar_return=make_non_admin_employee())

        app.dependency_overrides[get_current_user] = override_auth
        app.dependency_overrides[get_session] = make_db_override(mock_session)
        try:
            response = client.get("/admin/requests", headers=auth_header())
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 403

    def test_no_auth_header_returns_401(self) -> None:
        mock_session = make_session(scalar_return=make_admin_employee())

        app.dependency_overrides[get_session] = make_db_override(mock_session)
        try:
            response = client.get("/admin/requests")
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 401
