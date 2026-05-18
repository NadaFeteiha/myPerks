# ADR 0001 — Monorepo + FastAPI owns the database

**Status:** Accepted  
**Date:** 2026-05-18

## Context

- Team of 4, 10-day sprint
- Frontend: Next.js 14 (Person 4)
- Backend: FastAPI + LangGraph (Persons 1–3)
- Database: PostgreSQL + pgvector

## Decision

1. **Monorepo**: `frontend/` and `backend/` live in the same GitHub repository with one CI workflow.
2. **FastAPI + Alembic owns all migrations**: SQLAlchemy defines all models; Alembic runs migrations. The Next.js frontend has no Prisma and makes no direct DB connections.
3. **Single PostgreSQL database** with pgvector extension: one DB for both structured HR data and vector embeddings. No separate vector database needed.

## Consequences

- Person 3 is the single owner of the DB schema — no ORM conflicts
- Person 4 builds a pure UI that calls FastAPI REST endpoints
- Clerk JWT verification happens in FastAPI (`api/auth.py`) — Next.js just passes the token
- `alembic upgrade head` runs as part of both local setup and Render deploy
