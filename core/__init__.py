"""
Core module for JKB Finance Insights

This module contains the core business logic, data models,
and database management functionality.
"""

from .models import (
    FeedType,
    TaskStatus,
    TaskName,
    TaskInfo,
    AIAction,
    InsightModel,
    ScrapedItem,
    AIAnalysisResult
)

from .database import (
    DatabaseConfig,
    DatabaseManager,
    get_db_manager,
    get_db_connection,
    get_db_session
)

__all__ = [
    # Models
    'FeedType',
    'AIAction',
    'InsightModel',
    'ScrapedItem',
    'AIAnalysisResult',
    # Task System
    'TaskStatus',
    'TaskName',
    'TaskInfo',
    # Database
    'DatabaseConfig',
    'DatabaseManager',
    'get_db_manager',
    'get_db_connection',
    'get_db_session'
]



