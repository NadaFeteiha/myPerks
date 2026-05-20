import time
from typing import Any, cast

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from settings import settings

# ── JWKS cache ────────────────────────────────────────────────────────────────

_JWKS_CACHE: dict[str, Any] = {
    "keys": None,
    "fetched_at": 0.0,
}
_CACHE_TTL_SECONDS = 3600

_bearer_scheme = HTTPBearer(auto_error=False)


# ── JWKS fetcher ──────────────────────────────────────────────────────────────


async def _fetch_jwks() -> dict[str, Any]:
    """Fetch Clerk's public JWKS from the configured URL."""
    async with httpx.AsyncClient() as client:
        response = await client.get(settings.clerk_jwks_url, timeout=10)
        response.raise_for_status()
        data: dict[str, Any] = response.json()
        return data


async def get_jwks(force_refresh: bool = False) -> dict[str, Any]:
    """
    Return cached JWKS keys, refreshing if stale or forced.
    force_refresh=True handles Clerk key rotation.
    """
    now = time.monotonic()
    cache_expired = (now - _JWKS_CACHE["fetched_at"]) > _CACHE_TTL_SECONDS

    if force_refresh or cache_expired or _JWKS_CACHE["keys"] is None:
        _JWKS_CACHE["keys"] = await _fetch_jwks()
        _JWKS_CACHE["fetched_at"] = now

    return cast(dict[str, Any], _JWKS_CACHE["keys"])


# ── FastAPI dependency ────────────────────────────────────────────────────────


def _raise_401(detail: str = "Unauthorized") -> None:
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),  # noqa: B008
) -> str:
    """
    FastAPI dependency — verifies the Clerk JWT and returns clerk_user_id.

    Usage:
        @router.get("/protected")
        async def protected(user_id: str = Depends(get_current_user)):
            ...

    Raises HTTP 401 if:
    - Authorization header is missing
    - Token is malformed, expired, or has an invalid signature
    - Issuer does not match settings.clerk_issuer
    """
    if credentials is None:
        _raise_401("Missing authorization header")

    assert credentials is not None  # narrows type for mypy
    token = credentials.credentials

    jwks = await get_jwks()

    try:
        payload = jwt.decode(
            token,
            jwks,
            algorithms=["RS256"],
            issuer=settings.clerk_issuer,
            options={"verify_aud": False},
        )
    except JWTError:
        jwks = await get_jwks(force_refresh=True)
        try:
            payload = jwt.decode(
                token,
                jwks,
                algorithms=["RS256"],
                issuer=settings.clerk_issuer,
                options={"verify_aud": False},
            )
        except JWTError:
            _raise_401("Invalid or expired token")

    clerk_user_id: str | None = payload.get("sub")
    if not clerk_user_id:
        _raise_401("Token missing subject claim")

    return str(clerk_user_id)
