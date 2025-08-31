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
├── services/             Business orchestration (domain-specific services)
│   ├── insight_management_service.py  CRUD operations for insights
│   ├── insight_scraping_service.py    External data fetching via tasks
│   ├── insight_analysis_service.py    AI analysis of insights
│   ├── report_service.py              AI report generation
│   └── symbol_service.py              Symbol search and validation
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
| `services.insight_management_service` | `InsightManagementService` | CRUD operations for insights |
| `services.insight_scraping_service` | `InsightScrapingService` | Creates scraping tasks via queue |
| `services.insight_analysis_service` | `InsightAnalysisService` | AI analysis coordination |
| `services.report_service` | `ReportService` | AI report generation and management |
| `services.symbol_service` | `SymbolService` | Symbol search and validation |
| `scrapers.manager` | `ScraperManager` | Parallel execution + progress tracking |
| `tasks.worker` | `WorkerPool` | Async workers for queued tasks |

---

## 4️⃣ Runtime Flows

### 4.1 Web/UI Request

```text
Browser → GET /           (views.web_routes)
               ↓ calls InsightManagementService
               ↓ uses InsightsRepository
               ↓ hits SQLite
Template ← data ← service ← repo ← DB
```

### 4.2 API Request

```text
Client → /api/insights     (api.routes.insights)
             ↓ InsightManagementService
             ↓ InsightsRepository
             ↓ SQLite
JSON ← data ← service ← repo ← DB
```

### 4.3 Task-Based Processing

```text
API Request
   ↓ InsightScrapingService.create_scraping_task()
   ↓ TaskQueue.add_task('scraping_news')
   ↓ WorkerPool → handle_scraping_news
   ↓ ScraperManager.fetch_and_store()
   ↓ InsightsRepository.create() → new InsightModel (status: EMPTY)
   ↓ Auto-trigger: TaskQueue.add_task('ai_analysis')
   ↓ WorkerPool → handle_ai_analysis
   ↓ AnalysisService → OpenAIProvider
   ↓ InsightsRepository.update() → status: COMPLETED
```

### 4.4 Analysis Task Flow

```text
User clicks ANALYZE button → POST /api/analysis/analyze
   ↓ handle_bulk_analysis() finds pending insights
   ↓ For each insight:
      ├─ Has image? → Create AI_IMAGE_ANALYSIS task
      │   ↓ handle_image_analysis() → OpenAI vision API
      │   ↓ On completion → Create AI_TEXT_ANALYSIS task
      └─ No image? → Create AI_TEXT_ANALYSIS task directly
          ↓ handle_text_analysis() → OpenAI chat API
          ↓ Update insight with analysis results
```

### 4.4 ALL Pattern Implementation

```text
User selects "ALL" feeds
   ↓ InsightScrapingService._create_all_scraping_tasks()
   ↓ Creates individual tasks:
     • scraping_news
     • scraping_ideas_recent  
     • scraping_ideas_popular
     • scraping_opinions
   ↓ Each task processed independently
   ↓ Results aggregated in database
```

_(Sequence diagram available in `/docs/diagrams` when generated)_

---

## 5️⃣ Task System Details

### Overview

The task system provides asynchronous processing for long-running operations like web scraping and AI analysis. It's built as a lightweight, in-process queue with SQLite persistence.

### Core Components

| Component | File | Purpose |
|-----------|------|---------|
| `TaskQueue` | `tasks/queue.py` | Main queue implementation with task lifecycle management |
| `TaskWorker` | `tasks/worker.py` | Individual worker that processes tasks from queue |
| `WorkerPool` | `tasks/worker.py` | Manages multiple workers for concurrent processing |
| `Task Handlers` | `tasks/handlers.py` | Business logic for each task type |

### Task Lifecycle

```text
PENDING → PROCESSING → COMPLETED
                   ↘ → FAILED (with retry)
                   ↘ → CANCELLED
```

1. **Task Creation**: Tasks are added via `TaskQueue.add_task()` with a unique ID
2. **Processing**: Workers poll for pending tasks and mark them as processing
3. **Completion**: On success, tasks are marked completed; on failure, retry count increments
4. **Cleanup**: Old tasks are periodically purged based on retention settings

### Task Types & Handlers

| Task Type | Handler | Purpose |
|-----------|---------|---------|
| `ai_analysis` | `handle_ai_analysis` | Legacy single-step analysis (deprecated) |
| `ai_image_analysis` | `handle_image_analysis` | Analyze insight images with GPT-4 Vision |
| `ai_text_analysis` | `handle_text_analysis` | Analyze insight text content |
| `bulk_analysis` | `handle_bulk_analysis` | Queue analysis for multiple insights |
| `cleanup` | `handle_cleanup` | Clean up old/orphaned tasks |
| `ai_report_generation` | `handle_ai_report_generation` | Generate AI trading reports |
| `scraping_news` | `handle_scraping_news` | Scrape TradingView news |
| `scraping_ideas_recent` | `handle_scraping_ideas_recent` | Scrape recent trading ideas |
| `scraping_ideas_popular` | `handle_scraping_ideas_popular` | Scrape popular trading ideas |
| `scraping_opinions` | `handle_scraping_opinions` | Scrape market opinions |
| `scraping_all` | `handle_scraping_all` | Scrape all feed types |

### Queue Management

#### Key Methods

```python
# Core operations
queue.add_task(task_name, payload, entity_id, entity_type)
queue.get_next_task()
queue.complete_task(task_id, result)
queue.fail_task(task_id, error)

# Monitoring
queue.get_stats()  # Returns counts by status
queue.get_health_metrics()  # Detailed health check

# Maintenance  
queue.cleanup_old_tasks(days=7)
queue.reset_stuck_tasks(timeout_hours=2)
queue.purge_orphaned_tasks()
```

#### Database Schema

```sql
CREATE TABLE simple_tasks (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    payload TEXT,
    status TEXT DEFAULT 'pending',
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    created_at TEXT,
    started_at TEXT,
    completed_at TEXT,
    result TEXT,
    error TEXT,
    entity_id TEXT,
    entity_type TEXT
);
```

### Worker Pool Configuration

Workers are spawned at app startup via the lifespan event:

```python
# In app.py
worker_pool = WorkerPool(num_workers=3)
await worker_pool.start()
```

Each worker:
- Polls for tasks every 1 second
- Processes one task at a time
- Performs maintenance every 100 iterations
- Handles graceful shutdown on SIGTERM

### Task Queue Features

- **Persistence**: Tasks stored in SQLite with full state tracking
- **Retry Logic**: Configurable max retries (default: 3) with exponential backoff
- **Entity Tracking**: Tasks linked to insights/reports for filtering and status updates
- **Concurrent Processing**: Multiple async workers process tasks in parallel
- **Status Management**: Atomic status transitions prevent race conditions
- **Health Monitoring**: Built-in health checks detect queue issues
- **Automatic Cleanup**: Stale tasks cleaned up based on retention policies
- **Graceful Shutdown**: Workers complete current tasks before stopping

### API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/tasks/stats` | GET | Get task counts by status |
| `/api/tasks/status` | GET | Detailed task status report |
| `/api/tasks/cleanup` | POST | Manually trigger cleanup |
| `/api/queue/health` | GET | Queue health metrics |
| `/api/queue/stats` | GET | Detailed queue statistics |
| `/api/queue/reset` | POST | Reset stuck/failed tasks |

### Monitoring & Debugging

1. **UI Status Bar**: Real-time task counters display pending/processing/failed counts
2. **Debug Messages**: Task events logged via centralized debugger
3. **Health Checks**: Queue monitors for issues like:
   - High failure rates (>20%)
   - Stuck tasks (processing >2 hours)
   - Queue backlog (>100 pending)
   - Stale pending tasks (>24 hours old)

### Best Practices

1. **Task Payload**: Keep payloads small; store large data in DB and pass IDs
2. **Idempotency**: Design handlers to be safely retryable
3. **Error Handling**: Use specific error messages for debugging
4. **Entity Updates**: Always update linked entity status on task completion/failure
5. **Cleanup**: Run periodic cleanup to prevent unbounded growth

---

## 6️⃣ Deployment

### 6.1 Local (dev)

```bash
$ python main.py  # uses uvicorn reload if enabled in .env
```

Hot-reload templates & code via env var `UVICORN_RELOAD=true`.

### 6.2 Production (example)

```bash
$ uvicorn main:app --host 0.0.0.0 --port 80 --workers 4 --log-level info
```

Add a proper process manager (systemd, supervisor, docker-entrypoint) as needed.

---

## 7️⃣ Porting Guide

| Target | Changes Needed |
|--------|----------------|
| **Flask** | Replace `app.py` with Flask factory, mount blueprints mapping to services. Services / repos unchanged. |
| **Django** | Keep services; move repositories to Django ORM; create views calling services. |
| **SQLAlchemy** | Implement ORM models; update repository methods to use session queries. |
| **RQ / Dramatiq** | Swap `tasks.worker` with decorators; service / handler logic reusable. |
| **HTMX frontend** | Inject `hx-get` attributes in templates; existing routes return partials. |

---

## 8️⃣ Extending the System

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
