import logging
import time
from typing import Any, cast

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Employee
from db.session import get_session
from settings import settings

logger = logging.getLogger(__name__)

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


# ── Shared helpers ────────────────────────────────────────────────────────────


def _raise_401(detail: str = "Unauthorized") -> None:
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


async def _decode_token(token: str) -> dict[str, Any]:
    """
    Verify a Clerk JWT and return the decoded payload.
    Retries once with a forced JWKS refresh to handle key rotation.

    Raises HTTP 401 if the token is invalid, expired, or has a bad signature.
    """
    jwks = await get_jwks()

    try:
        payload: dict[str, Any] = jwt.decode(
            token,
            jwks,
            algorithms=["RS256"],
            issuer=settings.clerk_issuer,
            options={"verify_aud": False},
        )
    except JWTError as first_err:
        logger.warning("JWT decode failed (first attempt): %s", first_err)
        logger.warning(
            "clerk_issuer=%r  clerk_jwks_url=%r",
            settings.clerk_issuer,
            settings.clerk_jwks_url,
        )
        jwks = await get_jwks(force_refresh=True)
        try:
            payload = jwt.decode(
                token,
                jwks,
                algorithms=["RS256"],
                issuer=settings.clerk_issuer,
                options={"verify_aud": False},
            )
        except JWTError as second_err:
            logger.error("JWT decode failed (after JWKS refresh): %s", second_err)
            _raise_401("Invalid or expired token")
            raise  # unreachable — satisfies mypy that payload is always bound

    return payload


# ── FastAPI dependencies ──────────────────────────────────────────────────────


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),  # noqa: B008
) -> str:
    """
    FastAPI dependency — verifies the Clerk JWT and returns clerk_user_id.

    Usage:
        @router.get("/protected")
        async def endpoint(user_id: str = Depends(get_current_user)):
            ...

    Raises HTTP 401 if:
    - Authorization header is missing
    - Token is malformed, expired, or has an invalid signature
    - Issuer does not match settings.clerk_issuer
    """
    if credentials is None:
        _raise_401("Missing authorization header")

    assert credentials is not None  # narrows type for mypy
    payload = await _decode_token(credentials.credentials)

    clerk_user_id: str | None = payload.get("sub")
    if not clerk_user_id:
        _raise_401("Token missing subject claim")

    return str(clerk_user_id)


async def get_current_user_payload(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),  # noqa: B008
) -> dict[str, Any]:
    """
    FastAPI dependency — verifies the Clerk JWT and returns the full decoded payload.

    Use this instead of get_current_user when you need claims beyond sub,
    e.g. email and full_name for the onboarding endpoint.

    The payload always contains:
      sub       — Clerk user ID (always present after verification)
      email     — from the myperks-dev JWT template (may be absent if misconfigured)
      full_name — from the myperks-dev JWT template (may be absent if misconfigured)

    Raises HTTP 401 if:
    - Authorization header is missing
    - Token is malformed, expired, or has an invalid signature
    - Issuer does not match settings.clerk_issuer
    """
    if credentials is None:
        _raise_401("Missing authorization header")

    assert credentials is not None  # narrows type for mypy
    payload = await _decode_token(credentials.credentials)

    if not payload.get("sub"):
        _raise_401("Token missing subject claim")

    return payload


async def require_admin(
    clerk_user_id: str = Depends(get_current_user),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> Employee:
    """
    FastAPI dependency — verifies the authenticated user is an HR admin.

    Builds on get_current_user, then loads the Employee row and checks
    role == "hr_admin". Returns the full Employee object so downstream
    handlers don't need to re-query.

    Usage:
        @router.patch("/admin/...")
        async def endpoint(admin: Employee = Depends(require_admin)):
            ...

    Raises:
        HTTP 401 if the bearer token is missing/invalid (via get_current_user)
        HTTP 403 if no Employee row matches, or the role is not "hr_admin"
    """
    employee = await session.scalar(
        select(Employee).where(Employee.clerk_user_id == clerk_user_id)
    )
    if employee is None or employee.role != "hr_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="HR admin access required",
        )
    return employee
