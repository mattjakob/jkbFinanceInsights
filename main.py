"""
/**
 * 
 *  ┌─────────────────────────────────────┐
 *  │         FINANCE INSIGHTS            │
 *  └─────────────────────────────────────┘
 *  Simplified main application entry point
 * 
 *  Uses the refactored modular architecture for cleaner
 *  code organization and better separation of concerns.
 * 
 *  Parameters:
 *  - None
 * 
 *  Returns:
 *  - FastAPI application instance
 * 
 *  Notes:
 *  - All routes are imported from api module
 *  - Background workers managed separately
 */
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
from typing import Optional
import asyncio

from api import api_router
from core import get_db_manager
from tasks import WorkerPool, HANDLERS
from debugger import debug_success, debug_info
from config import SERVER_HOST, SERVER_PORT

# Global worker pool
worker_pool: Optional[WorkerPool] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global worker_pool
    
    # Startup logic
    # Initialize database
    db_manager = get_db_manager()
    debug_success("Database initialized")
    
    # Start task workers
    worker_pool = WorkerPool(worker_count=3)
    
    # Register all handlers
    for task_type, handler in HANDLERS.items():
        worker_pool.register_handler(task_type, handler)
    
    # Start workers in background
    asyncio.create_task(worker_pool.start())
    
    debug_success("Application started successfully")
    
    yield  # Application runs here
    
    # Shutdown logic
    if worker_pool:
        debug_info("Stopping background workers...")
        await worker_pool.stop()
        debug_success("Workers stopped")


# Initialize FastAPI app with lifespan
app = FastAPI(
    title="JKB Finance Insights",
    description="Financial insights management with AI analysis",
    version="2.0.0",
    lifespan=lifespan
)

# Include API routes
app.include_router(api_router)

# Setup templates and static files
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


# Web routes
@app.get("/", response_class=HTMLResponse)
async def home(request: Request, type: Optional[str] = None):
    """
     ┌─────────────────────────────────────┐
     │             HOME                    │
     └─────────────────────────────────────┘
     Display the main web interface
     
     Shows insights table with optional filtering.
    """
    from data import InsightsRepository
    from core import FeedType
    
    repo = InsightsRepository()
    
    # Get insights
    insights = repo.find_all(type_filter=type)
    
    # Convert to dict for template
    insights_data = [insight.to_dict() for insight in insights]
    
    # Get feed types for filter dropdown
    feed_names = [
        {"name": feed_type.value, "description": f"{feed_type.value} feed"}
        for feed_type in FeedType
    ]
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "insights": insights_data,
        "feed_names": feed_names,
        "selected_type": type or ""
    })


@app.get("/insight/{insight_id}", response_class=HTMLResponse)
async def view_insight(request: Request, insight_id: int):
    """
     ┌─────────────────────────────────────┐
     │         VIEW_INSIGHT                │
     └─────────────────────────────────────┘
     Display detailed view of an insight
    """
    from data import InsightsRepository
    
    repo = InsightsRepository()
    insight = repo.get_by_id(insight_id)
    
    if not insight:
        return RedirectResponse(url="/", status_code=404)
    
    return templates.TemplateResponse("detail.html", {
        "request": request,
        "insight": insight.to_dict()
    })


@app.get("/add", response_class=HTMLResponse)
async def add_form(request: Request):
    """Display form for adding insights (testing)"""
    from core import FeedType
    
    feed_names = [
        {"name": feed_type.value, "description": f"{feed_type.value} feed"}
        for feed_type in FeedType
    ]
    
    return templates.TemplateResponse("add.html", {
        "request": request,
        "feed_names": feed_names
    })


@app.get("/edit-insight/{insight_id}", response_class=HTMLResponse)
async def edit_form(request: Request, insight_id: int):
    """Display form for editing an insight"""
    from data import InsightsRepository
    from core import FeedType
    
    repo = InsightsRepository()
    insight = repo.get_by_id(insight_id)
    
    if not insight:
        return RedirectResponse(url="/", status_code=404)
    
    feed_names = [
        {"name": feed_type.value, "description": f"{feed_type.value} feed"}
        for feed_type in FeedType
    ]
    
    return templates.TemplateResponse("edit.html", {
        "request": request,
        "insight": insight.to_dict(),
        "feed_names": feed_names
    })


# Additional API endpoints that don't fit in the modular structure
@app.get("/api/debug-status")
async def get_debug_status():
    """Get current debug status for frontend"""
    from debugger import debugger
    return debugger.get_current_status()


@app.get("/summary")
async def get_summary(
    type_filter: Optional[str] = None,
    symbol_filter: Optional[str] = None
):
    """Get text summary of high-confidence insights"""
    from data import InsightsRepository
    from fastapi.responses import PlainTextResponse
    
    repo = InsightsRepository()
    insights = repo.find_all(type_filter=type_filter, symbol_filter=symbol_filter)
    
    # Filter high confidence
    high_confidence = [
        i for i in insights 
        if i.ai_confidence and i.ai_confidence > 0.5
    ]
    
    if not high_confidence:
        return PlainTextResponse("No insights found with confidence > 50%.")
    
    # Build text summary
    lines = []
    lines.append("JKB FINANCE INSIGHTS SUMMARY (CONFIDENCE > 50%)")
    lines.append("=" * 60)
    
    if type_filter:
        lines.append(f"Filtered by type: {type_filter}")
    if symbol_filter:
        lines.append(f"Filtered by symbol: {symbol_filter}")
    
    lines.append(f"Total insights: {len(high_confidence)}")
    lines.append("")
    
    for insight in high_confidence:
        if insight.symbol:
            lines.append(f"Symbol: {insight.symbol}")
        
        if insight.time_posted:
            lines.append(f"Posted: {insight.time_posted.strftime('%m-%d-%Y %H:%M')}")
        
        if insight.ai_summary:
            lines.append(insight.ai_summary)
        
        if insight.ai_action:
            lines.append(f"Proposed action: {insight.ai_action.value}")
        
        if insight.ai_confidence:
            lines.append(f"Confidence: {insight.ai_confidence:.0%}")
        
        if insight.ai_levels:
            lines.append(f"Levels: {insight.ai_levels}")
        
        if insight.ai_event_time:
            lines.append(f"Event Time: {insight.ai_event_time}")
        
        lines.append("-" * 40)
    
    return PlainTextResponse("\n".join(lines))


if __name__ == "__main__":
    debug_success("Starting Finance Insights server...")
    uvicorn.run(
        "main:app",
        host=SERVER_HOST,
        port=SERVER_PORT,
        reload=True,
        log_level="info"
    )
