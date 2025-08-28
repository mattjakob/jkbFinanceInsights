"""
/**
 * 
 *  ┌─────────────────────────────────────┐
 *  │         CONFIGURATION               │
 *  └─────────────────────────────────────┘
 *  Simplified configuration management
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
 */
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Server Configuration
SERVER_HOST = os.getenv("SERVER_HOST", "127.0.0.1")
SERVER_PORT = int(os.getenv("SERVER_PORT", 8000))

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "finance_insights.db")

# Scraper Configuration
SCRAPER_TIMEOUT = int(os.getenv("SCRAPER_TIMEOUT", 30))
SCRAPER_MAX_RETRIES = int(os.getenv("SCRAPER_MAX_RETRIES", 3))
SCRAPER_RETRY_DELAY = int(os.getenv("SCRAPER_RETRY_DELAY", 1))

# AI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4-vision-preview")

# Legacy prompt IDs (for compatibility)
OPENAI_PROMPT_BRIEFSTRATEGY_ID = os.getenv("OPENAI_PROMPT_BRIEFSTRATEGY_ID")
OPENAI_PROMPT_BRIEFSTRATEGY_VERSION_ID = os.getenv("OPENAI_PROMPT_BRIEFSTRATEGY_VERSION_ID")

# Circuit breaker settings
AI_CIRCUIT_BREAKER_THRESHOLD = int(os.getenv("AI_CIRCUIT_BREAKER_THRESHOLD", 3))
AI_CIRCUIT_BREAKER_RESET_MINUTES = int(os.getenv("AI_CIRCUIT_BREAKER_RESET_MINUTES", 60))

# Task Queue Configuration
TASK_WORKER_COUNT = int(os.getenv("TASK_WORKER_COUNT", 3))
TASK_MAX_RETRIES = int(os.getenv("TASK_MAX_RETRIES", 3))
TASK_CLEANUP_DAYS = int(os.getenv("TASK_CLEANUP_DAYS", 7))

# Application Info
APP_NAME = "JKB Finance Insights"
APP_VERSION = "2.0.0"

# Server Management Constants
MAIN_FILE = "main.py"
DEFAULT_PORT = SERVER_PORT
VENV_ACTIVATE = "venv/bin/activate"

# Uvicorn Configuration
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
            "debug": True
        }
    }

def get_config_summary():
    """Get configuration summary for server management"""
    return {
        "server": {
            "host": SERVER_HOST,
            "port": SERVER_PORT,
            "reload": UVICORN_RELOAD,
            "workers": 1
        },
        "database": {
            "url": DATABASE_URL
        },
        "environment": {
            "mode": "development" if UVICORN_RELOAD else "production",
            "debug": True
        },
        "uvicorn": {
            "host": UVICORN_HOST,
            "log_level": UVICORN_LOG_LEVEL
        }
    }
