# SmartDesk AI

AI-powered customer support platform that enables companies to deploy intelligent chat widgets on their websites. The system answers customer questions based on company-uploaded documents using RAG (Retrieval Augmented Generation), with seamless fallback to live human operators.

---

## Features

- **Company Onboarding** — Registration, email verification, login/logout, password reset, company profile management
- **Knowledge Base** — Upload PDF, Word, TXT files or paste raw text; FAQ management; processing status tracking
- **AI Chat** — Answers customer questions based on uploaded documents using RAG; shows source document; falls back to operator when answer not found
- **Chat Widget** — Embeddable one-line script tag; customizable name, color, icon; domain allowlist; mobile-friendly
- **Live Operator Support** — Real-time handoff to human operator via WebSocket; operator dashboard; auto-return to AI after conversation ends
- **Conversation History & Analytics** — Full conversation logs, most asked questions, unanswered questions list, daily/weekly/monthly stats
- **Notification System** — Email alerts for unanswered conversations, operator handoff requests, weekly analytics summary
- **Subscription & Billing** — Free/paid plans with usage limits, Stripe integration, invoice history, plan upgrade/downgrade
- **Super Admin Panel** — Platform-wide company management, block/activate companies, manual plan changes, revenue stats
- **Performance Tested** — Load tested with Locust (100 concurrent users)

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python, Django, Django REST Framework |
| Database | PostgreSQL, pgvector |
| Cache & Queue | Redis, Celery |
| Real-time | Django Channels, WebSockets |
| AI / RAG | LangChain, OpenAI Embeddings |
| Payments | Stripe, dj-stripe |
| Auth | JWT (SimpleJWT) |
| Background Tasks | Celery Beat |
| Performance Testing | Locust |
| Containerization | Docker, Docker Compose |
| Code Quality | Ruff, Bandit, Safety, Pytest |

---

## Getting Started

### Prerequisites

- Python 3.14+
- Docker & Docker Compose
- uv

### Setup

```bash
# Clone the repository
git clone https://github.com/mammadov115/smartdesk-ai.git
cd smartdesk-ai

# Start infrastructure (Postgres, Redis, pgBouncer)
make docker-start

# Run migrations
make django-migrate

# Create superuser
make django-initadmin

# Start the server
make docker-up
```

### Running Celery Worker

```bash
make celery-run
```

### Running Tests

```bash
make test
```

### Performance Testing

```bash
# With UI (open http://localhost:8089)
make perf-test

# Headless — 100 users, 60 seconds
make perf-test-headless
```

### Code Quality

```bash
make check  # format + lint + security scan + tests + migration check
```

---

## Environment Variables

Copy `.envs/.local/.env.example` to `.envs/.local/.env` and fill in:

```env
DATABASE_URL=postgres://...
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=...
OPENAI_API_KEY=sk-...
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
DJSTRIPE_WEBHOOK_SECRET=whsec_...
```

---

## Available Make Commands

```bash
make help  # lists all available commands
```

---

## License

Private — all rights reserved.