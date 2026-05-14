# AI Sales Teammate Workbench — Full Technical Documentation

> Comprehensive technical documentation covering architecture, data flows, API contracts, security model, and design rationale.

---

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Backend Deep Dive](#backend-deep-dive)
3. [Frontend Deep Dive](#frontend-deep-dive)
4. [Authentication & Security](#authentication--security)
5. [AI Integration](#ai-integration)
6. [Background Jobs](#background-jobs)
7. [Database Schema](#database-schema)
8. [API Reference](#api-reference)
9. [State Machine](#state-machine)
10. [File Structure](#file-structure)

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        USER BROWSER                         │
│  Next.js 16 (React 19 + TypeScript + Tailwind CSS 3)       │
│  ┌─────────┐ ┌───────────┐ ┌──────────┐ ┌──────────────┐  │
│  │  Login   │ │Work Queue │ │  Review  │ │ Admin Dash   │  │
│  │  Page    │ │ Dashboard │ │  Page    │ │ + Audit Log  │  │
│  └────┬─────┘ └────┬──────┘ └────┬─────┘ └──────┬───────┘  │
│       │             │             │               │          │
│       └─────────────┴──────┬──────┴───────────────┘          │
│                            │ REST API (JWT Bearer Token)     │
└────────────────────────────┼─────────────────────────────────┘
                             │
┌────────────────────────────┼─────────────────────────────────┐
│  FASTAPI BACKEND           │  Port 8000                      │
│  ┌─────────────────────────▼──────────────────────────────┐  │
│  │  API Layer (app/api/v1/)                               │  │
│  │  auth.py | work_items.py | audit_logs.py | admin.py    │  │
│  └─────────────────────────┬──────────────────────────────┘  │
│  ┌─────────────────────────▼──────────────────────────────┐  │
│  │  Service Layer (app/services/)                         │  │
│  │  auth_service.py | work_item_service.py | llm_service  │  │
│  └─────────────────────────┬──────────────────────────────┘  │
│  ┌─────────────────────────▼──────────────────────────────┐  │
│  │  Repository Layer (app/repositories/)                  │  │
│  │  user_repo | work_item_repo | audit_repo | job_repo    │  │
│  └─────────────────────────┬──────────────────────────────┘  │
│  ┌─────────────────────────▼──────────────────────────────┐  │
│  │  SQLAlchemy ORM Models (app/models/)                   │  │
│  │  Organization | User | LeadWorkItem | AuditLog | Job   │  │
│  └─────────────────────────┬──────────────────────────────┘  │
│                            │                                  │
└────────────────────────────┼──────────────────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
   ┌────▼─────┐     ┌───────▼──────┐    ┌───────▼──────┐
   │PostgreSQL │     │    Redis     │    │Celery Worker │
   │  16       │     │  7-alpine   │    │(Background)  │
   │Port 5432  │     │ Port 6379   │    │              │
   └───────────┘     └─────────────┘    └──────────────┘
```

### Layer Responsibilities

| Layer | Role | Key Pattern |
|-------|------|-------------|
| API Routes | HTTP handling, request validation | Thin — delegates to Service |
| Services | Business logic, state transitions | Core rules, authorization checks |
| Repositories | Database queries | Org-scoped, no business logic |
| Models | ORM definitions | UUID PKs, enums for status/roles |
| Workers | Background processing | Sync DB (Celery can't do async) |

---

## Backend Deep Dive

### Entry Point: `app/main.py`
- Creates FastAPI app with lifespan events
- Registers CORS, rate limiter, global exception handler
- Swagger/ReDoc disabled when `DEBUG=false` (production)

### Config: `app/config.py`
- Pydantic Settings loads from `.env` file
- All secrets via environment variables — never hardcoded
- Supports mock/groq/openai LLM providers

### Auth Flow
```
POST /api/v1/auth/login
  → AuthService.login(email, password)
    → UserRepository.get_by_email(email)
    → verify_password(plain, hashed)
    → create_access_token({sub: user_id, org: org_id})
    → Return {access_token, user}
```

### Work Item Lifecycle
```
1. Seed creates item → status: PENDING_REVIEW
2. Reviewer views → GET /work-items/{id}
3. Optional edit → PUT /work-items/{id} (saves edited_output)
4. Approve → POST /work-items/{id}/approve
   → status: APPROVED → Celery task dispatched
   → Celery: status: PROCESSING → simulates email → status: SENT
5. OR Reject → POST /work-items/{id}/reject → status: REJECTED
6. OR Regenerate → POST /work-items/{id}/regenerate
   → status: REGENERATING → LLM call → status: PENDING_REVIEW
```

---

## Frontend Deep Dive

### Pages

| Route | Component | Description |
|-------|-----------|-------------|
| `/login` | `login/page.tsx` | JWT login with test credential buttons |
| `/dashboard` | `dashboard/page.tsx` | Work queue table with status filters |
| `/dashboard/work-items/[id]` | `work-items/[id]/page.tsx` | Review page: lead context, AI draft, actions |
| `/dashboard/audit` | `audit/page.tsx` | Chronological audit log with metadata tags |
| `/dashboard/admin` | `admin/page.tsx` | Stats cards + pipeline overview bar |

### Components (`src/components/ui/index.tsx`)
- **Button** — variants: primary, secondary, success, danger, ghost
- **Card** — dark themed container
- **StatusBadge** — color-coded status pills
- **Toast** — success/error/info notifications
- **Skeleton** — loading shimmer animation

### Auth Context (`src/lib/auth.tsx`)
- React Context with `user` state
- Reads JWT from `localStorage`
- Auto-redirects to `/login` on 401

### API Client (`src/lib/api.ts`)
- Type-safe fetch wrapper with JWT injection
- Automatic 401 → logout + redirect
- Polling-based status updates (2s interval)

---

## Authentication & Security

### JWT Token Structure
```json
{
  "sub": "user-uuid",
  "org": "organization-uuid",
  "exp": 1718000000
}
```

### RBAC Enforcement
- `get_current_user` — extracts user from JWT (every protected route)
- `require_admin` — decorator that checks `user.role == ADMIN`
- Service layer: Reviewers can only access items where `assigned_reviewer_id == user.id`

### Multi-Tenant Isolation
- Every repository method takes `organization_id` parameter
- Every SQL query includes `WHERE organization_id = :org_id`
- Cross-org access returns 404 (not 403) — prevents enumeration

### Rate Limiting (slowapi)
- Login: 5 requests/minute per IP
- Regenerate: 10 requests/minute per IP
- Default: 60 requests/minute per IP

---

## AI Integration

### Provider Pattern
```python
class LLMProvider(ABC):
    async def generate_follow_up(lead_name, company_name, ...) -> str

class MockLLMProvider(LLMProvider)   # Templates, no API call
class GroqProvider(LLMProvider)      # Groq Cloud (Llama 3.3 70B)
class OpenAIProvider(LLMProvider)    # GPT-4o-mini

def get_llm_provider() -> LLMProvider:
    # Reads LLM_PROVIDER env var → returns correct provider
```

### Why Groq?
- Uses OpenAI-compatible SDK (`openai` package, custom `base_url`)
- 10x faster inference than OpenAI
- Free tier available
- Llama 3.3 70B produces excellent sales emails

### System Prompt
Structured to produce: subject line, personalized body, value props, CTA, plain text format.

---

## Background Jobs

### Celery Task: `process_approved_item`
```
1. Fetch job + work_item from DB (org-scoped)
2. Set status = PROCESSING, create audit log
3. Simulate email sending (configurable delay)
4. Simulate CRM sync, generate CRM record ID
5. Set status = SENT, create audit log with CRM ID
6. On failure: set status = FAILED, log error, retry up to 3x
```

### Why Celery uses Sync DB?
Celery workers run in separate processes and don't support `asyncio`. So we use `sqlalchemy.create_engine` (sync) with `psycopg2` instead of `asyncpg`.

---

## Database Schema

```
┌──────────────┐     ┌──────────────┐     ┌──────────────────┐
│ Organization │────<│     User     │────<│  LeadWorkItem    │
│              │     │              │     │                  │
│ id (UUID PK) │     │ id (UUID PK) │     │ id (UUID PK)     │
│ name         │     │ org_id (FK)  │     │ org_id (FK)      │
│ created_at   │     │ name         │     │ reviewer_id (FK) │
│              │     │ email        │     │ lead_name        │
│              │     │ role (enum)  │     │ company_name     │
│              │     │ password_hash│     │ lead_context     │
│              │     │              │     │ original_input   │
│              │     │              │     │ ai_output        │
└──────────────┘     └──────────────┘     │ edited_output    │
                                          │ status (enum)    │
                                          │ reviewer_note    │
                                          └───────┬──────────┘
                                                  │
                     ┌──────────────┐     ┌───────▼──────────┐
                     │BackgroundJob │     │   AuditLog       │
                     │              │     │                  │
                     │ id (UUID PK) │     │ id (UUID PK)     │
                     │ org_id (FK)  │     │ org_id (FK)      │
                     │ item_id (FK) │     │ item_id (FK)     │
                     │ job_type     │     │ actor_id (FK)    │
                     │ status (enum)│     │ action (enum)    │
                     │ error_message│     │ metadata_json    │
                     │ started_at   │     │ created_at       │
                     │ completed_at │     │                  │
                     └──────────────┘     └──────────────────┘
```

### Status Enum (WorkItemStatus)
`pending_review` → `approved` → `processing` → `sent`
                                              → `failed`
                 → `rejected`
                 → `regenerating` → `pending_review`

---

## API Reference

### Auth
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/login` | Login, returns JWT |
| GET | `/api/v1/auth/me` | Current user info |

### Work Items
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/work-items` | List (paginated, filterable) |
| GET | `/api/v1/work-items/{id}` | Get single item |
| PUT | `/api/v1/work-items/{id}` | Edit draft |
| POST | `/api/v1/work-items/{id}/approve` | Approve + trigger job |
| POST | `/api/v1/work-items/{id}/reject` | Reject |
| POST | `/api/v1/work-items/{id}/regenerate` | Regenerate AI draft |
| POST | `/api/v1/work-items/{id}/retry` | Retry failed item |

### Audit Logs
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/audit-logs` | List all org logs |
| GET | `/api/v1/audit-logs/work-item/{id}` | Logs for specific item |

### Admin (admin role only)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/admin/dashboard` | Pipeline stats |
| GET | `/api/v1/admin/users` | List org users |

---

## State Machine

```
                    ┌──────────────┐
                    │   CREATED    │
                    └──────┬───────┘
                           │ AI generates draft
                    ┌──────▼───────┐
              ┌─────│PENDING_REVIEW│◄────────────┐
              │     └──┬────┬──────┘             │
              │        │    │                    │
         Reject│   Edit│ Approve           Regenerate
              │        │    │                    │
              │        │    │            ┌───────┴───────┐
              │        │    │            │ REGENERATING  │
              │        │    │            └───────────────┘
       ┌──────▼──┐     │  ┌▼────────┐
       │REJECTED │     │  │APPROVED │
       └─────────┘     │  └────┬────┘
                       │       │ Celery picks up
                       │  ┌────▼──────┐
                       │  │PROCESSING │
                       │  └──┬─────┬──┘
                       │     │     │
                       │ Success  Failure
                       │     │     │
                       │  ┌──▼──┐ ┌▼──────┐
                       │  │SENT │ │FAILED │──► Retry
                       │  └─────┘ └───────┘
                       │
                       └── Edit saves to edited_output
```

---

## File Structure

### Backend (`backend/`)
```
app/
├── __init__.py
├── main.py              # FastAPI app, CORS, rate limiter
├── config.py            # Pydantic Settings
├── api/
│   ├── deps.py          # Auth dependencies (CurrentUser, AdminUser)
│   └── v1/
│       ├── router.py    # Route aggregation
│       ├── auth.py      # Login, /me
│       ├── work_items.py# CRUD + approve/reject/regenerate
│       ├── audit_logs.py# Audit log queries
│       └── admin.py     # Dashboard stats, user list
├── core/
│   ├── security.py      # JWT encode/decode, bcrypt
│   └── exceptions.py    # Custom HTTP exceptions
├── db/
│   └── session.py       # Async engine, session factory
├── models/
│   ├── organization.py  # Organization ORM
│   ├── user.py          # User ORM (role enum)
│   ├── work_item.py     # LeadWorkItem ORM (status enum)
│   ├── audit_log.py     # AuditLog ORM (action enum)
│   └── background_job.py# BackgroundJob ORM
├── repositories/        # Data access (all org-scoped)
├── schemas/             # Pydantic request/response models
├── services/
│   ├── auth_service.py  # Login logic
│   ├── work_item_service.py # Core business logic
│   └── llm_service.py   # LLM provider factory (Mock/Groq/OpenAI)
└── workers/
    ├── celery_app.py    # Celery configuration
    └── tasks.py         # process_approved_item task
```

### Frontend (`frontend/src/`)
```
app/
├── layout.tsx           # Root layout + AuthProvider
├── page.tsx             # Root redirect → /dashboard
├── globals.css          # Design system (CSS vars + Tailwind)
├── login/page.tsx       # Login page
└── dashboard/
    ├── layout.tsx       # Dashboard shell with sidebar
    ├── page.tsx         # Work queue table
    ├── audit/page.tsx   # Audit log timeline
    ├── admin/page.tsx   # Admin dashboard stats
    └── work-items/[id]/page.tsx  # Review page (split layout)
components/
├── ui/index.tsx         # Button, Card, Badge, Toast, etc.
└── layout/sidebar.tsx   # Sidebar navigation
lib/
├── api.ts               # Typed API client
├── auth.tsx             # Auth context + provider
└── utils.ts             # cn(), formatters
types/
└── index.ts             # TypeScript interfaces
```

---

## Design Rationale FAQ

**Q: Why polling instead of WebSockets?**
A: Browser's `EventSource` can't send custom Authorization headers. WebSockets add complexity (reconnection, auth handshake). 2-second polling with JWT is simpler, reliable, and sufficient for this use case.

**Q: How do you prevent IDOR attacks?**
A: Every database query is scoped by `organization_id`. If User A (Org 1) tries to access Work Item from Org 2, the query returns null → 404. We deliberately return 404 instead of 403 to prevent information leakage about what exists.

**Q: Why Celery over a simple background thread?**
A: Celery provides: automatic retries (3x with 5s delay), separate process (won't crash the API), task tracking, concurrency control, and is production-battle-tested. A background thread would die with the API process.

**Q: How does the LLM integration work?**
A: Provider pattern. Abstract base class `LLMProvider` with `generate_follow_up()`. Factory function reads `LLM_PROVIDER` env var and returns Mock/Groq/OpenAI. Groq uses the `openai` SDK with a custom `base_url` pointed at Groq's OpenAI-compatible endpoint. All API keys are server-side only.

**Q: How do you handle multi-tenancy?**
A: Organization model with UUID. Every user belongs to an org. Every query passes `organization_id` from the JWT token through the service → repository chain. No global queries exist.

**Q: What happens when approval is clicked?**
A: 1) Validate status is `pending_review` (prevents double-approve). 2) Save any last-minute edits. 3) Set status to `approved`. 4) Create a `BackgroundJob` record. 5) Create audit log. 6) Commit transaction. 7) Dispatch Celery task with job_id, item_id, org_id. The worker then processes asynchronously.

**Q: How is the frontend auth managed?**
A: React Context (`AuthProvider`). On login, JWT is stored in `localStorage`. Every API call reads the token and adds `Authorization: Bearer <token>` header. On 401 response, the API client auto-clears storage and redirects to `/login`.
