# backend/tests/test_admin_employee_write.py
"""
Tests for:
  POST  /admin/employees        — pre-create employee row
  PATCH /admin/employees/{id}   — update department / role

Test matrix:
  - hr_admin -> 201 / 200 success + correct shape
  - duplicate email -> 409
  - unknown id -> 404
  - invalid department / role -> 422 (Pydantic validation)
  - employee role -> 403
  - no auth header -> 401
  - no fields in PATCH body -> no-op, still 200
"""

from __future__ import annotations

from collections.abc import AsyncGenerator, Callable
from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock

from fastapi.testclient import TestClient
from httpx import Response

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


def make_employee(
    emp_id: int = 10,
    name: str = "Alice Smith",
    email: str = "alice@example.com",
    department: str = "engineering",
    role: str = "employee",
    clerk_user_id: str | None = None,
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
    return emp


CURRENT_YEAR = datetime.now(UTC).year


def make_balance(
    leave_type: str,
    total_days: float,
    used_days: float = 0.0,
    year: int = CURRENT_YEAR,
) -> MagicMock:
    bal = MagicMock()
    bal.leave_type = leave_type
    bal.total_days = total_days
    bal.used_days = used_days
    bal.year = year
    bal.remaining_days = total_days - used_days
    return bal


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
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.add = MagicMock()
    return session


def make_scalar_one_result(value: MagicMock | None) -> MagicMock:
    result = MagicMock()
    result.scalar_one_or_none.return_value = value
    return result


VALID_PRE_CREATE_BODY = {
    "name": "Alice Smith",
    "email": "alice@example.com",
    "department": "engineering",
    "joined_date": "2023-03-15",
    "benefits_year_reset": "2025-01-01",
}


# ── POST /admin/employees ─────────────────────────────────────────────────────


class TestPreCreateEmployee:
    def test_hr_admin_creates_employee_201(self) -> None:
        mock_session = make_session(scalar_return=make_admin_employee())
        # execute() for duplicate-email check returns None (no existing row)
        mock_session.execute = AsyncMock(return_value=make_scalar_one_result(None))
        # refresh() populates emp fields after commit
        mock_session.refresh = AsyncMock(side_effect=lambda e: None)

        # Simulate the created employee being returned after refresh
        emp_mock = make_employee()

        async def fake_refresh(obj: MagicMock) -> None:
            obj.id = emp_mock.id
            obj.name = emp_mock.name
            obj.email = emp_mock.email
            obj.department = emp_mock.department
            obj.role = emp_mock.role
            obj.joined_date = emp_mock.joined_date
            obj.benefits_year_reset = emp_mock.benefits_year_reset
            obj.clerk_user_id = None

        mock_session.refresh = AsyncMock(side_effect=fake_refresh)

        app.dependency_overrides[get_current_user] = override_auth
        app.dependency_overrides[get_session] = make_db_override(mock_session)
        try:
            response = client.post(
                "/admin/employees",
                json=VALID_PRE_CREATE_BODY,
                headers=auth_header(),
            )
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 201
        data = response.json()
        for field in (
            "id",
            "name",
            "email",
            "department",
            "role",
            "joined_date",
            "benefits_year_reset",
            "linked",
        ):
            assert field in data, f"missing field: {field}"

    def test_linked_is_false_on_pre_create(self) -> None:
        emp_mock = make_employee()

        async def fake_refresh(obj: MagicMock) -> None:
            obj.id = emp_mock.id
            obj.name = emp_mock.name
            obj.email = emp_mock.email
            obj.department = emp_mock.department
            obj.role = emp_mock.role
            obj.joined_date = emp_mock.joined_date
            obj.benefits_year_reset = emp_mock.benefits_year_reset
            obj.clerk_user_id = None

        mock_session = make_session(scalar_return=make_admin_employee())
        mock_session.execute = AsyncMock(return_value=make_scalar_one_result(None))
        mock_session.refresh = AsyncMock(side_effect=fake_refresh)

        app.dependency_overrides[get_current_user] = override_auth
        app.dependency_overrides[get_session] = make_db_override(mock_session)
        try:
            response = client.post(
                "/admin/employees",
                json=VALID_PRE_CREATE_BODY,
                headers=auth_header(),
            )
        finally:
            app.dependency_overrides.clear()

        assert response.json()["linked"] is False

    def test_duplicate_email_returns_409(self) -> None:
        mock_session = make_session(scalar_return=make_admin_employee())
        # execute() for duplicate-email check returns an existing employee
        mock_session.execute = AsyncMock(
            return_value=make_scalar_one_result(make_employee())
        )

        app.dependency_overrides[get_current_user] = override_auth
        app.dependency_overrides[get_session] = make_db_override(mock_session)
        try:
            response = client.post(
                "/admin/employees",
                json=VALID_PRE_CREATE_BODY,
                headers=auth_header(),
            )
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 409
        assert "email" in response.json()["detail"].lower()

    def test_invalid_department_returns_422(self) -> None:
        mock_session = make_session(scalar_return=make_admin_employee())

        app.dependency_overrides[get_current_user] = override_auth
        app.dependency_overrides[get_session] = make_db_override(mock_session)
        try:
            response = client.post(
                "/admin/employees",
                json={**VALID_PRE_CREATE_BODY, "department": "invalid_dept"},
                headers=auth_header(),
            )
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 422

    def test_employee_role_returns_403(self) -> None:
        mock_session = make_session(scalar_return=make_non_admin_employee())

        app.dependency_overrides[get_current_user] = override_auth
        app.dependency_overrides[get_session] = make_db_override(mock_session)
        try:
            response = client.post(
                "/admin/employees",
                json=VALID_PRE_CREATE_BODY,
                headers=auth_header(),
            )
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 403

    def test_no_auth_header_returns_401(self) -> None:
        mock_session = make_session(scalar_return=make_admin_employee())

        app.dependency_overrides[get_session] = make_db_override(mock_session)
        try:
            response = client.post("/admin/employees", json=VALID_PRE_CREATE_BODY)
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 401


# ── PATCH /admin/employees/{id} ───────────────────────────────────────────────


class TestPatchEmployee:
    def test_hr_admin_updates_department_200(self) -> None:
        emp = make_employee(department="engineering")

        async def fake_refresh(obj: MagicMock) -> None:
            obj.department = "sales"

        mock_session = make_session(scalar_return=make_admin_employee())
        mock_session.execute = AsyncMock(return_value=make_scalar_one_result(emp))
        mock_session.refresh = AsyncMock(side_effect=fake_refresh)

        app.dependency_overrides[get_current_user] = override_auth
        app.dependency_overrides[get_session] = make_db_override(mock_session)
        try:
            response = client.patch(
                "/admin/employees/10",
                json={"department": "sales"},
                headers=auth_header(),
            )
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        for field in (
            "id",
            "name",
            "email",
            "department",
            "role",
            "joined_date",
            "benefits_year_reset",
            "linked",
        ):
            assert field in data, f"missing field: {field}"

    def test_hr_admin_updates_role_200(self) -> None:
        emp = make_employee(role="employee")

        async def fake_refresh(obj: MagicMock) -> None:
            obj.role = "hr_admin"

        mock_session = make_session(scalar_return=make_admin_employee())
        mock_session.execute = AsyncMock(return_value=make_scalar_one_result(emp))
        mock_session.refresh = AsyncMock(side_effect=fake_refresh)

        app.dependency_overrides[get_current_user] = override_auth
        app.dependency_overrides[get_session] = make_db_override(mock_session)
        try:
            response = client.patch(
                "/admin/employees/10",
                json={"role": "hr_admin"},
                headers=auth_header(),
            )
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 200

    def test_empty_body_is_noop_200(self) -> None:
        emp = make_employee()

        mock_session = make_session(scalar_return=make_admin_employee())
        mock_session.execute = AsyncMock(return_value=make_scalar_one_result(emp))
        mock_session.refresh = AsyncMock(side_effect=lambda e: None)

        app.dependency_overrides[get_current_user] = override_auth
        app.dependency_overrides[get_session] = make_db_override(mock_session)
        try:
            response = client.patch(
                "/admin/employees/10",
                json={},
                headers=auth_header(),
            )
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 200

    def test_invalid_department_returns_422(self) -> None:
        mock_session = make_session(scalar_return=make_admin_employee())

        app.dependency_overrides[get_current_user] = override_auth
        app.dependency_overrides[get_session] = make_db_override(mock_session)
        try:
            response = client.patch(
                "/admin/employees/10",
                json={"department": "invalid_dept"},
                headers=auth_header(),
            )
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 422

    def test_invalid_role_returns_422(self) -> None:
        mock_session = make_session(scalar_return=make_admin_employee())

        app.dependency_overrides[get_current_user] = override_auth
        app.dependency_overrides[get_session] = make_db_override(mock_session)
        try:
            response = client.patch(
                "/admin/employees/10",
                json={"role": "superuser"},
                headers=auth_header(),
            )
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 422

    def test_unknown_id_returns_404(self) -> None:
        mock_session = make_session(scalar_return=make_admin_employee())
        mock_session.execute = AsyncMock(return_value=make_scalar_one_result(None))

        app.dependency_overrides[get_current_user] = override_auth
        app.dependency_overrides[get_session] = make_db_override(mock_session)
        try:
            response = client.patch(
                "/admin/employees/999999",
                json={"department": "sales"},
                headers=auth_header(),
            )
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 404

    def test_employee_role_returns_403(self) -> None:
        mock_session = make_session(scalar_return=make_non_admin_employee())

        app.dependency_overrides[get_current_user] = override_auth
        app.dependency_overrides[get_session] = make_db_override(mock_session)
        try:
            response = client.patch(
                "/admin/employees/10",
                json={"department": "sales"},
                headers=auth_header(),
            )
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 403

    def test_no_auth_header_returns_401(self) -> None:
        mock_session = make_session(scalar_return=make_admin_employee())

        app.dependency_overrides[get_session] = make_db_override(mock_session)
        try:
            response = client.patch("/admin/employees/10", json={"department": "sales"})
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 401


# ── POST /admin/employees — balances (T40) ────────────────────────────────────


class TestPreCreateBalances:
    def _run_post(self, body: dict[str, Any]) -> Response:
        emp_mock = make_employee()

        async def fake_refresh(obj: MagicMock) -> None:
            obj.id = emp_mock.id
            obj.name = emp_mock.name
            obj.email = emp_mock.email
            obj.department = emp_mock.department
            obj.role = emp_mock.role
            obj.joined_date = emp_mock.joined_date
            obj.benefits_year_reset = emp_mock.benefits_year_reset
            obj.clerk_user_id = None

        mock_session = make_session(scalar_return=make_admin_employee())
        mock_session.execute = AsyncMock(return_value=make_scalar_one_result(None))
        mock_session.refresh = AsyncMock(side_effect=fake_refresh)

        app.dependency_overrides[get_current_user] = override_auth
        app.dependency_overrides[get_session] = make_db_override(mock_session)
        try:
            return client.post("/admin/employees", json=body, headers=auth_header())
        finally:
            app.dependency_overrides.clear()

    def test_defaults_when_balances_omitted(self) -> None:
        resp = self._run_post(VALID_PRE_CREATE_BODY)
        assert resp.status_code == 201
        balances = {b["leave_type"]: b for b in resp.json()["balances"]}
        assert balances["vacation"]["total_days"] == 15.0
        assert balances["sick"]["total_days"] == 10.0
        assert balances["pto"]["total_days"] == 5.0
        assert all(b["used_days"] == 0.0 for b in balances.values())

    def test_partial_balances_merged_over_defaults(self) -> None:
        body = {
            **VALID_PRE_CREATE_BODY,
            "balances": [{"leave_type": "vacation", "total_days": 25}],
        }
        resp = self._run_post(body)
        assert resp.status_code == 201
        balances = {b["leave_type"]: b for b in resp.json()["balances"]}
        assert balances["vacation"]["total_days"] == 25.0  # overridden
        assert balances["sick"]["total_days"] == 10.0  # default
        assert balances["pto"]["total_days"] == 5.0  # default
        assert balances["vacation"]["remaining_days"] == 25.0

    def test_negative_total_days_422(self) -> None:
        body = {
            **VALID_PRE_CREATE_BODY,
            "balances": [{"leave_type": "vacation", "total_days": -1}],
        }
        assert self._run_post(body).status_code == 422

    def test_unknown_leave_type_422(self) -> None:
        body = {
            **VALID_PRE_CREATE_BODY,
            "balances": [{"leave_type": "bonus", "total_days": 5}],
        }
        assert self._run_post(body).status_code == 422

    def test_duplicate_leave_type_422(self) -> None:
        body = {
            **VALID_PRE_CREATE_BODY,
            "balances": [
                {"leave_type": "vacation", "total_days": 5},
                {"leave_type": "vacation", "total_days": 6},
            ],
        }
        assert self._run_post(body).status_code == 422


# ── PATCH /admin/employees/{id} — balances (T40) ──────────────────────────────


class TestPatchBalances:
    def _run_patch(self, emp: MagicMock, body: dict[str, Any]) -> Response:
        mock_session = make_session(scalar_return=make_admin_employee())
        mock_session.execute = AsyncMock(return_value=make_scalar_one_result(emp))
        mock_session.refresh = AsyncMock(side_effect=lambda e: None)

        app.dependency_overrides[get_current_user] = override_auth
        app.dependency_overrides[get_session] = make_db_override(mock_session)
        try:
            return client.patch("/admin/employees/10", json=body, headers=auth_header())
        finally:
            app.dependency_overrides.clear()

    def test_updates_current_year_total(self) -> None:
        emp = make_employee()
        emp.vacation_balances = [make_balance("vacation", 15.0)]
        resp = self._run_patch(
            emp, {"balances": [{"leave_type": "vacation", "total_days": 25}]}
        )
        assert resp.status_code == 200
        balances = {b["leave_type"]: b for b in resp.json()["balances"]}
        assert balances["vacation"]["total_days"] == 25.0

    def test_missing_row_returns_404(self) -> None:
        emp = make_employee()
        emp.vacation_balances = [make_balance("vacation", 15.0)]  # no pto row
        resp = self._run_patch(
            emp, {"balances": [{"leave_type": "pto", "total_days": 8}]}
        )
        assert resp.status_code == 404

    def test_prior_year_row_not_matched_404(self) -> None:
        emp = make_employee()
        # Only a previous-year vacation row exists for the current year filter.
        emp.vacation_balances = [make_balance("vacation", 15.0, year=CURRENT_YEAR - 1)]
        resp = self._run_patch(
            emp, {"balances": [{"leave_type": "vacation", "total_days": 25}]}
        )
        assert resp.status_code == 404
