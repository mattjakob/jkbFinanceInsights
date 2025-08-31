# JKB Finance Insights

A comprehensive financial insights platform with AI-powered analysis, automated scraping, and task-based processing. Built with clean architecture principles for maintainability and extensibility.

---

## ✨ Features

| Domain | Capabilities |
|--------|-------------|
| **Data Ingestion** | Automated scraping from TradingView (news, ideas, opinions) with task-based processing |
| **AI Analysis** | OpenAI-powered text and image analysis with trading recommendations |
| **Report Generation** | Comprehensive AI reports aggregating multiple insights |
| **Task Management** | Asynchronous background processing with retry logic and monitoring |
| **Web Interface** | Modern responsive UI with real-time updates |
| **REST API** | Full RESTful API with OpenAPI documentation |
| **Symbol Management** | Advanced symbol search and validation |

---

## 🚀 Quick Start

```bash
# 1. Clone and setup
git clone <repo-url>
cd jkbFinanceInsights

# 2. Create virtual environment
python -m venv venv && source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp env.example .env
# Edit .env with your OpenAI API key and other settings

# 5. Run the application
python main.py
# Access at http://localhost:8000
```

**API Documentation:** `/docs` (Swagger) • `/redoc` (ReDoc)

---

## 🏗 Architecture Overview

### Service Layer Organization

```text
┌─────────────────────────────────────────────────┐
│                PRESENTATION LAYER               │
│  ┌─────────────────┐    ┌─────────────────────┐ │
│  │   Web Routes    │    │    API Routes       │ │
│  │ (HTML Templates)│    │   (JSON/REST)       │ │
│  └─────────────────┘    └─────────────────────┘ │
└─────────────────┬───────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────┐
│                SERVICES LAYER                   │
│  ┌─────────────────────────────────────────────┐ │
│  │ InsightManagementService                    │ │
│  │ • CRUD operations for insights              │ │
│  │ • Validation and deduplication              │ │
│  └─────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────┐ │
│  │ InsightScrapingService                      │ │
│  │ • Creates scraping tasks                    │ │
│  │ • Manages external data fetching           │ │
│  └─────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────┐ │
│  │ InsightAnalysisService                      │ │
│  │ • AI analysis of insights                   │ │
│  │ • Trading recommendations                   │ │
│  └─────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────┐ │
│  │ ReportService                               │ │
│  │ • AI report generation                      │ │
│  │ • Report lifecycle management               │ │
│  └─────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────┐ │
│  │ SymbolService                               │ │
│  │ • Symbol search and validation              │ │
│  │ • Exchange management                       │ │
│  └─────────────────────────────────────────────┘ │
└─────────────────┬───────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────┐
│              REPOSITORY LAYER                   │
│  ┌─────────────────┐    ┌─────────────────────┐ │
│  │ InsightsRepo    │    │   ReportsRepo       │ │
│  │ (Raw SQL)       │    │   (Raw SQL)         │ │
│  └─────────────────┘    └─────────────────────┘ │
└─────────────────┬───────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────┐
│                DATABASE LAYER                   │
│  ┌─────────────────────────────────────────────┐ │
│  │            SQLite Database                  │ │
│  │ • WAL mode for concurrency                  │ │
│  │ • Connection pooling and retries            │ │
│  └─────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────┘
```

---

## 📊 Data Models

### Core Models

| Model | Purpose | Key Fields |
|-------|---------|------------|
| `InsightModel` | Financial insight data | type, title, content, symbol, ai_analysis |
| `ReportModel` | AI analysis reports | symbol, ai_summary, ai_action, confidence |
| `ScrapedItem` | Raw scraped data | title, content, timestamp, source_url |
| `TaskInfo` | Task tracking | name, status (pending/processing/completed) |

### Enumerations

| Enum | Values | Usage |
|------|--------|-------|
| `FeedType` | TD_NEWS, TD_IDEAS_RECENT, TD_IDEAS_POPULAR, TD_OPINIONS | Categorizing data sources |
| `TradingAction` | BUY, SELL, HOLD, WATCH | AI trading recommendations |
| `TaskStatus` | EMPTY, PENDING, PROCESSING, COMPLETED, FAILED | Task lifecycle |
| `TaskName` | AI_ANALYSIS, SCRAPING_*, REPORT_GENERATION | Task type identification |

---

## 🔄 Data Flow Examples

### 1. Insight Scraping Flow

```text
User/API Request
       │
       ▼
┌─────────────────────┐
│ InsightScrapingService │
│ • Validates parameters │
│ • Creates scraping task│
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│    Task Queue       │
│ • Stores task       │
│ • Status: PENDING   │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│   Worker Pool       │
│ • Picks up task     │
│ • Routes to handler │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│ Scraping Handler    │
│ • Calls scraper     │
│ • Stores insights   │
│ • Updates status    │
└─────────────────────┘
```

### 2. AI Analysis Flow

```text
Insight Created
       │
       ▼
┌─────────────────────┐
│   Task Creation     │
│ • ai_image_analysis │
│ • ai_text_analysis  │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│   AI Analysis       │
│ • OpenAI API calls  │
│ • Image processing  │
│ • Text analysis     │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  Result Storage     │
│ • Trading action    │
│ • Confidence score  │
│ • Summary & levels  │
└─────────────────────┘
```

---

## 🛠 Development

### Service Structure

Each service has a specific domain responsibility:

- **InsightManagementService:** Pure CRUD operations, no external calls
- **InsightScrapingService:** Task creation only, actual scraping in handlers
- **InsightAnalysisService:** AI analysis coordination
- **ReportService:** Report generation and management
- **SymbolService:** Symbol operations and validation

### Adding New Features

1. **New Scraper:** Inherit from `BaseScraper`, add task handler
2. **New AI Provider:** Implement `AIProvider` interface
3. **New Report Type:** Extend models and add service methods

---

## 📈 Performance & Monitoring

- **SQLite WAL mode** for concurrent operations
- **Async task processing** prevents blocking
- **Rate limiting** for external API calls
- **Configurable timeouts** for all operations
- **Real-time monitoring** via web interface

---

## 📚 Documentation

- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Detailed technical architecture
- **API Documentation** - Available at `/docs` when running
- **Code Documentation** - Comprehensive docstrings throughout

---

*Built with clean architecture principles for maintainability and extensibility*
