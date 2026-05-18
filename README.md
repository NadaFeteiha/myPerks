# MyPerks

> AI-Powered Employee Benefits & HR Assistant  
> Stack: Next.js 14 · FastAPI · LangGraph · RAG · PostgreSQL + pgvector

---

## What it does

Employees ask questions in plain language and get instant, accurate answers grounded in actual policy documents and their own live HR data.

- Answers benefits and policy questions from real uploaded PDF documents (RAG)
- Shows live vacation balance from PostgreSQL
- Generates ready-to-send HR request emails in one click
- Benefits dashboard with usage charts
- Full request history

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Next.js 14 (Vercel)          FastAPI (Render)           │
│  ─────────────────            ──────────────────         │
│  Clerk auth                   LangGraph agent            │
│  Dashboard (REST)    ◄──────► Router → RAG + DB nodes    │
│  Chat (SSE stream)            Synthesizer (Claude)       │
│  Upload (UploadThing)         pgvector similarity search │
│                               PostgreSQL (all data)      │
└─────────────────────────────────────────────────────────┘
```

**Single LangGraph agent — 2 LLM calls per turn:**
1. Router node: classifies intent → `["rag", "db", "email"]`
2. RAG + DB nodes run in parallel (zero LLM calls — pure vector math + SQL)
3. Synthesizer node: writes grounded answer from gathered data

---

## Monorepo structure

```
myperks/
├── frontend/          Next.js 14 app (Vercel)
├── backend/           FastAPI + LangGraph (Render)
├── docs/decisions/    Architecture Decision Records
└── .github/workflows/ CI for both
```

---

## Quick start

### Prerequisites

- Node 24+
- Python 3.12+
- PostgreSQL 17 with pgvector extension

### 1. Clone and install

```bash
git clone <repo>
cp .env.example .env   # fill in your values

# Frontend
cd frontend
npm install

# Backend
cd ../backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Set up the database

```bash
# Enable pgvector (run once in psql)
psql -U postgres -c "CREATE EXTENSION IF NOT EXISTS vector;"

# Run migrations
cd backend
alembic upgrade head

# Seed development data (optional)
python -m db.seed
```

### 3. Run

```bash
# Terminal 1 — backend
cd backend
uvicorn main:app --reload --port 8000

# Terminal 2 — frontend
cd frontend
npm run dev
```

Frontend: http://localhost:3000  
Backend API docs: http://localhost:8000/docs

---

## Tech stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14 (App Router), Tailwind CSS, shadcn/ui, Recharts |
| Auth | Clerk |
| Upload | UploadThing |
| Streaming | Vercel AI SDK + SSE |
| Backend | FastAPI, Python 3.12 |
| AI orchestration | LangGraph + LangChain |
| LLM | Claude (claude-sonnet-4-6) via Anthropic API |
| Embeddings | OpenAI text-embedding-3-small |
| Vector store | pgvector (PostgreSQL extension) |
| Database | PostgreSQL 17 |
| Migrations | Alembic |
| Reminders | APScheduler |
| Frontend deploy | Vercel |
| Backend deploy | Render |
