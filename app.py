"""
/**
 * 
 *  ┌─────────────────────────────────────┐
 *  │         APP FACTORY                 │
 *  └─────────────────────────────────────┘
 *  FastAPI application factory
 * 
 *  Creates and configures the FastAPI application with all
 *  routes, middleware, and lifecycle management.
 * 
 *  Parameters:
 *  - None
 * 
 *  Returns:
 *  - Configured FastAPI application instance
 * 
 *  Notes:
 *  - Separates web routes from API routes
 *  - Manages application lifecycle
 *  - Configures all middleware and static files
 */
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import asyncio
from typing import Optional

from api import api_router
from views import web_router
from core import get_db_manager
from tasks import HANDLERS, WorkerPool
from debugger import debug_success, debug_info
from config import (
    APP_NAME, APP_VERSION, TASK_WORKER_COUNT
)

# Global worker pool
worker_pool: Optional[WorkerPool] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
     ┌─────────────────────────────────────┐
     │           LIFESPAN                  │
     └─────────────────────────────────────┘
     Application lifespan manager (simplified)
     
     Handles startup and shutdown logic for the application.
    """
    global worker_pool
    
    # Startup logic
    debug_info("Starting JKB Finance Insights...")
    
    # Initialize database
    db_manager = get_db_manager()
    debug_success("Database initialized")
    
    # Start task workers in background (non-blocking)
    worker_pool = WorkerPool(worker_count=TASK_WORKER_COUNT)
    
    # Register all handlers
    for task_type, handler in HANDLERS.items():
        worker_pool.register_handler(task_type, handler)
    
    # Start workers (this should be non-blocking now)
    await worker_pool.start()
    
    debug_success(f"Application started successfully")
    debug_success(f"Workers: {TASK_WORKER_COUNT}")
    
    yield  # Application runs here
    
    # Shutdown logic
    if worker_pool:
        debug_info("Stopping background workers...")
        await worker_pool.stop()
        debug_success("Workers stopped")


def create_app() -> FastAPI:
    """
     ┌─────────────────────────────────────┐
     │         CREATE_APP                  │
     └─────────────────────────────────────┘
     Create and configure FastAPI application
     
     Factory function that creates a fully configured
     FastAPI application with all routes and middleware.
     
     Returns:
     - Configured FastAPI application
    """
    # Create FastAPI app
    app = FastAPI(
        title=APP_NAME,
        description="Financial insights management with AI analysis",
        version=APP_VERSION,
        lifespan=lifespan
    )
    
    # Setup static files
    app.mount("/static", StaticFiles(directory="static"), name="static")
    
    # Include routers
    # Web routes first (for HTML responses)
    app.include_router(web_router)
    # API routes second (for JSON responses)
    app.include_router(api_router)
    
    return app


# Create the application instance
app = create_app()


# Additional API endpoints that don't fit in the modular structure
@app.get("/api/debugger")
async def get_debugger_status():
    """Get current debugger status for frontend"""
    from debugger import debugger
    return debugger.get_current_status()

@app.post("/api/debug-message")
async def send_debug_message(request: dict):
    """Send debug message to centralized debugger"""
    from debugger import debugger
    
    message = request.get('message', '')
    status = request.get('status', 'info')
    
    if message:
        debugger.debug(message, status)
    
    return {"success": True}


@app.get("/api/symbols")
async def get_normalized_symbols():
    """Get a normalized list of unique symbols from insights"""
    from services import SymbolService
    
    symbol_service = SymbolService()
    return symbol_service.get_normalized_symbols()
