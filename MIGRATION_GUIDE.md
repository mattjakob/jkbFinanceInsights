# Framework Migration Guide

This guide provides step-by-step instructions for migrating JKB Finance Insights to different frameworks and technologies.

## 🎯 Migration Philosophy

The current architecture is designed with **framework portability** in mind:

- **Services layer** remains framework-agnostic
- **Repository pattern** abstracts data access
- **Provider pattern** abstracts external services
- **Clean separation** between business logic and framework code

## 🌶️ Flask + SQLAlchemy Migration

### Step 1: Setup Flask Application

#### Install Dependencies
```bash
pip install flask flask-sqlalchemy flask-migrate python-dotenv
```

#### Create Flask App Factory
```python
# app.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///finance_insights.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Register blueprints
    from views.web_routes import web_bp
    from api.routes import api_bp
    
    app.register_blueprint(web_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    
    return app
```

### Step 2: Convert Models to SQLAlchemy

#### Create SQLAlchemy Models
```python
# models/sqlalchemy_models.py
from app import db
from datetime import datetime
from enum import Enum

class FeedType(Enum):
    TD_NEWS = "TD NEWS"
    TD_IDEAS_RECENT = "TD IDEAS RECENT"
    TD_IDEAS_POPULAR = "TD IDEAS POPULAR"
    TD_OPINIONS = "TD OPINIONS"

class AIAnalysisStatus(Enum):
    EMPTY = "empty"
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class Insight(db.Model):
    __tablename__ = 'insights'
    
    id = db.Column(db.Integer, primary_key=True)
    time_fetched = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    time_posted = db.Column(db.DateTime, nullable=False)
    type = db.Column(db.Enum(FeedType), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    symbol = db.Column(db.String(20))
    exchange = db.Column(db.String(50))
    image_url = db.Column(db.String(500))
    ai_image_summary = db.Column(db.Text)
    ai_summary = db.Column(db.Text)
    ai_action = db.Column(db.String(20))
    ai_confidence = db.Column(db.Float)
    ai_event_time = db.Column(db.String(100))
    ai_levels = db.Column(db.Text)
    ai_analysis_status = db.Column(db.Enum(AIAnalysisStatus), default=AIAnalysisStatus.EMPTY)
    
    def to_dict(self):
        return {
            'id': self.id,
            'timeFetched': self.time_fetched.isoformat(),
            'timePosted': self.time_posted.isoformat(),
            'type': self.type.value,
            'title': self.title,
            'content': self.content,
            'symbol': self.symbol,
            'exchange': self.exchange,
            'imageURL': self.image_url,
            'AIImageSummary': self.ai_image_summary,
            'AISummary': self.ai_summary,
            'AIAction': self.ai_action,
            'AIConfidence': self.ai_confidence,
            'AIEventTime': self.ai_event_time,
            'AILevels': self.ai_levels,
            'AIAnalysisStatus': self.ai_analysis_status.value if self.ai_analysis_status else None
        }
```

### Step 3: Update Repository Layer

#### SQLAlchemy Repository Implementation
```python
# data/repositories/sqlalchemy_insights.py
from typing import List, Optional, Dict, Any, Tuple
from models.sqlalchemy_models import Insight, db
from core.models import InsightModel, FeedType, AIAnalysisStatus

class SQLAlchemyInsightsRepository:
    def create(self, insight: InsightModel) -> Tuple[int, bool]:
        # Check for duplicates
        existing = self._check_duplicate(insight)
        if existing:
            return (existing.id, False)
        
        # Create new insight
        db_insight = Insight(
            time_fetched=insight.time_fetched,
            time_posted=insight.time_posted,
            type=insight.type,
            title=insight.title,
            content=insight.content,
            symbol=insight.symbol,
            exchange=insight.exchange,
            image_url=insight.image_url,
            ai_image_summary=insight.ai_image_summary,
            ai_summary=insight.ai_summary,
            ai_action=insight.ai_action.value if insight.ai_action else None,
            ai_confidence=insight.ai_confidence,
            ai_event_time=insight.ai_event_time,
            ai_levels=insight.ai_levels,
            ai_analysis_status=insight.ai_analysis_status
        )
        
        db.session.add(db_insight)
        db.session.commit()
        
        return (db_insight.id, True)
    
    def find_all(self, 
                 type_filter: Optional[str] = None,
                 symbol_filter: Optional[str] = None,
                 limit: Optional[int] = None,
                 offset: int = 0) -> List[InsightModel]:
        
        query = Insight.query
        
        if type_filter:
            query = query.filter(Insight.type == FeedType(type_filter))
        
        if symbol_filter:
            query = query.filter(Insight.symbol == symbol_filter)
        
        query = query.order_by(Insight.time_posted.desc())
        
        if offset:
            query = query.offset(offset)
        
        if limit:
            query = query.limit(limit)
        
        insights = query.all()
        return [self._to_model(insight) for insight in insights]
    
    def _to_model(self, db_insight: Insight) -> InsightModel:
        return InsightModel(
            id=db_insight.id,
            type=db_insight.type,
            title=db_insight.title,
            content=db_insight.content,
            symbol=db_insight.symbol,
            exchange=db_insight.exchange,
            time_fetched=db_insight.time_fetched,
            time_posted=db_insight.time_posted,
            image_url=db_insight.image_url,
            ai_image_summary=db_insight.ai_image_summary,
            ai_summary=db_insight.ai_summary,
            ai_action=AIAction(db_insight.ai_action) if db_insight.ai_action else None,
            ai_confidence=db_insight.ai_confidence,
            ai_event_time=db_insight.ai_event_time,
            ai_levels=db_insight.ai_levels,
            ai_analysis_status=db_insight.ai_analysis_status
        )
```

### Step 4: Update Service Layer
Services remain largely unchanged! Just update the repository injection:

```python
# services/insights_service.py
class InsightsService:
    def __init__(self, insights_repo=None):
        if insights_repo is None:
            from data.repositories.sqlalchemy_insights import SQLAlchemyInsightsRepository
            insights_repo = SQLAlchemyInsightsRepository()
        self.insights_repo = insights_repo
    
    # All other methods remain the same!
```

### Step 5: Convert Routes to Flask

#### Web Routes (Views)
```python
# views/web_routes.py
from flask import Blueprint, render_template, request
from services import InsightsService

web_bp = Blueprint('web', __name__)
insights_service = InsightsService()

@web_bp.route('/')
def home():
    insights_data = insights_service.get_insights()
    
    return render_template('index.html', 
                         insights=insights_data,
                         config=get_config())

@web_bp.route('/insight/<int:insight_id>')
def view_insight(insight_id):
    insight_data = insights_service.get_insight_by_id(insight_id)
    
    if not insight_data:
        return redirect('/')
    
    return render_template('detail.html', insight=insight_data)
```

#### API Routes
```python
# api/routes/insights.py
from flask import Blueprint, request, jsonify
from services import InsightsService

insights_bp = Blueprint('insights', __name__)
insights_service = InsightsService()

@insights_bp.route('/insights', methods=['GET'])
def get_insights():
    type_filter = request.args.get('type')
    symbol_filter = request.args.get('symbol')
    limit = request.args.get('limit', type=int)
    offset = request.args.get('offset', 0, type=int)
    
    try:
        insights = insights_service.get_insights(
            type_filter=type_filter,
            symbol_filter=symbol_filter,
            limit=limit,
            offset=offset
        )
        return jsonify(insights)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@insights_bp.route('/insights/<int:insight_id>', methods=['GET'])
def get_insight(insight_id):
    insight_data = insights_service.get_insight_by_id(insight_id)
    
    if not insight_data:
        return jsonify({'error': 'Insight not found'}), 404
    
    return jsonify(insight_data)
```

### Step 6: Database Migration
```bash
# Initialize migration
flask db init

# Create migration
flask db migrate -m "Initial migration"

# Apply migration
flask db upgrade
```

### Step 7: Update Main Entry Point
```python
# main.py
from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8000, debug=True)
```

## 🎨 HTMX Frontend Migration

### Step 1: Add HTMX to Templates

#### Update Base Template
```html
<!-- templates/base.html -->
<head>
    <!-- Existing head content -->
    <script src="https://unpkg.com/htmx.org@1.8.4"></script>
    <script src="https://unpkg.com/hyperscript.org@0.9.7"></script>
</head>
```

### Step 2: Convert JavaScript Interactions to HTMX

#### Table Auto-Refresh
```html
<!-- Before: JavaScript setInterval -->
<div id="insights-table">
    <!-- Table content -->
</div>

<!-- After: HTMX auto-refresh -->
<div id="insights-table" 
     hx-get="/api/insights/partial" 
     hx-trigger="every 10s"
     hx-swap="innerHTML">
    <!-- Table content -->
</div>
```

#### Form Submissions
```html
<!-- Before: JavaScript form handling -->
<form id="scrapingForm">
    <!-- Form fields -->
    <button type="submit">Fetch Insights</button>
</form>

<!-- After: HTMX form -->
<form hx-post="/api/scraping/fetch"
      hx-target="#results"
      hx-indicator="#loading">
    <!-- Form fields -->
    <button type="submit">
        Fetch Insights
        <span id="loading" class="htmx-indicator">Loading...</span>
    </button>
</form>

<div id="results"></div>
```

#### Search Functionality
```html
<!-- Before: JavaScript debounced search -->
<input type="text" id="symbolInput" placeholder="Search symbols...">

<!-- After: HTMX search -->
<input type="text" 
       name="query"
       placeholder="Search symbols..."
       hx-get="/api/symbols/search"
       hx-trigger="keyup changed delay:300ms"
       hx-target="#symbol-suggestions">

<div id="symbol-suggestions"></div>
```

### Step 3: Create Partial Templates

#### Partial Route Handlers
```python
# views/partials.py
from flask import Blueprint, render_template
from services import InsightsService

partials_bp = Blueprint('partials', __name__)

@partials_bp.route('/insights/partial')
def insights_table_partial():
    insights_service = InsightsService()
    insights_data = insights_service.get_insights()
    
    return render_template('partials/insights_table.html', 
                         insights=insights_data)

@partials_bp.route('/symbols/search')
def symbol_search_partial():
    query = request.args.get('query', '')
    # Search logic
    suggestions = search_symbols(query)
    
    return render_template('partials/symbol_suggestions.html',
                         suggestions=suggestions)
```

#### Partial Templates
```html
<!-- templates/partials/insights_table.html -->
{% for insight in insights %}
<tr>
    <td>{{ insight.symbol }}</td>
    <td>{{ insight.title }}</td>
    <td>
        <button hx-delete="/api/insights/{{ insight.id }}"
                hx-target="closest tr"
                hx-swap="outerHTML"
                hx-confirm="Delete this insight?">
            Delete
        </button>
    </td>
</tr>
{% endfor %}
```

## 🔄 RQ/Dramatiq Migration

### Step 1: Setup Redis Queue

#### Install Dependencies
```bash
pip install rq redis dramatiq[redis]
```

#### RQ Implementation
```python
# tasks/rq_tasks.py
from rq import Queue
from redis import Redis
from tasks.handlers import handle_ai_analysis, handle_bulk_analysis

# Setup Redis connection
redis_conn = Redis(host='localhost', port=6379, db=0)
task_queue = Queue(connection=redis_conn)

# Convert handlers to RQ jobs
def queue_ai_analysis(insight_id):
    """Queue AI analysis task"""
    job = task_queue.enqueue(
        handle_ai_analysis,
        {'insight_id': insight_id},
        job_timeout='5m'
    )
    return job.id

def queue_bulk_analysis(symbol=None):
    """Queue bulk analysis task"""
    job = task_queue.enqueue(
        handle_bulk_analysis,
        {'symbol': symbol},
        job_timeout='30m'
    )
    return job.id
```

#### Dramatiq Implementation
```python
# tasks/dramatiq_tasks.py
import dramatiq
from dramatiq.brokers.redis import RedisBroker
from tasks.handlers import handle_ai_analysis, handle_bulk_analysis

# Setup broker
redis_broker = RedisBroker(host="localhost", port=6379, db=0)
dramatiq.set_broker(redis_broker)

@dramatiq.actor
def ai_analysis_task(insight_id):
    """AI analysis task"""
    return handle_ai_analysis({'insight_id': insight_id})

@dramatiq.actor
def bulk_analysis_task(symbol=None):
    """Bulk analysis task"""
    return handle_bulk_analysis({'symbol': symbol})
```

### Step 2: Update Task Service

#### RQ Task Service
```python
# services/rq_task_service.py
from tasks.rq_tasks import queue_ai_analysis, queue_bulk_analysis
from rq import Queue
from redis import Redis

class RQTaskService:
    def __init__(self):
        self.redis_conn = Redis(host='localhost', port=6379, db=0)
        self.queue = Queue(connection=self.redis_conn)
    
    def queue_ai_analysis(self, insight_id):
        return queue_ai_analysis(insight_id)
    
    def queue_bulk_analysis(self, symbol=None):
        return queue_bulk_analysis(symbol)
    
    def get_job_status(self, job_id):
        job = self.queue.fetch_job(job_id)
        if not job:
            return None
        
        return {
            'id': job.id,
            'status': job.get_status(),
            'result': job.result,
            'created_at': job.created_at.isoformat() if job.created_at else None,
            'started_at': job.started_at.isoformat() if job.started_at else None,
            'ended_at': job.ended_at.isoformat() if job.ended_at else None
        }
```

### Step 3: Update API Routes
```python
# api/routes/tasks.py
from services.rq_task_service import RQTaskService

task_service = RQTaskService()

@tasks_bp.route('/ai-analysis', methods=['POST'])
def queue_ai_analysis():
    data = request.get_json()
    insight_id = data.get('insight_id')
    
    job_id = task_service.queue_ai_analysis(insight_id)
    
    return jsonify({
        'success': True,
        'job_id': job_id,
        'message': 'AI analysis queued'
    })

@tasks_bp.route('/jobs/<job_id>/status', methods=['GET'])
def get_job_status(job_id):
    status = task_service.get_job_status(job_id)
    
    if not status:
        return jsonify({'error': 'Job not found'}), 404
    
    return jsonify(status)
```

### Step 4: Worker Process

#### RQ Worker
```python
# worker.py
from rq import Worker
from redis import Redis
from tasks.rq_tasks import redis_conn

if __name__ == '__main__':
    worker = Worker(['default'], connection=redis_conn)
    worker.work()
```

#### Dramatiq Worker
```bash
# Run worker
dramatiq tasks.dramatiq_tasks
```

## 🗄️ PostgreSQL Migration

### Step 1: Update Database Configuration
```python
# config.py
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/finance_insights")
```

### Step 2: Update SQLAlchemy Models
```python
# models/postgresql_models.py
from sqlalchemy.dialects.postgresql import UUID
import uuid

class Insight(db.Model):
    # Use UUID for PostgreSQL
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Use PostgreSQL-specific types
    content = db.Column(db.Text)  # Better for large text
    metadata = db.Column(db.JSON)  # JSON column for flexible data
    
    # Add indexes for performance
    __table_args__ = (
        db.Index('idx_insights_symbol_exchange', 'symbol', 'exchange'),
        db.Index('idx_insights_time_posted', 'time_posted'),
        db.Index('idx_insights_type_status', 'type', 'ai_analysis_status'),
    )
```

### Step 3: Connection Pooling
```python
# app.py
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600
)

app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_size': 10,
    'max_overflow': 20,
    'pool_pre_ping': True,
    'pool_recycle': 3600
}
```

## 🧪 Testing During Migration

### Step 1: Parallel Testing
```python
# tests/test_migration.py
import pytest
from old_app import create_old_app
from new_app import create_new_app

class TestMigrationCompatibility:
    def test_api_responses_match(self):
        """Test that old and new APIs return same data"""
        old_client = create_old_app().test_client()
        new_client = create_new_app().test_client()
        
        old_response = old_client.get('/api/insights')
        new_response = new_client.get('/api/insights')
        
        assert old_response.status_code == new_response.status_code
        # Compare data structures
        assert len(old_response.json) == len(new_response.json)
```

### Step 2: Gradual Migration
```python
# Feature flag approach
ENABLE_NEW_FRAMEWORK = os.getenv('ENABLE_NEW_FRAMEWORK', 'false').lower() == 'true'

def get_insights_service():
    if ENABLE_NEW_FRAMEWORK:
        from services.new_insights_service import InsightsService
    else:
        from services.insights_service import InsightsService
    return InsightsService()
```

## 📋 Migration Checklist

### Pre-Migration
- [ ] Backup production database
- [ ] Set up testing environment
- [ ] Create feature flags for gradual rollout
- [ ] Document current API behavior
- [ ] Set up monitoring and alerting

### During Migration
- [ ] Migrate models and database schema
- [ ] Update repository implementations
- [ ] Convert route handlers
- [ ] Update frontend interactions
- [ ] Test API compatibility
- [ ] Performance testing
- [ ] Security testing

### Post-Migration
- [ ] Remove old code and dependencies
- [ ] Update documentation
- [ ] Update deployment scripts
- [ ] Monitor performance metrics
- [ ] Gather user feedback
- [ ] Plan next optimizations

This migration guide provides comprehensive pathways for transitioning JKB Finance Insights to different technology stacks while maintaining functionality and minimizing downtime.
