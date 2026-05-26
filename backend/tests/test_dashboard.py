# backend/tests/test_dashboard.py

import datetime
from collections.abc import AsyncGenerator, Callable
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from api.auth import get_current_user
from db.session import get_session
from main import app

client = TestClient(app)

# ── Mock data ─────────────────────────────────────────────────────────────────

MOCK_CLERK_USER_ID = "clerk_user_001"

mock_employee = MagicMock()
mock_employee.id = 1
mock_employee.clerk_user_id = MOCK_CLERK_USER_ID
mock_employee.name = "Alice Johnson"
mock_employee.department = "Engineering"

mock_vacation = MagicMock()
mock_vacation.leave_type = "vacation"
mock_vacation.total_days = 15.0
mock_vacation.used_days = 3.0
mock_vacation.remaining_days = 12.0

mock_sick = MagicMock()
mock_sick.leave_type = "sick"
mock_sick.total_days = 10.0
mock_sick.used_days = 1.0
mock_sick.remaining_days = 9.0

mock_pto = MagicMock()
mock_pto.leave_type = "pto"
mock_pto.total_days = 5.0
mock_pto.used_days = 0.0
mock_pto.remaining_days = 5.0

MOCK_BALANCES = [mock_vacation, mock_sick, mock_pto]

mock_request_1 = MagicMock()
mock_request_1.id = 1
mock_request_1.type = "vacation"
mock_request_1.status = "approved"
mock_request_1.created_at = datetime.datetime(2026, 3, 10)
mock_request_1.body = '{"days": 3}'

mock_request_2 = MagicMock()
mock_request_2.id = 2
mock_request_2.type = "pto"
mock_request_2.status = "pending"
mock_request_2.created_at = datetime.datetime(2026, 5, 1)
mock_request_2.body = '{"days": 1}'

MOCK_REQUESTS = [mock_request_1, mock_request_2]


def override_auth() -> str:
    """Replacement for get_current_user — returns mock clerk_user_id."""
    return MOCK_CLERK_USER_ID


def make_db_override(
    mock_session: AsyncMock,
) -> Callable[[], AsyncGenerator[AsyncMock, None]]:
    """
    Returns an async generator that yields the mock session.
    This matches the signature of get_db() exactly.
    """

    async def override_db() -> AsyncGenerator[AsyncMock, None]:
        yield mock_session

    return override_db


def auth_header() -> dict[str, str]:
    """Returns a fake Authorization header."""
    return {"Authorization": "Bearer fake.jwt.token"}


def make_mock_session(return_values: list[MagicMock]) -> AsyncMock:
    """
    Creates a mock DB session whose execute() returns values in order.
    Uses side_effect to return a different value on each successive call.
    """
    mock_session = AsyncMock()
    mock_session.execute = AsyncMock(side_effect=return_values)
    return mock_session


def make_scalar_result(rows: list[MagicMock]) -> MagicMock:
    """Creates a mock result where .scalars().all() returns rows."""
    result = MagicMock()
    result.scalars.return_value.all.return_value = rows
    return result


def make_count_result(count: int) -> MagicMock:
    """Creates a mock result where .scalar() returns count."""
    result = MagicMock()
    result.scalar.return_value = count
    return result


# ── GET /me/vacation ──────────────────────────────────────────────────────────


class TestGetVacationBalance:
    def test_returns_balances_for_authenticated_user(self) -> None:
        """Happy path — valid JWT + employee in DB → returns balances."""
        mock_session = make_mock_session([make_scalar_result(MOCK_BALANCES)])
        app.dependency_overrides[get_current_user] = override_auth
        app.dependency_overrides[get_session] = make_db_override(mock_session)
        try:
            with patch(
                "api.routers.dashboard._get_employee",
                new_callable=AsyncMock,
                return_value=mock_employee,
            ):
                response = client.get("/me/vacation", headers=auth_header())
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert "year" in data
        assert len(data["balances"]) == 3
        assert data["balances"][0]["leave_type"] == "vacation"
        assert data["balances"][0]["total_days"] == 15.0
        assert data["balances"][0]["used_days"] == 3.0
        assert data["balances"][0]["remaining_days"] == 12.0

    def test_returns_401_without_token(self) -> None:
        """No Authorization header → 401."""
        response = client.get("/me/vacation")
        assert response.status_code == 401

    def test_returns_404_when_employee_not_found(self) -> None:
        """Valid JWT but employee not in DB → 404."""
        from fastapi import HTTPException

        mock_session = make_mock_session([])
        app.dependency_overrides[get_current_user] = override_auth
        app.dependency_overrides[get_session] = make_db_override(mock_session)
        try:
            with patch(
                "api.routers.dashboard._get_employee",
                new_callable=AsyncMock,
                side_effect=HTTPException(status_code=404, detail="Employee not found"),
            ):
                response = client.get("/me/vacation", headers=auth_header())
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 404


# ── GET /me/requests ──────────────────────────────────────────────────────────


class TestGetRequestHistory:
    def test_returns_paginated_requests(self) -> None:
        """Happy path — returns paginated request history."""
        mock_session = make_mock_session(
            [make_count_result(2), make_scalar_result(MOCK_REQUESTS)]
        )
        app.dependency_overrides[get_current_user] = override_auth
        app.dependency_overrides[get_session] = make_db_override(mock_session)
        try:
            with patch(
                "api.routers.dashboard._get_employee",
                new_callable=AsyncMock,
                return_value=mock_employee,
            ):
                response = client.get(
                    "/me/requests?page=1&page_size=10",
                    headers=auth_header(),
                )
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert data["page"] == 1
        assert data["page_size"] == 10
        assert len(data["items"]) == 2
        assert data["items"][0]["type"] == "vacation"
        assert data["items"][0]["status"] == "approved"

    def test_returns_401_without_token(self) -> None:
        """No Authorization header → 401."""
        response = client.get("/me/requests")
        assert response.status_code == 401

    def test_rejects_invalid_pagination_params(self) -> None:
        """
        page=0 violates ge=1 constraint → 422 Unprocessable Entity.
        ─────────────────────────────────────────────────────────────
        """
        app.dependency_overrides[get_current_user] = override_auth
        try:
            response = client.get(
                "/me/requests?page=0",
                headers=auth_header(),
            )
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 422


# ── GET /me/benefits-summary ──────────────────────────────────────────────────


class TestGetBenefitsSummary:
    def test_returns_summary_with_percent_used(self) -> None:
        """Happy path — returns summary with computed percent_used."""
        mock_session = make_mock_session([make_scalar_result(MOCK_BALANCES)])
        app.dependency_overrides[get_current_user] = override_auth
        app.dependency_overrides[get_session] = make_db_override(mock_session)
        try:
            with patch(
                "api.routers.dashboard._get_employee",
                new_callable=AsyncMock,
                return_value=mock_employee,
            ):
                response = client.get("/me/benefits-summary", headers=auth_header())
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
        assert len(data["summary"]) == 3

        vacation = next(
            item for item in data["summary"] if item["leave_type"] == "vacation"
        )
        assert vacation["percent_used"] == 20.0

        pto = next(item for item in data["summary"] if item["leave_type"] == "pto")
        assert pto["percent_used"] == 0.0

    def test_returns_401_without_token(self) -> None:
        """No Authorization header → 401."""
        response = client.get("/me/benefits-summary")
        assert response.status_code == 401
