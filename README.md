# MyPerks

> AI-Powered Employee Benefits & HR Assistant  
> Stack: Next.js 16 · FastAPI · LangGraph · RAG · PostgreSQL + pgvector · OpenAI

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
1. HR uploads PDF → chunked + embedded by OpenAI `text-embedding-3-small`
2. HR clicks "Extract Policy" → `gpt-4o-mini` reads chunks, returns structured JSON
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
- An [OpenAI API key](https://platform.openai.com/api-keys)

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
```

### 2. Set up the database

```bash
# Enable pgvector (run once in psql)
psql -U postgres -c "CREATE EXTENSION IF NOT EXISTS vector;"

# Run all migrations
cd backend
alembic upgrade head

# Seed development data (optional)
python -m db.seed
```

### 3. Configure environment

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
OPENAI_API_KEY=sk-...
```

### 4. Run

```bash
# Terminal 1 — backend
cd backend
uvicorn main:app --reload --port 8000

# Terminal 2 — frontend
cd frontend
npm run dev
```

- Frontend: http://localhost:3000
- API docs: http://localhost:8000/docs

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
| LLM | OpenAI gpt-4o / gpt-4o-mini |
| Embeddings | OpenAI text-embedding-3-small (1536 dims) |
| Vector store | pgvector (PostgreSQL extension) |
| Database | PostgreSQL 17 |
| Migrations | Alembic |

---

## Database schema (key tables)

| Table | Purpose |
|-------|---------|
| `employees` | Users with role (`employee` \| `hr_admin`) and department |
| `documents` | Uploaded PDFs scoped to a department |
| `document_chunks` | PDF text chunks with 1536-dim embeddings |
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
ingest_pdf()  ──  chunk text  ──  embed with text-embedding-3-small  ──  store in pgvector
    │
    ▼
HR clicks "Review" on the document list
    │
    ▼
POST /admin/documents/{id}/extract
    ├── gpt-4o-mini reads chunks
    └── returns { vacation_days, sick_days, pto_days, notes }
    │
    ▼
HR edits values in the review form
    │
    ▼
POST /admin/documents/{id}/extraction/approve
    └── writes VacationBalance rows for every employee in the department
```
