# JKB Finance Insights - Optimized Architecture

A clean, modular financial insights management system with AI analysis capabilities, designed for easy portability and maintainability.

## 🏗️ Architecture Overview

The application follows a **layered architecture** with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                       │
├─────────────────────────────────────────────────────────────┤
│  Views (web_routes.py)     │     API Routes (api/)          │
│  - HTML templates          │     - JSON responses           │
│  - Web interface           │     - RESTful endpoints        │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│                     BUSINESS LAYER                          │
├─────────────────────────────────────────────────────────────┤
│              Services (services/)                           │
│  - InsightsService: Business logic for insights             │
│  - ScrapingService: Scraping coordination                   │
│  - AnalysisService: AI analysis management                  │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│                      DATA LAYER                             │
├─────────────────────────────────────────────────────────────┤
│    Repositories (data/)    │    External Services           │
│  - InsightsRepository      │    - AI Providers              │
│  - ReportsRepository       │    - Web Scrapers              │
│  - Database abstraction    │    - Task Queue                │
└─────────────────────────────────────────────────────────────┘
```

## 📁 Project Structure

```
jkbFinanceInsights/
├── app.py                  # FastAPI app factory
├── main.py                 # Application entry point
├── config.py               # Configuration management
├── debugger.py             # Unified logging system
│
├── core/                   # Core domain models & database
│   ├── models.py           # Data models and enums
│   └── database.py         # Database connection management
│
├── services/               # Business logic layer
│   ├── insights_service.py # Insights business logic
│   ├── scraping_service.py # Scraping coordination
│   └── analysis_service.py # AI analysis management
│
├── views/                  # Web interface routes
│   └── web_routes.py       # HTML template routes
│
├── api/                    # REST API routes
│   └── routes/             # API endpoint modules
│       ├── insights.py     # Insights CRUD operations
│       ├── scraping.py     # Data fetching endpoints
│       ├── analysis.py     # AI analysis endpoints
│       └── ...
│
├── data/                   # Data access layer
│   └── repositories/       # Repository pattern implementation
│       ├── insights.py     # Insights data access
│       └── reports.py      # Reports data access
│
├── analysis/               # AI analysis system
│   ├── service.py          # Analysis orchestration
│   ├── models.py           # Analysis data models
│   └── providers/          # AI provider implementations
│       ├── base.py         # Provider interface
│       └── openai.py       # OpenAI implementation
│
├── scrapers/               # External data fetching
│   ├── base.py             # Scraper interface
│   ├── manager.py          # Scraper coordination
│   └── tradingview_*.py    # TradingView scrapers
│
├── tasks/                  # Background task system
│   ├── queue.py            # Task queue implementation
│   ├── worker.py           # Worker pool management
│   └── handlers.py         # Task handler functions
│
├── templates/              # Jinja2 HTML templates
├── static/                 # Static assets
│   ├── style.css           # Application styles
│   └── js/
│       └── simple-app.js   # Simplified frontend logic
│
└── venv/                   # Python virtual environment
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Virtual environment support

### Installation

1. **Clone and navigate to the project:**
   ```bash
   git clone <repository-url>
   cd jkbFinanceInsights
   ```

2. **Set up virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**
   ```bash
   cp env.example .env
   # Edit .env with your configuration
   ```

5. **Run the application:**
   ```bash
   python main.py
   ```

6. **Access the application:**
   - Web Interface: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

## ⚙️ Configuration

The application uses environment variables for configuration. Key settings:

```bash
# Server Configuration
SERVER_HOST=127.0.0.1
SERVER_PORT=8000

# Database
DATABASE_URL=finance_insights.db

# AI Configuration
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4-vision-preview

# Frontend Behavior
FRONTEND_UNIFIED_REFRESH_INTERVAL=1000
FRONTEND_TABLE_REFRESH_INTERVAL=10000
APP_AUTO_REFRESH=true
APP_MAX_ITEMS=25
```

## 🏛️ Architecture Principles

### 1. **Separation of Concerns**
- **Views**: Handle HTTP requests and render templates
- **Services**: Contain business logic and coordinate operations
- **Repositories**: Manage data access and persistence
- **Models**: Define data structures and domain entities

### 2. **Dependency Injection**
- Services are injected into controllers
- Repositories are injected into services
- Easy to test and swap implementations

### 3. **Interface Segregation**
- Clear interfaces for AI providers, scrapers, and repositories
- Easy to add new implementations

### 4. **Framework Portability**
The architecture is designed for easy migration to other frameworks:

#### **Flask Migration Ready**
```python
# Current FastAPI → Future Flask
from services import InsightsService

@app.route('/api/insights')
def get_insights():
    service = InsightsService()
    return jsonify(service.get_insights())
```

#### **SQLAlchemy Ready**
```python
# Current Repository → Future ORM
class InsightsRepository:
    def find_all(self):
        # Current: Raw SQL
        # Future: return session.query(Insight).all()
```

#### **HTMX Ready**
Templates are structured for component-based updates:
```html
<!-- Current full page → Future partial updates -->
<div id="insights-table" hx-get="/api/insights" hx-trigger="every 10s">
    <!-- Table content -->
</div>
```

#### **RQ/Dramatiq Ready**
```python
# Current task system → Future job queue
from tasks.handlers import handle_ai_analysis

# Current: Internal queue
# Future: @job decorator for RQ/Dramatiq
```

## 🔄 Data Flow

### 1. **Web Request Flow**
```
User → Web Route → Service → Repository → Database
                     ↓
              Template ← Data ← Response
```

### 2. **API Request Flow**
```
Client → API Route → Service → Repository → Database
                       ↓
               JSON Response ← Data
```

### 3. **Background Processing**
```
Trigger → Task Queue → Worker → Handler → Service → Repository
```

## 🧪 Testing Strategy

The modular architecture enables comprehensive testing:

```python
# Unit Tests: Test services in isolation
def test_insights_service():
    mock_repo = Mock()
    service = InsightsService(mock_repo)
    # Test business logic

# Integration Tests: Test with real database
def test_insights_api():
    response = client.get("/api/insights")
    assert response.status_code == 200

# End-to-End Tests: Test complete workflows
def test_scraping_workflow():
    # Test scraping → storage → analysis pipeline
```

## 📊 Database Schema

### Core Tables

**insights**: Financial insights with AI analysis
```sql
CREATE TABLE insights (
    id INTEGER PRIMARY KEY,
    timeFetched TEXT NOT NULL,
    timePosted TEXT NOT NULL,
    type TEXT NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    symbol TEXT,
    exchange TEXT,
    imageURL TEXT,
    AISummary TEXT,
    AIAction TEXT,
    AIConfidence REAL,
    AIAnalysisStatus TEXT DEFAULT 'empty'
);
```

**reports**: AI analysis reports
```sql
CREATE TABLE reports (
    id INTEGER PRIMARY KEY,
    timeFetched TEXT NOT NULL,
    symbol TEXT NOT NULL,
    AISummary TEXT NOT NULL,
    AIAction TEXT NOT NULL,
    AIConfidence REAL NOT NULL,
    AIAnalysisStatus TEXT DEFAULT 'completed'
);
```

## 🔌 API Endpoints

### Insights Management
- `GET /api/insights` - List insights with filtering
- `GET /api/insights/{id}` - Get specific insight
- `POST /api/insights` - Create new insight
- `PUT /api/insights/{id}` - Update insight
- `DELETE /api/insights/{id}` - Delete insight

### Data Scraping
- `POST /api/scraping/fetch` - Fetch new data
- `GET /api/scraping/feeds` - List available feeds
- `GET /api/scraping/symbols/search` - Search symbols

### AI Analysis
- `POST /api/analysis/analyze-insight` - Analyze insight
- `POST /api/analysis/analyze-text` - Analyze text content
- `POST /api/analysis/analyze-image` - Analyze image content

### Task Management
- `GET /api/tasks` - List background tasks
- `POST /api/tasks/{type}` - Queue new task
- `DELETE /api/tasks/{id}` - Cancel task

## 🎨 Frontend Architecture

### Simplified JavaScript
The frontend uses a single, straightforward JavaScript file:

```javascript
// Direct API communication
class SimpleApp {
    async fetchInsights() {
        const response = await fetch('/api/insights');
        return response.json();
    }
    
    async updateTable() {
        // Simple DOM updates
    }
}
```

### Key Features
- **Direct API calls** (no complex managers)
- **Simple refresh intervals**
- **Minimal dependencies**
- **Easy to understand and modify**

## 🔄 Migration Guide

### To Flask + SQLAlchemy

1. **Replace FastAPI with Flask:**
   ```python
   # app.py
   from flask import Flask
   from services import InsightsService
   
   app = Flask(__name__)
   
   @app.route('/api/insights')
   def get_insights():
       service = InsightsService()
       return jsonify(service.get_insights())
   ```

2. **Replace Repository with SQLAlchemy:**
   ```python
   # models.py
   from sqlalchemy import Column, Integer, String
   from sqlalchemy.ext.declarative import declarative_base
   
   Base = declarative_base()
   
   class Insight(Base):
       __tablename__ = 'insights'
       id = Column(Integer, primary_key=True)
       title = Column(String(200), nullable=False)
       # ... other fields
   ```

3. **Update Services:**
   Services remain largely unchanged, just swap repository implementations.

### To HTMX Frontend

1. **Add HTMX to templates:**
   ```html
   <script src="https://unpkg.com/htmx.org@1.8.4"></script>
   ```

2. **Convert to partial updates:**
   ```html
   <div hx-get="/api/insights" hx-trigger="every 10s">
       <!-- Dynamic content -->
   </div>
   ```

### To RQ/Dramatiq

1. **Replace task system:**
   ```python
   from rq import Queue
   from tasks.handlers import handle_ai_analysis
   
   @job
   def analyze_insight(insight_id):
       return handle_ai_analysis({'insight_id': insight_id})
   ```

## 🛠️ Development Workflow

### Adding New Features

1. **Define models** in `core/models.py`
2. **Create repository** in `data/repositories/`
3. **Implement service** in `services/`
4. **Add API routes** in `api/routes/`
5. **Add web routes** in `views/` (if needed)
6. **Update templates** and frontend

### Code Quality Standards

- **Type hints** for all function parameters and returns
- **Docstring headers** for all classes and functions
- **Error handling** with proper logging
- **No hardcoded values** - use configuration
- **Single responsibility** principle for all modules

## 📈 Performance Considerations

- **Database indexes** on frequently queried fields
- **Connection pooling** for database access
- **Caching** for expensive operations
- **Background processing** for time-consuming tasks
- **Pagination** for large data sets

## 🔒 Security Features

- **Input validation** on all endpoints
- **SQL injection prevention** through parameterized queries
- **Rate limiting** configuration available
- **Environment-based secrets** management
- **CORS configuration** for cross-origin requests

## 🤝 Contributing

1. **Follow the architecture patterns** established in the codebase
2. **Add tests** for new functionality
3. **Update documentation** for any changes
4. **Use the established code style** and commenting format
5. **Ensure framework portability** is maintained

## 📝 License

[Add your license information here]

---

This optimized architecture provides a solid foundation for financial insights management while maintaining flexibility for future framework migrations and feature additions.