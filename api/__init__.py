"""
API module for JKB Finance Insights

This module contains all API route definitions,
organized by resource type.
"""

from fastapi import APIRouter

# Import routers
from .routes import insights, analysis, scraping, tasks

# Create main API router
api_router = APIRouter()

# Include sub-routers
api_router.include_router(insights.router)
api_router.include_router(analysis.router)
api_router.include_router(scraping.router)
api_router.include_router(tasks.router)

__all__ = [
    'api_router'
]



