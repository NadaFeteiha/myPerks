from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy import select

from settings import settings
from db.models import Employee

app = FastAPI(title="MyPerks API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_headers=["*"],
    allow_methods=["*"],
    allow_origins=settings.allowed_origins,
)

engine = create_async_engine(settings.database_url, echo=False)
AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


@app.get("/")
async def welcome() -> dict[str, str]:
    return {"message": "Welcome to MyPerks API"}


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


# ── TEMP: test route — remove before production ───────────────────────────────
@app.get("/test/employees")
async def test_employees() -> list[dict]:
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Employee))
        employees = result.scalars().all()
        return [
            {
                "id": e.id,
                "name": e.name,
                "email": e.email,
                "department": e.department,
                "clerk_user_id": e.clerk_user_id,
            }
            for e in employees
        ]
# ── END TEMP ──────────────────────────────────────────────────────────────────