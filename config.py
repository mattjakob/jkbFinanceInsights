"""
 ┌─────────────────────────────────────┐
 │            CONFIG                   │
 └─────────────────────────────────────┘
 Configuration management for JKB Finance Insights
 
 Centralizes all environment variable configuration and provides
 default values for the application.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Server Configuration
SERVER_HOST = os.getenv("SERVER_HOST", "127.0.0.1")
SERVER_PORT = int(os.getenv("SERVER_PORT", 8000))
SERVER_RELOAD = os.getenv("SERVER_RELOAD", "true").lower() == "true"
SERVER_WORKERS = int(os.getenv("SERVER_WORKERS", 1))

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "finance_insights.db")

# Environment
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
DEBUG = os.getenv("DEBUG", "true").lower() == "true"

# Uvicorn Configuration
UVICORN_HOST = os.getenv("UVICORN_HOST", "127.0.0.1")
UVICORN_PORT = int(os.getenv("UVICORN_PORT", 8000))
UVICORN_RELOAD = os.getenv("UVICORN_RELOAD", "true").lower() == "true"
UVICORN_RELOAD_DIR = os.getenv("UVICORN_RELOAD_DIR", ".")
UVICORN_LOG_LEVEL = os.getenv("UVICORN_LOG_LEVEL", "info")

# Application Configuration
APP_NAME = "JKB Finance Insights"
MAIN_FILE = "main.py"
VENV_ACTIVATE = ".venv/bin/activate"

# Legacy compatibility
DEFAULT_PORT = SERVER_PORT

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", None)
OPENAI_SUMMARY_MODEL = os.getenv("OPENAI_SUMMARY_MODEL", "gpt-4-vision-preview")
OPENAI_PROMPT1_ID = os.getenv("OPENAI_PROMPT1_ID", None)
OPENAI_PROMPT1_VERSION_ID = os.getenv("OPENAI_PROMPT1_VERSION_ID", None)
OPENAI_PROMPT2_ID = os.getenv("OPENAI_PROMPT2_ID", None)
OPENAI_PROMPT2_VERSION_ID = os.getenv("OPENAI_PROMPT2_VERSION_ID", None)

def get_config_summary():
    """Get a summary of current configuration"""
    return {
        "server": {
            "host": SERVER_HOST,
            "port": SERVER_PORT,
            "reload": SERVER_RELOAD,
            "workers": SERVER_WORKERS
        },
        "database": {
            "url": DATABASE_URL
        },
        "environment": {
            "mode": ENVIRONMENT,
            "debug": DEBUG
        },
        "uvicorn": {
            "host": UVICORN_HOST,
            "port": UVICORN_PORT,
            "reload": UVICORN_RELOAD,
            "reload_dir": UVICORN_RELOAD_DIR,
            "log_level": UVICORN_LOG_LEVEL
        }
    }

def get_uvicorn_command(port=None):
    """Get the uvicorn command for development mode"""
    if port is None:
        port = UVICORN_PORT
    
    return f"uvicorn main:app --host {UVICORN_HOST} --port {port} --reload --reload-dir {UVICORN_RELOAD_DIR} --log-level {UVICORN_LOG_LEVEL}"

def get_server_info():
    """Get basic server information"""
    return {
        "name": APP_NAME,
        "main_file": MAIN_FILE,
        "venv_activate": VENV_ACTIVATE,
        "default_port": DEFAULT_PORT
    }
