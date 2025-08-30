# JKB Finance Insights – Technical Architecture

**Version 2.0 – unified documentation**  
_This file supersedes previous `DEPLOYMENT.md` and `MIGRATION_GUIDE.md`._

---

## 1️⃣ System Overview

JKB Finance Insights ingests real-time TradingView content, stores it locally, performs AI summarisation, and exposes the results via web UI & REST API.  The design follows Clean / Hexagonal principles: inner business logic free from framework concerns and external adapters swappable via interfaces.

---

## 2️⃣ Architectural Principles

* **Layered separation** – presentation → services → repositories → infrastructure  
* **Interface abstraction** – providers, scrapers, repositories specified via _ABC_ classes  
* **Framework portability** – swap FastAPI, SQLite, in-process queue with Flask, SQLAlchemy, RQ, etc. without touching core logic  
* **Configuration over hard-coding** – all tunables live in `.env` loaded by `config.py`  
* **Background off-loading** – long running work executed by lightweight worker pool to keep web latency low

---

## 3️⃣ Directory & Key Components

```text
jkbFinanceInsights/
├── app.py                FastAPI factory & lifespan
├── main.py               Entrypoint (spawns uvicorn)
├── config.py             Env-driven settings helper
├── core/
│   ├── models.py         Pydantic / dataclass domain entities
│   └── database.py       SQLite helper (row factory, WAL, retries)
├── data/repositories/    Data access layer (raw SQL – swap-ready)
├── services/             Business orchestration
├── analysis/             AI provider interface + OpenAI impl
├── scrapers/             TradingView scrapers + manager
├── tasks/                In-process queue, handlers, workers
├── views/                HTML routes (templates/)
└── api/routes/           REST endpoints
```

### Key Classes & Responsibilities

| Module | Class / Function | Purpose |
|--------|------------------|---------|
| `core.database` | `get_db_manager()` | Context-managed sqlite connects w/ retry |
| `analysis.service` | `AnalysisService` | Orchestrates provider calls / caching |
| `analysis.providers.base` | `BaseProvider` | Contract for `analyze_*` methods |
| `services.insights_service` | `InsightsService` | CRUD + business filters |
| `scrapers.manager` | `ScraperManager` | Parallel execution + progress tracking |
| `tasks.worker` | `WorkerPool` | Async workers for queued tasks |

---

## 4️⃣ Runtime Flows

### 4.1 Web/UI Request

```text
Browser → GET /           (views.web_routes)
               ↓ calls InsightsService
               ↓ uses InsightsRepository
               ↓ hits SQLite
Template ← data ← service ← repo ← DB
```

### 4.2 API Request

```text
Client → /api/insights     (api.routes.insights)
             ↓ InsightsService
             ↓ InsightsRepository
             ↓ SQLite
JSON ← data ← service ← repo ← DB
```

### 4.3 Scrape & Analysis Background

```text
cron / user
   ↓ enqueue('scrape')         tasks.queue
   ↓ handled by WorkerPool → tasks.handlers.handle_scrape
   ↓ ScraperManager runs N scrapers
   ↓ writes new rows (status: empty)
   ↓ enqueue('ai_analysis') for each row
   ↓ WorkerPool → handle_ai_analysis
   ↓ AnalysisService → OpenAIProvider
   ↓ repository.update insight
```

_(Sequence diagram available in `/docs/diagrams` when generated)_

---

## 5️⃣ Deployment

### 5.1 Local (dev)

```bash
$ python main.py  # uses uvicorn reload if enabled in .env
```

Hot-reload templates & code via env var `UVICORN_RELOAD=true`.

### 5.2 Production (example)

```bash
$ uvicorn main:app --host 0.0.0.0 --port 80 --workers 4 --log-level info
```

Add a proper process manager (systemd, supervisor, docker-entrypoint) as needed.

---

## 6️⃣ Porting Guide

| Target | Changes Needed |
|--------|----------------|
| **Flask** | Replace `app.py` with Flask factory, mount blueprints mapping to services. Services / repos unchanged. |
| **Django** | Keep services; move repositories to Django ORM; create views calling services. |
| **SQLAlchemy** | Implement ORM models; update repository methods to use session queries. |
| **RQ / Dramatiq** | Swap `tasks.worker` with decorators; service / handler logic reusable. |
| **HTMX frontend** | Inject `hx-get` attributes in templates; existing routes return partials. |

---

## 7️⃣ Extending the System

1. **New Feed Scraper**  
   • Create `<name>.py` subclassing `scrapers.base.AbstractScraper`  
   • Import & register in `scrapers.manager.py`  
2. **Alternate AI Provider**  
   • Implement `analysis.providers.BaseProvider`  
   • Add selection logic (env var `AI_PROVIDER`) in `analysis/service.py`  
3. **Additional Report Type**  
   • Extend `core.models` & DB schema  
   • Create repository + service methods  
   • Wire up API / UI layer

---

## 8️⃣ Testing Matrix

| Layer | Strategy |
|-------|----------|
| Services | Unit tests with mocked repos/providers |
| API Routes | Integration tests via FastAPI `TestClient` |
| Background tasks | Simulate queue, assert handler side-effects |
| Scrapers | Record/replay HTTP responses (VCR.py) |

Run all with `pytest -q`.

---

## 9️⃣ Performance & Scaling Notes

* Enable SQLite WAL (default via `.env`) for concurrent reads/writes  
* Indexes on `insights(type, symbol, AIAnalysisStatus, timePosted)`  
* Offload CPU/API heavy work using external job queue when traffic grows  
* Cache analysis results in provider layer if using paid API

---

## 🔚 End of File
