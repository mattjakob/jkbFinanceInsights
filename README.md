# JKB Finance Insights

A modular financial-insights platform with AI-powered analysis, background task processing and scraper integration.  Designed for clarity, portability, and quick onboarding.

---

## ✨ Features at a Glance

| Domain | Highlights |
|--------|------------|
| **Data ingestion** | TradingView scrapers (popular, recent, news, opinions) → SQLite repository |
| **Analysis** | Pluggable AI providers (OpenAI by default) deliver summarisation, action signals & confidence |
| **Presentation** | FastAPI-served HTML templates **and** REST API (Swagger docs) |
| **Background tasks** | Lightweight in-process queue + worker pool for long-running jobs |
| **Portability** | Clear service / repository / provider interfaces → swap web-framework, ORM or task-queue with minimal edits |

---

## 🚀 Quick-start

```bash
# 1. Clone & enter project
$ git clone <repo-url>
$ cd jkbFinanceInsights

# 2. Create & activate venv
$ python -m venv venv && source venv/bin/activate

# 3. Install requirements
$ pip install -r requirements.txt

# 4. Configure environment
$ cp env.example .env  # edit as needed

# 5. Run
$ python main.py  # http://localhost:8000
```

Swagger (OpenAPI) docs live at **/docs**  •  ReDoc at **/redoc**.

---

## 🏗  High-level Architecture

```text
┌──────────────────────────────┐
│        Presentation          │
│  • views/web_routes.py       │
│  • api/routes/*              │
└────────────┬─────────────────┘
             │ calls
┌────────────▼─────────────────┐
│        Services Layer        │
│  • services/*.py             │
└────────────┬─────────────────┘
             │ uses
┌────────────▼─────────────────┐
│        Repositories          │
│  • data/repositories/*.py    │
└────────────┬─────────────────┘
             │ persisted-via
┌────────────▼─────────────────┐
│         Database             │
│  • SQLite (core/database.py) │
└──────────────────────────────┘
```

Deep-dive docs live in [`ARCHITECTURE.md`](ARCHITECTURE.md).

---

## ⚡ API Cheatsheet

```
GET  /api/insights              List or filter insights
POST /api/scraping/fetch        Trigger new scrape
POST /api/analysis/analyze-*    AI analyse text / image / insight
GET  /api/tasks                 Background-task status
```

See `api/routes/` for full surface.

---

## 🗺  Directory Tour (essentials only)

| Path | Role |
|------|------|
| `app.py`            | FastAPI factory – mounts routers, static, templates |
| `services/`         | Business logic (InsightsService, ScrapingService…) |
| `analysis/`         | AI provider interface + implementations |
| `scrapers/`         | TradingView scrapers & coordination manager |
| `tasks/`            | In-proc queue, worker pool & handlers |
| `core/database.py`  | SQLite connection helpers |

_(Full tree & responsibilities in `ARCHITECTURE.md`)_

---

## 🔄 Typical Flow Examples

1. **User opens dashboard** → `views.web_routes:index` renders `templates/index.html` using data from `InsightsService`.
2. **Client hits API** (`/api/insights`) → route delegates to service → repository → DB → JSON response.
3. **Background analysis** – `tasks.queue.enqueue('ai_analysis', {...})` picked by worker → `tasks.handlers.handle_ai_analysis` uses `AnalysisService` → writes results back via repository.

ASCII sequence diagrams & detailed interaction charts inside `ARCHITECTURE.md`.

---

## ➕ Extending

| You want to… | Do this |
|--------------|---------|
| Add new scraper | 1) Subclass `scrapers.base.AbstractScraper` 2) Register in `scrapers/manager.py` |
| Support new AI provider | 1) Implement `analysis.providers.BaseProvider` 2) Add switch logic in `analysis/service.py` |
| Migrate to another web framework | Keep services / repos intact, replace `app.py` with framework adapters |
| Swap SQLite for ORM | Replace methods in `data/repositories/`, keep models |

---

## 🧪 Tests

Run unit tests (if present) with `pytest`.  Recommended conventions:

```bash
$ pytest -q
```

---

## 📜 License

Add your licence text here.