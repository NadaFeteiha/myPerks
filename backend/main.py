from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from settings import settings

app = FastAPI(title="MyPerks API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_headers=["*"],
    allow_methods=["*"],
    allow_origins=settings.allowed_origins,
)


@app.get("/")
async def welcome() -> dict[str, str]:
    return {"message": "Welcome to MyPerks API"}


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
