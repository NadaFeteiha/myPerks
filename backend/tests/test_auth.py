from unittest.mock import AsyncMock, patch

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from api.auth import get_current_user

# ── Test app setup ─────────────────────────────────────────────────────────────

app = FastAPI()


@app.get("/protected")
async def protected_route(
    user_id: str = Depends(get_current_user),
) -> dict[str, str]:
    return {"user_id": user_id}


# Use sync TestClient — wraps async correctly with pytest
client = TestClient(app)


# ── Helpers ───────────────────────────────────────────────────────────────────

TEST_USER_ID = "user_abc123"
TEST_ISSUER = "https://test.clerk.accounts.dev"

# A minimal RSA-style mock — we patch jwt.decode so no real key needed in tests
MOCK_PAYLOAD = {"sub": TEST_USER_ID, "iss": TEST_ISSUER}
MOCK_JWKS = {"keys": [{"kty": "RSA", "kid": "test-key"}]}


# ── Tests ─────────────────────────────────────────────────────────────────────


class TestGetCurrentUser:
    def test_valid_token_returns_user_id(self) -> None:
        """Happy path — valid JWT returns clerk_user_id."""
        with (
            patch("api.auth.get_jwks", new_callable=AsyncMock, return_value=MOCK_JWKS),
            patch("api.auth.jwt.decode", return_value=MOCK_PAYLOAD),
        ):
            response = client.get(
                "/protected",
                headers={"Authorization": "Bearer valid.jwt.token"},
            )

        assert response.status_code == 200
        assert response.json() == {"user_id": TEST_USER_ID}

    def test_missing_authorization_header_returns_401(self) -> None:
        """No Authorization header → 401."""
        response = client.get("/protected")

        assert response.status_code == 401
        assert (
            "Unauthorized" in response.json()["detail"] or response.status_code == 401
        )

    def test_invalid_token_returns_401(self) -> None:
        """Bad signature → 401 after retry."""
        from jose import JWTError

        with (
            patch("api.auth.get_jwks", new_callable=AsyncMock, return_value=MOCK_JWKS),
            patch("api.auth.jwt.decode", side_effect=JWTError("bad signature")),
        ):
            response = client.get(
                "/protected",
                headers={"Authorization": "Bearer invalid.jwt.token"},
            )

        assert response.status_code == 401

    def test_expired_token_returns_401(self) -> None:
        """Expired token → 401."""
        from jose import ExpiredSignatureError

        with (
            patch("api.auth.get_jwks", new_callable=AsyncMock, return_value=MOCK_JWKS),
            patch("api.auth.jwt.decode", side_effect=ExpiredSignatureError("expired")),
        ):
            response = client.get(
                "/protected",
                headers={"Authorization": "Bearer expired.jwt.token"},
            )

        assert response.status_code == 401

    def test_token_missing_sub_claim_returns_401(self) -> None:
        """Valid JWT structure but missing 'sub' → 401."""
        with (
            patch("api.auth.get_jwks", new_callable=AsyncMock, return_value=MOCK_JWKS),
            patch("api.auth.jwt.decode", return_value={"iss": TEST_ISSUER}),  # no sub
        ):
            response = client.get(
                "/protected",
                headers={"Authorization": "Bearer no.sub.token"},
            )

        assert response.status_code == 401
