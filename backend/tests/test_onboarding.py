from collections.abc import AsyncGenerator, Callable
from unittest.mock import AsyncMock, MagicMock

from fastapi.testclient import TestClient

from api.auth import get_current_user
from db.session import get_session
from main import app

client = TestClient(app)

# ── Constants ─────────────────────────────────────────────────────────────────

MOCK_CLERK_USER_ID = "clerk_user_test_999"


# ── Override factories ────────────────────────────────────────────────────────


def override_auth() -> str:
    return MOCK_CLERK_USER_ID


def make_db_override(
    mock_session: AsyncMock,
) -> Callable[[], AsyncGenerator[AsyncMock, None]]:
    async def override() -> AsyncGenerator[AsyncMock, None]:
        yield mock_session

    return override


def auth_header() -> dict[str, str]:
    return {"Authorization": "Bearer fake.jwt.token"}


def make_scalar_result(row: MagicMock | None) -> MagicMock:
    """Creates a mock result where .scalars().first() returns row."""
    result = MagicMock()
    result.scalars.return_value.first.return_value = row
    return result


def make_mock_employee() -> MagicMock:
    employee = MagicMock()
    employee.id = 42
    employee.clerk_user_id = MOCK_CLERK_USER_ID
    employee.name = "Alice Test"
    employee.email = "alice@example.com"
    employee.department = "Engineering"
    return employee


# ── GET /me ───────────────────────────────────────────────────────────────────


def test_get_me_returns_employee() -> None:
    """GET /me returns the employee record when it exists."""
    mock_session = AsyncMock()
    mock_session.execute = AsyncMock(
        return_value=make_scalar_result(make_mock_employee())
    )

    app.dependency_overrides[get_current_user] = override_auth
    app.dependency_overrides[get_session] = make_db_override(mock_session)

    try:
        response = client.get("/me", headers=auth_header())
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    data = response.json()
    assert data["clerk_user_id"] == MOCK_CLERK_USER_ID
    assert data["name"] == "Alice Test"
    assert data["email"] == "alice@example.com"
    assert data["department"] == "Engineering"


def test_get_me_returns_404_when_no_employee() -> None:
    """GET /me returns 404 when no Employee row exists for the Clerk user."""
    mock_session = AsyncMock()
    mock_session.execute = AsyncMock(return_value=make_scalar_result(None))

    app.dependency_overrides[get_current_user] = override_auth
    app.dependency_overrides[get_session] = make_db_override(mock_session)

    try:
        response = client.get("/me", headers=auth_header())
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404


def test_get_me_unauthenticated() -> None:
    """GET /me returns 401 with no token."""
    response = client.get("/me")
    assert response.status_code == 401


# ── POST /me/onboard ──────────────────────────────────────────────────────────


ONBOARD_BODY = {
    "name": "Alice Test",
    "email": "alice@example.com",
    "department": "Engineering",
}


def test_onboard_creates_employee() -> None:
    """POST /me/onboard creates a new Employee row and returns 201."""
    mock_session = AsyncMock()
    # First execute: SELECT returns nothing (employee doesn't exist yet)
    mock_session.execute = AsyncMock(return_value=make_scalar_result(None))
    mock_session.add = MagicMock()
    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock(side_effect=lambda emp: setattr(emp, "id", 42))

    app.dependency_overrides[get_current_user] = override_auth
    app.dependency_overrides[get_session] = make_db_override(mock_session)

    try:
        response = client.post("/me/onboard", json=ONBOARD_BODY, headers=auth_header())
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    data = response.json()
    assert data["clerk_user_id"] == MOCK_CLERK_USER_ID
    assert data["name"] == "Alice Test"
    assert data["email"] == "alice@example.com"
    assert data["department"] == "Engineering"
    mock_session.add.assert_called_once()
    mock_session.commit.assert_awaited_once()


def test_onboard_returns_409_when_employee_exists() -> None:
    """POST /me/onboard returns 409 if the Employee row already exists."""
    mock_session = AsyncMock()
    mock_session.execute = AsyncMock(
        return_value=make_scalar_result(make_mock_employee())
    )

    app.dependency_overrides[get_current_user] = override_auth
    app.dependency_overrides[get_session] = make_db_override(mock_session)

    try:
        response = client.post("/me/onboard", json=ONBOARD_BODY, headers=auth_header())
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 409
    mock_session.add.assert_not_called()


def test_onboard_unauthenticated() -> None:
    """POST /me/onboard returns 401 with no token."""
    response = client.post("/me/onboard", json=ONBOARD_BODY)
    assert response.status_code == 401
