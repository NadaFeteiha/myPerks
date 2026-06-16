# MyPerks

> AI-Powered Employee Benefits & HR Assistant  
> Stack: Next.js 16 · FastAPI · LangGraph · RAG · PostgreSQL + pgvector · Ollama

---

## What it does

Employees ask questions in plain language and get instant, accurate answers grounded in actual HR policy documents and their own live data. HR admins upload policy PDFs, review AI-extracted policy data, and apply it to departments in one click.

**Employee features**
- Chat assistant answers benefits and policy questions from real uploaded PDFs (RAG)
- Live vacation / sick / PTO balance from PostgreSQL
- Generates HR request emails in one click
- Benefits dashboard with usage charts and request history

**HR Admin features**
- Upload PDF policy documents per department
- AI extracts structured policy data (vacation days, sick days, PTO, notes)
- Review and edit extracted values before applying
- Approve → automatically updates all employees in the department
- Document list with per-document extraction status badges

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  Next.js 16 (App Router)        FastAPI (Python)                │
│  ───────────────────────        ─────────────────               │
│  Clerk auth                     LangGraph agent                 │
│  Employee dashboard   ◄──────►  Router → RAG + DB nodes        │
│  HR admin panel                 Synthesizer (LLM)               │
│  Chat (SSE stream)              pgvector similarity search      │
│  Upload (UploadThing)           Document extraction pipeline    │
│                                 PostgreSQL (all data)           │
└─────────────────────────────────────────────────────────────────┘
```

**LangGraph agent — 2 LLM calls per turn:**
1. Router node — classifies intent → `["rag", "db", "email"]`
2. RAG + DB nodes run in parallel (pure vector math + SQL, no LLM)
3. Synthesizer node — writes grounded answer from gathered context

**Document extraction pipeline:**
1. HR uploads PDF → chunked + embedded by `nomic-embed-text` via Ollama
2. HR clicks "Extract Policy" → `llama3.2` reads chunks, returns structured JSON
3. HR reviews / edits values in the UI → clicks Approve
4. Backend writes `VacationBalance` rows for every employee in the department

---

## Monorepo structure

```
myperks/
├── frontend/                  Next.js 16 app
│   └── src/
│       ├── app/(app)/admin/   HR dashboard, documents, review pages
│       ├── app/(app)/         Employee dashboard, assistant, history
│       ├── components/        Upload, chat, dashboard, layout components
│       └── lib/               API client, auth helpers, formatters
├── backend/                   FastAPI + LangGraph
│   ├── api/                   Endpoints (chat, upload, admin, employees)
│   ├── agent/                 LangGraph graph, nodes, state
│   ├── rag/                   Ingest, search, extract pipelines
│   ├── db/                    SQLAlchemy models, session, seed
│   └── migrations/            Alembic migration versions
└── docs/                      Architecture decisions
```

---

## Quick start

### Prerequisites

- Node 20+
- Python 3.12+
- PostgreSQL 17 with pgvector extension
- [Ollama](https://ollama.com) (for local AI — free, no API key needed)

### 1. Clone and install

```bash
git clone <repo>

# Frontend
cd frontend && npm install

# Backend
cd ../backend
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install langchain-ollama    # Ollama integration
```

### 2. Pull Ollama models

```bash
ollama pull nomic-embed-text    # embeddings (768 dims)
ollama pull llama3.2            # policy extraction LLM
```

### 3. Set up the database

```bash
# Enable pgvector (run once in psql)
psql -U postgres -c "CREATE EXTENSION IF NOT EXISTS vector;"

# Run all migrations
cd backend
alembic upgrade head

# Seed development data (optional)
python -m db.seed
```

### 4. Configure environment

Copy and fill in your values:

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local
```

Key backend variables:

```env
DATABASE_URL=postgresql+asyncpg://...
CLERK_ISSUER=https://...
CLERK_JWKS_URL=https://.../.well-known/jwks.json

# Pick one AI backend:
AI_BACKEND=ollama        # local Ollama — no API key needed (default)
# AI_BACKEND=openai      # OpenAI API — add OPENAI_API_KEY below

# Required only when AI_BACKEND=openai:
# OPENAI_API_KEY=sk-...
```

### 5. Run

```bash
# Terminal 1 — Ollama server
ollama serve

# Terminal 2 — backend
cd backend
uvicorn main:app --reload --port 8000

# Terminal 3 — frontend
cd frontend
npm run dev
```

- Frontend: http://localhost:3000
- API docs: http://localhost:8000/docs

---

## AI backend modes

Set one line in `backend/.env` to switch:

```env
AI_BACKEND=ollama    # default — local, no API key needed
AI_BACKEND=openai    # cloud — requires OPENAI_API_KEY
```

| Mode | Embeddings | LLM | Cost |
|------|------------|-----|------|
| `ollama` | `nomic-embed-text` (768 dims, local) | `llama3.2` (local) | Free |
| `openai` | `text-embedding-3-small` (1536 dims) | `gpt-4o-mini` | ~$0.002 / 1k tokens |

> **Switching between `ollama` and `openai` requires re-uploading documents** — the vector dimensions differ (768 vs 1536) so existing embeddings are incompatible.

---

## Tech stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 16 (App Router), Tailwind CSS, Recharts |
| Auth | Clerk |
| File upload | UploadThing |
| Streaming | Server-Sent Events (SSE) |
| Backend | FastAPI, Python 3.13 |
| AI orchestration | LangGraph + LangChain |
| LLM (local) | Ollama — llama3.2 |
| LLM (cloud) | OpenAI gpt-4o-mini |
| Embeddings (local) | Ollama — nomic-embed-text (768 dims) |
| Embeddings (cloud) | OpenAI text-embedding-3-small (1536 dims) |
| Vector store | pgvector (PostgreSQL extension) |
| Database | PostgreSQL 17 |
| Migrations | Alembic |

---

## Database schema (key tables)

| Table | Purpose |
|-------|---------|
| `employees` | Users with role (`employee` \| `hr_admin`) and department |
| `documents` | Uploaded PDFs scoped to a department |
| `document_chunks` | PDF text chunks with 768-dim embeddings |
| `document_extractions` | LLM-extracted HR policy data, review status, approved values |
| `vacation_balances` | Per-employee, per-year leave balances (vacation / sick / PTO) |
| `request_histories` | Leave requests with approval status |
| `conversations` + `messages` | Chat history |

---

## HR document review flow

```
Upload PDF
    │
    ▼
ingest_pdf()  ──  chunk text  ──  embed with nomic-embed-text  ──  store in pgvector
    │
    ▼
HR clicks "Review" on the document list
    │
    ▼
POST /admin/documents/{id}/extract
    ├── llama3.2 reads chunks
    └── returns { vacation_days, sick_days, pto_days, notes }
    │
    ▼
HR edits values in the review form
    │
    ▼
POST /admin/documents/{id}/extraction/approve
    └── writes VacationBalance rows for every employee in the department
```
