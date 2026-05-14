# AI Sales Teammate Workbench

> A full-stack, AI-native workbench where human reviewers can review, edit, and approve AI-generated sales follow-up emails — built for the Teammates.ai engineering assessment.

---

## Quick Start (Docker — recommended)

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop) installed and running

### 1. Clone & configure

```bash
git clone <repo-url> && cd Teammates.ai
cp .env.example .env
```

Edit `.env` and add your **Groq API key** (free at [console.groq.com](https://console.groq.com)):

```env
GROQ_API_KEY=gsk_your_key_here
```

> **Note**: Set `LLM_PROVIDER=mock` to run without an API key (uses pre-built templates).

### 2. Start everything

```bash
docker compose up --build
```

This starts **5 services**: PostgreSQL, Redis, FastAPI backend, Celery worker, and Next.js frontend.

### 3. Seed the database

```bash
docker compose exec backend python -m seed
```

### 4. Open the app

- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs

### Test Credentials

| Role | Email | Password |
|------|-------|----------|
| Admin | `admin@acmecorp.com` | `admin123` |
| Reviewer | `reviewer@acmecorp.com` | `reviewer123` |
| Admin (Org 2) | `admin@techflowinc.com` | `admin123` |

---

## Local Development (without Docker)

### Prerequisites
- Python 3.11+, Node.js 21+, PostgreSQL 16+, Redis 7+

### Backend

```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # Update DATABASE_URL for your local Postgres
createdb sales_workbench  # Create the database
python -m seed          # Create tables and seed demo data
uvicorn app.main:app --reload --port 8000
```

In a separate terminal (for background jobs):

```bash
cd backend && source venv/bin/activate
celery -A app.workers.celery_app worker --loglevel=info
```

### Frontend

```bash
cd frontend
npm install
echo 'NEXT_PUBLIC_API_URL=http://localhost:8000' > .env.local
npm run dev
```

---

## Architecture

```
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│   Next.js    │──────│   FastAPI     │──────│  PostgreSQL   │
│   Frontend   │ REST │   Backend     │ SQL  │  Database     │
│  (Port 3000) │      │  (Port 8000)  │      │  (Port 5432)  │
└──────────────┘      └──────┬───────┘      └──────────────┘
                             │
                     ┌───────┴───────┐
                     │   Redis       │
                     │  (Port 6379)  │
                     └───────┬───────┘
                             │
                     ┌───────┴───────┐
                     │ Celery Worker │
                     │ (Background)  │
                     └───────────────┘
```

### Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 16, React 19, TypeScript, Tailwind CSS 3 |
| Backend | FastAPI, SQLAlchemy 2 (async), Pydantic 2 |
| Database | PostgreSQL 16 with UUID primary keys |
| Queue | Redis + Celery for async background jobs |
| AI | Groq (Llama 3.3 70B) via OpenAI-compatible SDK |
| Auth | JWT + bcrypt password hashing |

---

## Key Features

- **AI Draft Generation** — Groq-powered follow-up email drafts with structured prompts
- **Human-in-the-Loop Review** — Edit, approve, reject, or regenerate AI drafts
- **Role-Based Access** — Admins see all items; Reviewers see only assigned items
- **Organization Isolation** — Multi-tenant: all queries scoped by `organization_id`
- **Background Job Processing** — Celery tasks for email delivery simulation + CRM sync
- **Real-Time Status Updates** — Polling-based status tracking during processing
- **Comprehensive Audit Trail** — Every action logged with actor, timestamp, and metadata
- **Admin Dashboard** — Pipeline overview with stats cards and status bar chart

---

## Security

| Control | Implementation |
|---------|---------------|
| Authentication | JWT tokens (30-min expiry), bcrypt password hashing |
| Authorization | RBAC (Admin / Reviewer) enforced at service layer |
| Tenant Isolation | All DB queries include `organization_id` WHERE clause |
| IDOR Prevention | Cross-org access returns 404 (not 403) to prevent enumeration |
| Rate Limiting | Login: 5/min, Regenerate: 10/min, Default: 60/min |
| Error Handling | Global exception handler — no stack traces leaked to client |
| API Docs | Swagger/ReDoc disabled in production mode |
| Secrets | All secrets via env vars, `.env` files gitignored |

---

## Project Structure

```
Teammates.ai/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # Route handlers (auth, work_items, audit, admin)
│   │   ├── core/            # Security, exceptions
│   │   ├── db/              # SQLAlchemy session, base
│   │   ├── models/          # ORM models (org, user, work_item, audit, job)
│   │   ├── repositories/    # Data access layer
│   │   ├── schemas/         # Pydantic request/response models
│   │   ├── services/        # Business logic (work_item, auth, llm)
│   │   ├── workers/         # Celery tasks
│   │   ├── config.py        # Settings from env vars
│   │   └── main.py          # FastAPI app entry point
│   ├── seed.py              # Database seeder
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/             # Next.js pages (login, dashboard, review, audit, admin)
│   │   ├── components/      # Reusable UI components
│   │   ├── lib/             # API client, auth context, utils
│   │   └── types/           # TypeScript interfaces
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml
├── .env.example             # Template for secrets
└── README.md
```

---

## Design Decisions

| Decision | Rationale |
|----------|-----------|
| **Polling over WebSockets** | Browser EventSource can't send Auth headers; polling (2s) with JWT is simpler and more reliable |
| **Groq over OpenAI** | 10x faster inference, free tier, same OpenAI SDK compatibility |
| **Provider pattern for LLM** | Abstract base class lets us swap mock ↔ Groq ↔ OpenAI via single env var |
| **UUID primary keys** | No sequential ID enumeration attacks; safe for multi-tenant |
| **404 for IDOR** | Cross-org requests return "not found" instead of "forbidden" to prevent information leakage |
| **Tailwind v3** | Stable CSS generation with Turbopack; v4 had utility generation issues |
| **Celery + Redis** | Battle-tested async task queue; job retries and failure handling built in |

---

## Stopping

```bash
docker compose down        # Stop containers
docker compose down -v     # Stop + delete data
```

---

## Deliverables Links

- **Live Deployed App**: `[Insert your live URL here]`
- **Loom Walkthrough**: `[Insert your Loom link here]`

---

## AI Usage

**Tools Used:** Gemini 3.1 Pro (via Antigravity agent), GitHub Copilot.

**Where AI Helped Most:**
- Generating the initial boilerplate for FastAPI, SQLAlchemy models, and the Next.js Tailwind UI.
- Structuring the Celery background worker setup securely inside Docker.
- Creating realistic, contextual dummy data in `seed.py`.

**Manual Review & Rewrites:**
- I manually redesigned the UI state machine to avoid issues with SSE auth headers, choosing a robust polling architecture instead.
- The `regenerating` status originally caused PostgreSQL Enum transaction issues because of upper/lower case mismatches. I manually rewrote the `regenerate_draft` logic to execute inline without saving the intermediate state, ensuring robustness.
- Manually audited all API endpoints to ensure they used the `organization_id` constraint to strictly enforce tenant isolation.

**Rejected AI Output:**
- An AI suggestion tried to use Next.js Server Actions with direct database queries. I rejected this to maintain a strict separation of concerns, routing everything through the secure FastAPI backend layer.

**Validation:**
- Relied heavily on end-to-end browser subagent testing, checking the UI manually, and writing a seed script that tests different state transitions and roles.

---

## Known Limitations

- **Polling Overhead**: Currently using 2s polling for real-time updates. While functional, at massive scale this would cause high server load compared to WebSockets.
- **Single Database**: Celery and FastAPI share the same database. Celery uses a sync engine, FastAPI uses asyncpg. Under extreme load, managing connection pools across both paradigms requires careful PgBouncer configuration.
- **LLM Latency**: When a user clicks "Regenerate Draft", the UI blocks for a few seconds waiting for the inline Groq API response.

---

## What I Would Improve With One More Week

1. **WebSockets for Real-Time UX**: I would move from polling to WebSockets (using `socket.io` or FastAPI WebSockets), passing a short-lived token in the URL or payload for authentication.
2. **Smarter Retries & Dead Letter Queue**: For the Celery workers, I would implement exponential backoff for failed CRM syncs and a Dead Letter Queue for failed email dispatches so admins can investigate.
3. **Comprehensive Test Suite**: Add a full `pytest` suite for the backend and Playwright E2E tests for the frontend to ensure no regressions during refactors.
4. **Caching Layer**: Add Redis caching for the `/api/v1/work-items` dashboard endpoint, invalidating the cache when a work item status changes.
5. **AI Evaluation**: Add an LLM evaluation framework (e.g., using a smaller judge model) to ensure regenerated drafts actually meet quality thresholds before displaying them to the user.
