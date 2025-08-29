"""
/**
 * 
 *  ┌─────────────────────────────────────┐
 *  │      SIMPLIFIED CONFIGURATION       │
 *  └─────────────────────────────────────┘
 *  Simplified configuration management
 * 
 *  Consolidates all settings into logical groups with
 *  smart defaults to minimize configuration complexity.
 * 
 *  Parameters:
 *  - None
 * 
 *  Returns:
 *  - Configuration constants
 * 
 *  Notes:
 *  - Uses environment variables with smart defaults
 *  - Minimal required configuration
 *  - Logical grouping of related settings
 */
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# =============================================================================
# CORE SETTINGS
# =============================================================================
APP_NAME = os.getenv("APP_NAME", "JKB Finance Insights")
SERVER_HOST = os.getenv("SERVER_HOST", "127.0.0.1")
SERVER_PORT = int(os.getenv("SERVER_PORT", 8000))
DATABASE_URL = os.getenv("DATABASE_URL", "finance_insights.db")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# =============================================================================
# FEATURE TOGGLES
# =============================================================================
FEATURES = {
    "auto_refresh": os.getenv("FEATURES_AUTO_REFRESH", "true").lower() == "true",
    "ai_analysis": os.getenv("FEATURES_AI_ANALYSIS", "true").lower() == "true",
    "debug_mode": os.getenv("FEATURES_DEBUG_MODE", "false").lower() == "true",
    "hot_reload": os.getenv("FEATURES_HOT_RELOAD", "true").lower() == "true"
}

# =============================================================================
# PERFORMANCE SETTINGS
# =============================================================================
PERFORMANCE = {
    "refresh_interval": int(os.getenv("PERFORMANCE_REFRESH_INTERVAL", 10000)),
    "worker_count": int(os.getenv("PERFORMANCE_WORKER_COUNT", 3)),
    "timeout": int(os.getenv("PERFORMANCE_TIMEOUT", 30))
}

# =============================================================================
# DERIVED SETTINGS (Computed from core settings)
# =============================================================================

# Frontend refresh intervals (all based on single setting)
FRONTEND_REFRESH_INTERVALS = {
    "age": 1000,  # Always 1 second for time displays
    "table": PERFORMANCE["refresh_interval"],
    "status": min(2000, PERFORMANCE["refresh_interval"] // 2)  # Half of main interval, max 2s
}

# Application behavior
APP_BEHAVIOR = {
    "reload_delay": 1000,  # Always 1 second
    "max_items": 25,  # Reasonable default
    "search_debounce": 300,  # Standard debounce
    "auto_refresh": FEATURES["auto_refresh"]
}

# Task/Worker settings
TASK_WORKER_COUNT = PERFORMANCE["worker_count"]
TASK_MAX_RETRIES = int(os.getenv("TASK_MAX_RETRIES", 3))
TASK_CLEANUP_DAYS = int(os.getenv("TASK_CLEANUP_DAYS", 7))

# Scraper settings
SCRAPER_TIMEOUT = int(os.getenv("SCRAPER_TIMEOUT", PERFORMANCE["timeout"]))
SCRAPER_MAX_RETRIES = int(os.getenv("SCRAPER_MAX_RETRIES", 3))
SCRAPER_RETRY_DELAY = int(os.getenv("SCRAPER_RETRY_DELAY", 1))

# =============================================================================
# ADVANCED SETTINGS (With defaults)
# =============================================================================

# AI Configuration
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4-vision-preview")
AI_CIRCUIT_BREAKER_THRESHOLD = int(os.getenv("AI_CIRCUIT_BREAKER_THRESHOLD", 3))
AI_CIRCUIT_BREAKER_RESET_MINUTES = int(os.getenv("AI_CIRCUIT_BREAKER_RESET_MINUTES", 60))

# OpenAI Prompt IDs (Required for AI analysis)
OPENAI_PROMPT_BRIEFSTRATEGY_ID = os.getenv("OPENAI_PROMPT_BRIEFSTRATEGY_ID")
OPENAI_PROMPT_BRIEFSTRATEGY_VERSION_ID = os.getenv("OPENAI_PROMPT_BRIEFSTRATEGY_VERSION_ID")

# TradingView Chart
TRADINGVIEW_CHART_HEIGHT = int(os.getenv("TRADINGVIEW_CHART_HEIGHT", 400))
TRADINGVIEW_CHART_INTERVAL = os.getenv("TRADINGVIEW_CHART_INTERVAL", "1")
TRADINGVIEW_CHART_TIMEZONE = os.getenv("TRADINGVIEW_CHART_TIMEZONE", "America/New_York")

# Debug and Logging
DEBUG_MODE = FEATURES["debug_mode"]
LOG_LEVEL = os.getenv("LOG_LEVEL", "info")
DEBUGGER_ENABLED = True  # Always enabled, controlled by debug_mode

# Security
RATE_LIMIT_REQUESTS_PER_MINUTE = int(os.getenv("RATE_LIMIT_REQUESTS_PER_MINUTE", 100))
CORS_ENABLED = os.getenv("CORS_ENABLED", "true").lower() == "true"
CORS_ALLOWED_ORIGINS = os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:8000,http://127.0.0.1:8000").split(",")

# Development
DEV_MODE = FEATURES["debug_mode"]
FRONTEND_HOT_RELOAD = FEATURES["hot_reload"]
SHOW_DETAILED_ERRORS = os.getenv("SHOW_DETAILED_ERRORS", "true").lower() == "true"

# =============================================================================
# UVICORN CONFIGURATION
# =============================================================================
UVICORN_HOST = SERVER_HOST
UVICORN_RELOAD = FEATURES["hot_reload"]
UVICORN_RELOAD_DIR = "."
UVICORN_LOG_LEVEL = LOG_LEVEL
UVICORN_ACCESS_LOG = True

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def get_uvicorn_command(port):
    """Get uvicorn command for server startup"""
    cmd_parts = [
        "uvicorn main:app",
        f"--host {UVICORN_HOST}",
        f"--port {port}",
        f"--log-level {UVICORN_LOG_LEVEL}"
    ]
    
    if UVICORN_RELOAD:
        cmd_parts.extend([
            "--reload",
            f"--reload-dir {UVICORN_RELOAD_DIR}"
        ])
    
    if UVICORN_ACCESS_LOG:
        cmd_parts.append("--access-log")
    
    return " ".join(cmd_parts)

def get_server_info():
    """Get server information summary"""
    return {
        "app_name": APP_NAME,
        "version": "3.0.0",  # Simplified version
        "host": SERVER_HOST,
        "port": SERVER_PORT,
        "database": DATABASE_URL,
        "environment": {
            "mode": "development" if DEV_MODE else "production",
            "debug": DEBUG_MODE,
            "features": FEATURES
        }
    }

def get_config_summary():
    """Get configuration summary for server management"""
    return {
        "server": {
            "host": SERVER_HOST,
            "port": SERVER_PORT,
            "reload": FEATURES["hot_reload"],
            "workers": PERFORMANCE["worker_count"]
        },
        "database": {
            "url": DATABASE_URL
        },
        "environment": {
            "mode": "development" if DEV_MODE else "production",
            "debug": DEBUG_MODE
        },
        "features": FEATURES,
        "performance": PERFORMANCE,
        "frontend": {
            "refresh_intervals": FRONTEND_REFRESH_INTERVALS,
            "auto_refresh": FEATURES["auto_refresh"]
        }
    }

# =============================================================================
# VALIDATION
# =============================================================================

# Ensure required settings are present
if FEATURES["ai_analysis"]:
    missing_ai_config = []
    if not OPENAI_API_KEY:
        missing_ai_config.append("OPENAI_API_KEY")
    if not OPENAI_PROMPT_BRIEFSTRATEGY_ID:
        missing_ai_config.append("OPENAI_PROMPT_BRIEFSTRATEGY_ID")
    if not OPENAI_PROMPT_BRIEFSTRATEGY_VERSION_ID:
        missing_ai_config.append("OPENAI_PROMPT_BRIEFSTRATEGY_VERSION_ID")
    
    if missing_ai_config:
        print(f"WARNING: Missing AI configuration: {', '.join(missing_ai_config)}")
        print("AI analysis features will be disabled.")
        FEATURES["ai_analysis"] = False

# Ensure reasonable performance settings
if PERFORMANCE["refresh_interval"] < 5000:
    print("WARNING: Refresh interval < 5 seconds may impact performance.")
    
if PERFORMANCE["worker_count"] > 10:
    print("WARNING: More than 10 workers may not improve performance.")

# =============================================================================
# SERVER MANAGEMENT CONSTANTS (Unchanged for compatibility)
# =============================================================================
MAIN_FILE = "main.py"
DEFAULT_PORT = SERVER_PORT
VENV_ACTIVATE = "venv/bin/activate"
TASK_CLEANUP_DAYS = 7