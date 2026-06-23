import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from api.auth import get_current_user
from main import app

client = TestClient(app)

CLERK_USER_ID = "clerk_user_001"
AUTH_HEADER = {"Authorization": "Bearer valid.jwt.token"}


def _fake_get_current_user() -> str:
    return CLERK_USER_ID


def _make_employee(**overrides: object) -> MagicMock:
    employee = MagicMock()
    employee.id = 1
    employee.clerk_user_id = CLERK_USER_ID
    employee.name = "Alice Johnson"
    employee.email = "alice.johnson@myperks.dev"
    employee.department = "engineering"
    employee.role = "employee"
    employee.joined_date = datetime.date(2022, 3, 1)
    employee.benefits_year_reset = datetime.date(2027, 1, 1)
    for key, value in overrides.items():
        setattr(employee, key, value)
    return employee


def _make_session(scalar_results: list[object]) -> MagicMock:
    session = MagicMock()
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=False)
    session.scalar = AsyncMock(side_effect=scalar_results)
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.flush = AsyncMock()
    session.add = MagicMock()
    session.add_all = MagicMock()
    return session


# ── GET /employees/me ────────────────────────────────────────────────────────


class TestGetMe:
    def test_returns_employee_with_role_and_benefits_fields(self) -> None:
        employee = _make_employee()
        session = _make_session([employee])

        app.dependency_overrides[get_current_user] = _fake_get_current_user
        try:
            with patch("api.routers.employees.AsyncSessionLocal", return_value=session):
                response = client.get("/employees/me", headers=AUTH_HEADER)
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "employee"
        assert data["joined_date"] == "2022-03-01"
        assert data["benefits_year_reset"] == "2027-01-01"

    def test_returns_404_when_employee_not_found(self) -> None:
        session = _make_session([None])

        app.dependency_overrides[get_current_user] = _fake_get_current_user
        try:
            with patch("api.routers.employees.AsyncSessionLocal", return_value=session):
                response = client.get("/employees/me", headers=AUTH_HEADER)
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 404

    def test_returns_401_without_token(self) -> None:
        response = client.get("/employees/me")
        assert response.status_code == 401


# ── POST /employees/me ───────────────────────────────────────────────────────


class TestRegisterMe:
    def test_creates_employee_with_joined_date_and_benefits_year_reset(self) -> None:
        session = _make_session([None, None])

        async def fake_refresh(obj: object) -> None:
            obj.id = 42  # type: ignore[attr-defined]
            obj.role = "employee"  # type: ignore[attr-defined]

        session.refresh = AsyncMock(side_effect=fake_refresh)

        app.dependency_overrides[get_current_user] = _fake_get_current_user
        try:
            with patch("api.routers.employees.AsyncSessionLocal", return_value=session):
                response = client.post(
                    "/employees/me",
                    json={
                        "name": "New Hire",
                        "email": "new.hire@myperks.dev",
                        "department": "engineering",
                    },
                    headers=AUTH_HEADER,
                )
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 201
        data = response.json()
        today = datetime.date.today()
        assert data["role"] == "employee"
        assert data["joined_date"] == today.isoformat()
        assert (
            data["benefits_year_reset"]
            == datetime.date(today.year + 1, 1, 1).isoformat()
        )

    def test_returns_409_when_employee_already_exists(self) -> None:
        existing = _make_employee()
        session = _make_session([existing])

        app.dependency_overrides[get_current_user] = _fake_get_current_user
        try:
            with patch("api.routers.employees.AsyncSessionLocal", return_value=session):
                response = client.post(
                    "/employees/me",
                    json={
                        "name": "Alice Johnson",
                        "email": "alice.johnson@myperks.dev",
                    },
                    headers=AUTH_HEADER,
                )
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 409

    def test_relinks_existing_employee_by_email(self) -> None:
        existing = _make_employee(clerk_user_id=None)
        session = _make_session([None, existing])

        app.dependency_overrides[get_current_user] = _fake_get_current_user
        try:
            with patch("api.routers.employees.AsyncSessionLocal", return_value=session):
                response = client.post(
                    "/employees/me",
                    json={
                        "name": "Alice Johnson",
                        "email": "alice.johnson@myperks.dev",
                    },
                    headers=AUTH_HEADER,
                )
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 201
        data = response.json()
        assert data["clerk_user_id"] == CLERK_USER_ID
        assert data["role"] == "employee"
        assert data["joined_date"] == "2022-03-01"
        assert data["benefits_year_reset"] == "2027-01-01"

    def test_does_not_relink_email_owned_by_another_account(self) -> None:
        # Email matches a row already linked to a DIFFERENT Clerk user, the
        # link must not be overwritten (no hijack), and nothing is committed.
        other = _make_employee(clerk_user_id="clerk_user_999")
        session = _make_session([None, other])

        app.dependency_overrides[get_current_user] = _fake_get_current_user
        try:
            with patch("api.routers.employees.AsyncSessionLocal", return_value=session):
                response = client.post(
                    "/employees/me",
                    json={
                        "name": "Alice Johnson",
                        "email": "alice.johnson@myperks.dev",
                    },
                    headers=AUTH_HEADER,
                )
        finally:
            app.dependency_overrides.clear()

        assert response.status_code == 409
        session.commit.assert_not_awaited()
