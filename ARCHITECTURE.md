# Technical Architecture Documentation

## System Overview

JKB Finance Insights is a modular financial data management system designed with clean architecture principles and framework portability in mind.

## Architecture Patterns

### 1. Layered Architecture

```
┌─────────────────────────────────────────┐
│           Presentation Layer            │ ← HTTP/Web Interface
├─────────────────────────────────────────┤
│            Business Layer               │ ← Services & Logic  
├─────────────────────────────────────────┤
│             Data Layer                  │ ← Repositories & Models
├─────────────────────────────────────────┤
│          Infrastructure Layer           │ ← Database, External APIs
└─────────────────────────────────────────┘
```

### 2. Repository Pattern
- **Purpose**: Abstract data access logic
- **Benefits**: Framework-agnostic data operations, testability
- **Implementation**: Repository classes in `data/repositories/`

### 3. Service Layer Pattern
- **Purpose**: Encapsulate business logic
- **Benefits**: Reusable across different presentation layers
- **Implementation**: Service classes in `services/`

### 4. Provider Pattern
- **Purpose**: Abstract external service integrations
- **Benefits**: Swappable implementations (OpenAI, Claude, etc.)
- **Implementation**: Provider classes in `analysis/providers/`

## Module Dependencies

```
Views/API Routes
    ↓ depends on
Services
    ↓ depends on
Repositories ←→ Models
    ↓ depends on
Database/External APIs
```

### Dependency Rules
1. **Inner layers** never depend on outer layers
2. **Services** coordinate between repositories and external systems
3. **Controllers** only handle HTTP concerns and delegate to services
4. **Repositories** only handle data access concerns

## Data Flow Patterns

### 1. Request-Response Flow
```
HTTP Request → Route Handler → Service → Repository → Database
                   ↓              ↓         ↓
              Response ← Business Logic ← Data Access
```

### 2. Background Processing Flow
```
Trigger → Task Queue → Worker Pool → Handler → Service → Repository
```

### 3. External Data Integration
```
Scheduler → Scraper → Service → Repository → Database
              ↓
         AI Analysis → Service → Repository
```

## Component Interactions

### Core Components

#### 1. **Core Module** (`core/`)
- **Purpose**: Domain models and database infrastructure
- **Key Files**:
  - `models.py`: Domain entities (InsightModel, ReportModel, etc.)
  - `database.py`: Database connection management

#### 2. **Services Module** (`services/`)
- **Purpose**: Business logic coordination
- **Key Files**:
  - `insights_service.py`: Insights business operations
  - `scraping_service.py`: Data fetching coordination
  - `analysis_service.py`: AI analysis management

#### 3. **Data Module** (`data/`)
- **Purpose**: Data access abstraction
- **Key Files**:
  - `repositories/insights.py`: Insights data operations
  - `repositories/reports.py`: Reports data operations

#### 4. **API Module** (`api/`)
- **Purpose**: RESTful API endpoints
- **Structure**: Organized by resource type (insights, scraping, analysis)

#### 5. **Views Module** (`views/`)
- **Purpose**: Web interface routes
- **Structure**: HTML template rendering for user interface

## Framework Portability Design

### Database Abstraction
Current implementation uses raw SQL with SQLite, designed for easy SQLAlchemy migration:

```python
# Current Repository Pattern
class InsightsRepository:
    def find_all(self) -> List[InsightModel]:
        with get_db_session() as conn:
            rows = conn.execute("SELECT * FROM insights").fetchall()
            return [InsightModel.from_dict(dict(row)) for row in rows]

# Future SQLAlchemy Migration
class InsightsRepository:
    def find_all(self) -> List[InsightModel]:
        insights = self.session.query(Insight).all()
        return [insight.to_model() for insight in insights]
```

### Service Layer Independence
Services are framework-agnostic and can work with any web framework:

```python
# Works with FastAPI, Flask, Django, etc.
class InsightsService:
    def get_insights(self, filters) -> List[Dict]:
        # Framework-independent business logic
        return self.repository.find_all(**filters)
```

### Task System Abstraction
Current task system designed for easy migration to RQ/Dramatiq:

```python
# Current Implementation
class TaskWorker:
    def process_task(self, task):
        handler = HANDLERS[task.type]
        return handler(task.data)

# Future RQ Migration
@job
def process_ai_analysis(insight_id):
    return handle_ai_analysis({'insight_id': insight_id})
```

## Database Design

### Schema Philosophy
- **Denormalized for performance**: Optimized for read operations
- **JSON fields**: For flexible AI analysis results
- **Indexes**: Strategic indexing on query patterns
- **Constraints**: Minimal to allow flexibility

### Key Tables

#### insights
```sql
CREATE TABLE insights (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timeFetched TEXT NOT NULL,           -- ISO timestamp
    timePosted TEXT NOT NULL,            -- ISO timestamp  
    type TEXT NOT NULL,                  -- FeedType enum value
    title TEXT NOT NULL,                 -- Max 200 chars
    content TEXT NOT NULL,               -- Full content
    symbol TEXT,                         -- Trading symbol
    exchange TEXT,                       -- Exchange name
    imageURL TEXT,                       -- Optional image
    AIImageSummary TEXT,                 -- AI image analysis
    AISummary TEXT,                      -- AI text analysis
    AIAction TEXT,                       -- AI recommendation
    AIConfidence REAL,                   -- 0.0 to 1.0
    AIEventTime TEXT,                    -- AI predicted timing
    AILevels TEXT,                       -- Support/resistance levels
    AIAnalysisStatus TEXT DEFAULT 'empty' -- Processing status
);

-- Indexes for performance
CREATE INDEX idx_insights_type ON insights(type);
CREATE INDEX idx_insights_symbol ON insights(symbol);
CREATE INDEX idx_insights_status ON insights(AIAnalysisStatus);
CREATE INDEX idx_insights_timePosted ON insights(timePosted);
```

#### reports
```sql
CREATE TABLE reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timeFetched TEXT NOT NULL,
    symbol TEXT NOT NULL,
    AISummary TEXT NOT NULL,
    AIAction TEXT NOT NULL,
    AIConfidence REAL NOT NULL,
    AIEventTime TEXT,
    AILevels TEXT,
    AIAnalysisStatus TEXT DEFAULT 'completed'
);

-- Indexes
CREATE INDEX idx_reports_symbol ON reports(symbol);
CREATE INDEX idx_reports_timeFetched ON reports(timeFetched);
```

## API Design

### RESTful Principles
- **Resource-based URLs**: `/api/insights/{id}`
- **HTTP methods**: GET, POST, PUT, DELETE
- **Status codes**: Proper HTTP status codes
- **JSON responses**: Consistent response format

### Response Format
```json
{
    "success": true,
    "data": {...},
    "message": "Operation completed",
    "timestamp": "2024-01-01T00:00:00Z"
}
```

### Error Handling
```json
{
    "success": false,
    "error": "Validation failed",
    "details": {...},
    "timestamp": "2024-01-01T00:00:00Z"
}
```

## Security Architecture

### Input Validation
- **Pydantic models** for request validation
- **Type checking** at runtime
- **SQL injection prevention** through parameterized queries

### Authentication & Authorization
- **Stateless design** ready for JWT implementation
- **Role-based access** structure prepared
- **API key support** for external integrations

### Data Protection
- **Environment variables** for sensitive data
- **No hardcoded secrets** in codebase
- **Secure defaults** in configuration

## Performance Considerations

### Database Optimization
- **Strategic indexing** on frequently queried columns
- **Connection pooling** through database manager
- **Query optimization** in repository layer

### Caching Strategy
- **Application-level caching** for expensive operations
- **Database query result caching**
- **Static asset caching**

### Scalability Design
- **Stateless services** for horizontal scaling
- **Background task processing** for heavy operations
- **Database connection management** for concurrent requests

## Monitoring & Observability

### Logging Strategy
```python
# Centralized logging through debugger.py
debug_info("Operation started")
debug_success("Operation completed")
debug_error("Operation failed", error)
debug_warning("Potential issue detected")
```

### Health Checks
- **Database connectivity** checks
- **External service** availability
- **Task queue** status monitoring

### Metrics Collection
- **Response times** for API endpoints
- **Task processing** statistics
- **Error rates** by component

## Testing Strategy

### Unit Testing
```python
# Service layer testing
def test_insights_service():
    mock_repo = Mock(spec=InsightsRepository)
    service = InsightsService(mock_repo)
    
    result = service.get_insights()
    
    mock_repo.find_all.assert_called_once()
    assert isinstance(result, list)
```

### Integration Testing
```python
# API endpoint testing
def test_insights_api(client):
    response = client.get("/api/insights")
    
    assert response.status_code == 200
    assert "insights" in response.json()
```

### End-to-End Testing
```python
# Full workflow testing
def test_scraping_workflow():
    # Test: Scrape → Store → Analyze → Report
    pass
```

## Deployment Architecture

### Environment Configuration
```bash
# Development
DEBUG_MODE=true
DATABASE_URL=sqlite:///dev.db

# Production  
DEBUG_MODE=false
DATABASE_URL=postgresql://user:pass@host/db
```

### Container Ready
```dockerfile
FROM python:3.11-slim
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . /app
WORKDIR /app
CMD ["python", "main.py"]
```

### Process Management
- **Single process** for development
- **Multiple workers** for production (Gunicorn/uWSGI)
- **Background workers** for task processing

## Migration Paths

### To Flask + SQLAlchemy
1. Replace FastAPI routes with Flask routes
2. Replace repository implementations with SQLAlchemy
3. Services remain unchanged
4. Update dependency injection

### To Django
1. Convert models to Django models
2. Replace services with Django views/viewsets
3. Update URL patterns
4. Integrate with Django ORM

### To HTMX Frontend
1. Add HTMX library to templates
2. Convert JavaScript interactions to HTMX attributes
3. Create partial template endpoints
4. Update frontend refresh logic

### To RQ/Dramatiq
1. Replace task queue with Redis-backed queue
2. Convert task handlers to job functions
3. Update worker management
4. Add job monitoring

## Code Quality Standards

### Documentation Standards
```python
"""
/**
 * 
 *  ┌─────────────────────────────────────┐
 *  │         FUNCTION NAME               │
 *  └─────────────────────────────────────┘
 *  Brief description
 * 
 *  Detailed explanation of functionality.
 * 
 *  Parameters:
 *  - param1: Description
 * 
 *  Returns:
 *  - Return value description
 * 
 *  Notes:
 *  - Additional notes
 */
"""
```

### Type Hints
```python
def process_insights(
    insights: List[InsightModel],
    filters: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    # Implementation
```

### Error Handling
```python
try:
    result = risky_operation()
    debug_success("Operation completed")
    return result
except SpecificException as e:
    debug_error(f"Specific error: {e}")
    raise HTTPException(status_code=400, detail=str(e))
except Exception as e:
    debug_error(f"Unexpected error: {e}")
    raise HTTPException(status_code=500, detail="Internal server error")
```

This architecture provides a solid foundation for maintainable, scalable, and portable financial insights management system.
