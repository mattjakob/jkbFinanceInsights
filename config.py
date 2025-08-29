"""
/**
 * 
 *  ┌─────────────────────────────────────┐
 *  │         CONFIGURATION               │
 *  └─────────────────────────────────────┘
 *  Comprehensive configuration management
 * 
 *  Centralizes all configuration with sensible defaults
 *  and clear organization by module.
 * 
 *  Parameters:
 *  - None
 * 
 *  Returns:
 *  - Configuration constants
 * 
 *  Notes:
 *  - Uses environment variables with defaults
 *  - Organized by functional area
 *  - All hardcoded values moved to environment variables
 */
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# =============================================================================
# SERVER CONFIGURATION
# =============================================================================
SERVER_HOST = os.getenv("SERVER_HOST", "127.0.0.1")
SERVER_PORT = int(os.getenv("SERVER_PORT", 8000))

# =============================================================================
# DATABASE CONFIGURATION
# =============================================================================
DATABASE_URL = os.getenv("DATABASE_URL", "finance_insights.db")

# =============================================================================
# SCRAPER CONFIGURATION
# =============================================================================
SCRAPER_TIMEOUT = int(os.getenv("SCRAPER_TIMEOUT", 30))
SCRAPER_MAX_RETRIES = int(os.getenv("SCRAPER_MAX_RETRIES", 3))
SCRAPER_RETRY_DELAY = int(os.getenv("SCRAPER_RETRY_DELAY", 1))

# =============================================================================
# AI CONFIGURATION
# =============================================================================
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4-vision-preview")

# Legacy prompt IDs (for compatibility)
OPENAI_PROMPT_BRIEFSTRATEGY_ID = os.getenv("OPENAI_PROMPT_BRIEFSTRATEGY_ID")
OPENAI_PROMPT_BRIEFSTRATEGY_VERSION_ID = os.getenv("OPENAI_PROMPT_BRIEFSTRATEGY_VERSION_ID")

# Report prompt configuration
OPENAI_PROMPT_REPORT_ID = os.getenv("OPENAI_PROMPT_REPORT_ID")
OPENAI_PROMPT_REPORT_VERSION_ID = os.getenv("OPENAI_PROMPT_REPORT_VERSION_ID")

# Circuit breaker settings
AI_CIRCUIT_BREAKER_THRESHOLD = int(os.getenv("AI_CIRCUIT_BREAKER_THRESHOLD", 3))
AI_CIRCUIT_BREAKER_RESET_MINUTES = int(os.getenv("AI_CIRCUIT_BREAKER_RESET_MINUTES", 60))

# =============================================================================
# TASK QUEUE CONFIGURATION
# =============================================================================
TASK_WORKER_COUNT = int(os.getenv("TASK_WORKERS", os.getenv("TASK_WORKER_COUNT", 3)))
TASK_MAX_RETRIES = int(os.getenv("TASK_MAX_RETRIES", 3))
TASK_PROCESSING_TIMEOUT = int(os.getenv("TASK_PROCESSING_TIMEOUT", 300000))  # Default: 5 minutes in milliseconds
# Validate TASK_PROCESSING_TIMEOUT is reasonable
if TASK_PROCESSING_TIMEOUT < 1000:  # Less than 1 second
    TASK_PROCESSING_TIMEOUT = 1000
    print(f"Warning: TASK_PROCESSING_TIMEOUT too low, setting to minimum 1000ms")
elif TASK_PROCESSING_TIMEOUT > 3600000:  # More than 1 hour
    TASK_PROCESSING_TIMEOUT = 3600000
    print(f"Warning: TASK_PROCESSING_TIMEOUT too high, setting to maximum 3600000ms (1 hour)")
TASK_CLEANUP_DAYS = int(os.getenv("TASK_CLEANUP_DAYS", 7))
TASK_PENDING_TIMEOUT = int(os.getenv("TASK_PENDING_TIMEOUT", 3600000))  # Default: 1 hour in milliseconds
# Validate TASK_PENDING_TIMEOUT is reasonable
if TASK_PENDING_TIMEOUT < 60000:  # Less than 1 minute
    TASK_PENDING_TIMEOUT = 60000
    print(f"Warning: TASK_PENDING_TIMEOUT too low, setting to minimum 60000ms (1 minute)")
elif TASK_PENDING_TIMEOUT > 86400000:  # More than 24 hours
    TASK_PENDING_TIMEOUT = 86400000
    print(f"Warning: TASK_PENDING_TIMEOUT too high, setting to maximum 86400000ms (24 hours)")

# =============================================================================
# FRONTEND REFRESH INTERVALS (in milliseconds)
# =============================================================================
# Core refresh intervals for different UI components
# Support both UI_REFRESH and FRONTEND_UNIFIED_REFRESH_INTERVAL for compatibility
UI_REFRESH = int(os.getenv("UI_REFRESH", os.getenv("FRONTEND_UNIFIED_REFRESH_INTERVAL", 1000)))
FRONTEND_UNIFIED_REFRESH_INTERVAL = UI_REFRESH
FRONTEND_TABLE_REFRESH_INTERVAL = int(os.getenv("FRONTEND_TABLE_REFRESH_INTERVAL", 10000))

FRONTEND_REFRESH_INTERVALS = {
    "age": FRONTEND_UNIFIED_REFRESH_INTERVAL,      # Age display updates
    "table": FRONTEND_TABLE_REFRESH_INTERVAL,      # Table data refresh  
    "status": FRONTEND_UNIFIED_REFRESH_INTERVAL,   # Status bar updates
    "unified": FRONTEND_UNIFIED_REFRESH_INTERVAL   # Unified interval for all UI elements
}

# =============================================================================
# APPLICATION BEHAVIOR SETTINGS
# =============================================================================
# Core application behavior configuration
APP_BEHAVIOR = {
    "reload_delay": int(os.getenv("APP_RELOAD_DELAY", 1000)),
    "max_items": int(os.getenv("APP_MAX_ITEMS", 25)),
    "search_debounce": int(os.getenv("APP_SEARCH_DEBOUNCE", 300)),
    "auto_refresh": os.getenv("APP_AUTO_REFRESH", "true").lower() == "true"
}

# =============================================================================
# TRADINGVIEW CHART CONFIGURATION
# =============================================================================
TRADINGVIEW_CHART_HEIGHT = int(os.getenv("TRADINGVIEW_CHART_HEIGHT", 400))
TRADINGVIEW_CHART_INTERVAL = os.getenv("TRADINGVIEW_CHART_INTERVAL", "1")
TRADINGVIEW_CHART_TIMEZONE = os.getenv("TRADINGVIEW_CHART_TIMEZONE", "America/New_York")

# =============================================================================
# DEBUG AND LOGGING
# =============================================================================
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "info")
DEBUGGER_ENABLED = os.getenv("DEBUGGER_ENABLED", "true").lower() == "true"

# =============================================================================
# SECURITY AND RATE LIMITING
# =============================================================================
RATE_LIMIT_REQUESTS_PER_MINUTE = int(os.getenv("RATE_LIMIT_REQUESTS_PER_MINUTE", 100))
CORS_ENABLED = os.getenv("CORS_ENABLED", "true").lower() == "true"
CORS_ALLOWED_ORIGINS = os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:8000,http://127.0.0.1:8000").split(",")

# =============================================================================
# DEVELOPMENT SETTINGS
# =============================================================================
DEV_MODE = os.getenv("DEV_MODE", "true").lower() == "true"
FRONTEND_HOT_RELOAD = os.getenv("FRONTEND_HOT_RELOAD", "true").lower() == "true"
SHOW_DETAILED_ERRORS = os.getenv("SHOW_DETAILED_ERRORS", "true").lower() == "true"

# =============================================================================
# APPLICATION INFO
# =============================================================================
APP_NAME = "JKB Finance Insights"
APP_VERSION = "2.0.0"

# =============================================================================
# SERVER MANAGEMENT CONSTANTS
# =============================================================================
MAIN_FILE = "main.py"
DEFAULT_PORT = SERVER_PORT
VENV_ACTIVATE = "venv/bin/activate"

# =============================================================================
# UVICORN CONFIGURATION
# =============================================================================
UVICORN_HOST = SERVER_HOST
UVICORN_RELOAD = os.getenv("UVICORN_RELOAD", "true").lower() == "true"  # Default to true
UVICORN_RELOAD_DIR = os.getenv("UVICORN_RELOAD_DIR", ".") or "."  # Ensure it's never empty
UVICORN_LOG_LEVEL = os.getenv("UVICORN_LOG_LEVEL", "info")
UVICORN_ACCESS_LOG = os.getenv("UVICORN_ACCESS_LOG", "true").lower() == "true"  # Default to true

def get_uvicorn_command(port):
    """Get uvicorn command for server startup"""
    cmd_parts = [
        "uvicorn main:app",
        f"--host {UVICORN_HOST}",
        f"--port {port}",
        f"--log-level {UVICORN_LOG_LEVEL}"
    ]
    
    # Always enable auto-reload for development
    if UVICORN_RELOAD:
        cmd_parts.extend([
            "--reload",
            f"--reload-dir {UVICORN_RELOAD_DIR}"
        ])
    
    # Enable access logging for console output
    if UVICORN_ACCESS_LOG:
        cmd_parts.append("--access-log")
    
    return " ".join(cmd_parts)

def get_server_info():
    """Get server information summary"""
    return {
        "app_name": APP_NAME,
        "version": APP_VERSION,
        "host": SERVER_HOST,
        "port": SERVER_PORT,
        "database": DATABASE_URL,
        "environment": {
            "mode": "development" if UVICORN_RELOAD else "production",
            "debug": DEBUG_MODE
        }
    }

def get_config_summary():
    """Get configuration summary for server management"""
    return {
        "server": {
            "host": SERVER_HOST,
            "port": SERVER_PORT,
            "reload": UVICORN_RELOAD,
            "workers": TASK_WORKER_COUNT
        },
        "database": {
            "url": DATABASE_URL
        },
        "environment": {
            "mode": "development" if UVICORN_RELOAD else "production",
            "debug": DEBUG_MODE
        },
        "uvicorn": {
            "host": UVICORN_HOST,
            "log_level": UVICORN_LOG_LEVEL
        },
        "frontend": {
            "age_refresh_interval": FRONTEND_REFRESH_INTERVALS["age"],
            "table_refresh_interval": FRONTEND_REFRESH_INTERVALS["table"],
            "status_refresh_interval": FRONTEND_REFRESH_INTERVALS["status"],
            "auto_refresh": APP_BEHAVIOR["auto_refresh"]
        },
        "app": {
            "reload_delay": APP_BEHAVIOR["reload_delay"],
            "max_items": APP_BEHAVIOR["max_items"],
            "search_debounce": APP_BEHAVIOR["search_debounce"]
        }
    }
