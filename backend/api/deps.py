import httpx
from fastapi import Header, HTTPException
from jose import JWTError, jwt
from sqlalchemy import select

from db.models import Employee
from db.session import AsyncSessionLocal
from settings import settings

_jwks_cache: dict | None = None


async def _get_jwks() -> dict:
    global _jwks_cache
    if _jwks_cache is None:
        async with httpx.AsyncClient() as client:
            resp = await client.get(settings.clerk_jwks_url, timeout=10)
            resp.raise_for_status()
            _jwks_cache = resp.json()
    assert _jwks_cache is not None
    return _jwks_cache


async def get_current_employee(authorization: str = Header(...)) -> Employee:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization[7:]

    try:
        jwks = await _get_jwks()
        payload = jwt.decode(token, jwks, algorithms=["RS256"])
        clerk_user_id: str = payload["sub"]
    except (JWTError, KeyError, httpx.HTTPError):
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    async with AsyncSessionLocal() as db:
        employee = (
            await db.execute(
                select(Employee).where(Employee.clerk_user_id == clerk_user_id)
            )
        ).scalar_one_or_none()

    if employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")

    return employee
