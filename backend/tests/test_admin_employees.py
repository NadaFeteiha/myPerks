# backend/tests/test_admin_employees.py
"""
Tests for:
  GET /admin/employees          — list (paginated, searchable)
  GET /admin/employees/{id}     — detail (balances, history, linked flag)

Test matrix:
  - hr_admin role            -> 200, correct shape
  - employee role            -> 403
  - no matching Employee row -> 403
  - no Authorization header  -> 401
  - unknown employee id      -> 404
"""

from __future__ import annotations

from collections.abc import AsyncGenerator, Callable
from unittest.mock import AsyncMock, MagicMock

from fastapi.testclient import TestClient

from api.auth import get_current_user
from db.session import get_session
from main import app

client = TestClient(app)

# ── Mock data ─────────────────────────────────────────────────────────────────

MOCK_CLERK_USER_ID = "clerk_admin_001"


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


def make_employee(
    emp_id: int = 10,
    name: str = "Alice Smith",
    email: str = "alice@example.com",
    department: str = "engineering",
    role: str = "employee",
    clerk_user_id: str | None = "clerk_emp_001",
) -> MagicMock:
    emp = MagicMock()
    emp.id = emp_id
    emp.name = name
    emp.email = email
    emp.department = department
    emp.role = role
    emp.clerk_user_id = clerk_user_id
    emp.joined_date = "2023-03-15"
    emp.benefits_year_reset = "2025-01-01"
    emp.vacation_balances = []
    emp.request_histories = []
    return emp


def make_balance(leave_type: str = "vacation") -> MagicMock:
    b = MagicMock()
    b.leave_type = leave_type
    b.total_days = 20.0
    b.used_days = 5.0
    b.remaining_days = 15.0
    return b


def make_request_history() -> MagicMock:
    from datetime import UTC, datetime

    r = MagicMock()
    r.id = 99
    r.type = "vacation"
    r.status = "approved"
    r.created_at = datetime(2025, 6, 1, tzinfo=UTC)
    r.body = '{"days": 5}'
    return r


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
    """Mock session for require_admin's scalar() lookup."""
    session = AsyncMock()
    session.scalar = AsyncMock(return_value=scalar_return)
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    return session


def make_scalar_one_result(value: MagicMock | None) -> MagicMock:
    result = MagicMock()
    result.scalar_one_or_none.return_value = value
    return result


def make_scalars_all_result(values: list[MagicMock]) -> MagicMock:
    result = MagicMock()
    result.scalars.return_value.all.return_value = values
    return result


# ── GET /admin/employees ──────────────────────────────────────────────────────


class TestListEmployees:
    def test_hr_admin_gets_200_with_correct_shape(self) -> None:
        emp = make_employee()
        mock_session = make_session(scalar_return=make_admin_employee())
        # scalar() for count, execute() for rows
        mock_session.scalar = AsyncMock(
            side_effect=[make_admin_employee(), 1]
        )
        mock_session.execute = AsyncMock(
            return_value=make_scalars_all_result([emp])
        )

        app.dependency_overrides[get_current_user] = override_auth
        app.dependency_overrides[get_session] = make_db_override(mock_session)
        try:
            response = client.get("/admin/employees", headers=auth_header())
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "size" in data
        assert "pages" in data

    def test_item_shape(self) -> None:
        emp = make_employee()
        mock_session = make_session(scalar_return=make_admin_employee())
        mock_session.scalar = AsyncMock(side_effect=[make_admin_employee(), 1])
        mock_session.execute = AsyncMock(
            return_value=make_scalars_all_result([emp])
        )

        app.dependency_overrides[get_current_user] = override_auth
        app.dependency_overrides[get_session] = make_db_override(mock_session)
        try:
            response = client.get("/admin/employees", headers=auth_header())
        finally:
            app.dependency_overrides.clear()

        item = response.json()["items"][0]
        for field in ("id", "name", "email", "department", "role", "joined_date", "linked"):
            assert field in item, f"missing field: {field}"

    def test_linked_true_when_clerk_id_present(self) -> None:
        emp = make_employee(clerk_user_id="clerk_emp_001")
        mock_session = make_session(scalar_return=make_admin_employee())
        mock_session.scalar = AsyncMock(side_effect=[make_admin_employee(), 1])
        mock_session.execute = AsyncMock(
            return_value=make_scalars_all_result([emp])
        )

        app.dependency_overrides[get_current_user] = override_auth
        app.dependency_overrides[get_session] = make_db_override(mock_session)
        try:
            response = client.get("/admin/employees", headers=auth_header())
        finally:
            app.dependency_overrides.clear()

        assert response.json()["items"][0]["linked"] is True

    def test_linked_false_when_clerk_id_absent(self) -> None:
        emp = make_employee(clerk_user_id=None)
        mock_session = make_session(scalar_return=make_admin_employee())
        mock_session.scalar = AsyncMock(side_effect=[make_admin_employee(), 1])
        mock_session.execute = AsyncMock(
            return_value=make_scalars_all_result([emp])
        )

        app.dependency_overrides[get_current_user] = override_auth
        app.dependency_overrides[get_session] = make_db_override(mock_session)
        try:
            response = client.get("/admin/employees", headers=auth_header())
        finally:
            app.dependency_overrides.clear()

        assert response.json()["items"][0]["linked"] is False

    def test_employee_role_returns_403(self) -> None:
        mock_session = make_session(scalar_return=make_non_admin_employee())

        app.dependency_overrides[get_current_user] = override_auth
        app.dependency_overrides[get_session] = make_db_override(mock_session)
        try:
            response = client.get("/admin/employees", headers=auth_header())
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 403

    def test_no_employee_record_returns_403(self) -> None:
        mock_session = make_session(scalar_return=None)

        app.dependency_overrides[get_current_user] = override_auth
        app.dependency_overrides[get_session] = make_db_override(mock_session)
        try:
            response = client.get("/admin/employees", headers=auth_header())
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 403

    def test_no_auth_header_returns_401(self) -> None:
        mock_session = make_session(scalar_return=make_admin_employee())

        app.dependency_overrides[get_session] = make_db_override(mock_session)
        try:
            response = client.get("/admin/employees")
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 401


# ── GET /admin/employees/{id} ─────────────────────────────────────────────────


class TestGetEmployeeDetail:
    def test_hr_admin_gets_200_with_correct_shape(self) -> None:
        emp = make_employee()
        emp.vacation_balances = [make_balance()]
        emp.request_histories = [make_request_history()]

        mock_session = make_session(scalar_return=make_admin_employee())
        mock_session.execute = AsyncMock(
            return_value=make_scalar_one_result(emp)
        )

        app.dependency_overrides[get_current_user] = override_auth
        app.dependency_overrides[get_session] = make_db_override(mock_session)
        try:
            response = client.get("/admin/employees/10", headers=auth_header())
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        for field in (
            "id", "name", "email", "department", "role",
            "joined_date", "benefits_year_reset", "linked",
            "balances", "request_history",
        ):
            assert field in data, f"missing field: {field}"

    def test_balances_shape(self) -> None:
        emp = make_employee()
        emp.vacation_balances = [make_balance()]
        emp.request_histories = []

        mock_session = make_session(scalar_return=make_admin_employee())
        mock_session.execute = AsyncMock(
            return_value=make_scalar_one_result(emp)
        )

        app.dependency_overrides[get_current_user] = override_auth
        app.dependency_overrides[get_session] = make_db_override(mock_session)
        try:
            response = client.get("/admin/employees/10", headers=auth_header())
        finally:
            app.dependency_overrides.clear()

        balance = response.json()["balances"][0]
        for field in ("leave_type", "total_days", "used_days", "remaining_days"):
            assert field in balance

    def test_request_history_shape(self) -> None:
        emp = make_employee()
        emp.vacation_balances = []
        emp.request_histories = [make_request_history()]

        mock_session = make_session(scalar_return=make_admin_employee())
        mock_session.execute = AsyncMock(
            return_value=make_scalar_one_result(emp)
        )

        app.dependency_overrides[get_current_user] = override_auth
        app.dependency_overrides[get_session] = make_db_override(mock_session)
        try:
            response = client.get("/admin/employees/10", headers=auth_header())
        finally:
            app.dependency_overrides.clear()

        req = response.json()["request_history"][0]
        for field in ("id", "type", "status", "created_at"):
            assert field in req

    def test_linked_true_when_clerk_id_present(self) -> None:
        emp = make_employee(clerk_user_id="clerk_emp_001")
        emp.vacation_balances = []
        emp.request_histories = []

        mock_session = make_session(scalar_return=make_admin_employee())
        mock_session.execute = AsyncMock(
            return_value=make_scalar_one_result(emp)
        )

        app.dependency_overrides[get_current_user] = override_auth
        app.dependency_overrides[get_session] = make_db_override(mock_session)
        try:
            response = client.get("/admin/employees/10", headers=auth_header())
        finally:
            app.dependency_overrides.clear()

        assert response.json()["linked"] is True

    def test_linked_false_when_clerk_id_absent(self) -> None:
        emp = make_employee(clerk_user_id=None)
        emp.vacation_balances = []
        emp.request_histories = []

        mock_session = make_session(scalar_return=make_admin_employee())
        mock_session.execute = AsyncMock(
            return_value=make_scalar_one_result(emp)
        )

        app.dependency_overrides[get_current_user] = override_auth
        app.dependency_overrides[get_session] = make_db_override(mock_session)
        try:
            response = client.get("/admin/employees/10", headers=auth_header())
        finally:
            app.dependency_overrides.clear()

        assert response.json()["linked"] is False

    def test_unknown_id_returns_404(self) -> None:
        mock_session = make_session(scalar_return=make_admin_employee())
        mock_session.execute = AsyncMock(
            return_value=make_scalar_one_result(None)
        )

        app.dependency_overrides[get_current_user] = override_auth
        app.dependency_overrides[get_session] = make_db_override(mock_session)
        try:
            response = client.get("/admin/employees/999999", headers=auth_header())
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 404

    def test_employee_role_returns_403(self) -> None:
        mock_session = make_session(scalar_return=make_non_admin_employee())

        app.dependency_overrides[get_current_user] = override_auth
        app.dependency_overrides[get_session] = make_db_override(mock_session)
        try:
            response = client.get("/admin/employees/10", headers=auth_header())
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 403

    def test_no_auth_header_returns_401(self) -> None:
        mock_session = make_session(scalar_return=make_admin_employee())

        app.dependency_overrides[get_session] = make_db_override(mock_session)
        try:
            response = client.get("/admin/employees/10")
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 401
