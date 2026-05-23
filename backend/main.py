from typing import cast

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from api.upload import router as upload_router
from api.chat import router as chat_router
from db.models import Employee
from db.session import AsyncSessionLocal
from settings import settings

app = FastAPI(title="MyPerks API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_headers=["*"],
    allow_methods=["*"],
    allow_origins=settings.allowed_origins,
)

app.include_router(upload_router)
app.include_router(chat_router)


@app.get("/")
async def welcome() -> dict[str, str]:
    return {"message": "Welcome to MyPerks API"}


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


# ── TEMP: remove before production ───────────────────────────────────────────
@app.get("/test/employees")
async def test_employees() -> list[dict[str, str | int | None]]:
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Employee))
        employees = result.scalars().all()
        return [
            {
                "id": cast(int, e.id),
                "name": cast(str, e.name),
                "email": cast(str, e.email),
                "department": cast(str | None, e.department),
                "clerk_user_id": cast(str, e.clerk_user_id),
            }
            for e in employees
        ]


# ── END TEMP ──────────────────────────────────────────────────────────────────
