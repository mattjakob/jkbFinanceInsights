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
    TradingAction,
    InsightModel,
    ScrapedItem,
    AIAnalysisResult,
    ReportModel
)

from .database import (
    DatabaseConfig,
    DatabaseManager,
    get_db_manager,
    get_db_connection,
    get_db_session,
    get_db_write_connection,
    get_db_write_session
)

__all__ = [
    # Models
    'FeedType',
    'TradingAction',
    'InsightModel',
    'ScrapedItem',
    'AIAnalysisResult',
    'ReportModel',
    # Task System
    'TaskStatus',
    'TaskName',
    'TaskInfo',
    # Database
    'DatabaseConfig',
    'DatabaseManager',
    'get_db_manager',
    'get_db_connection',
    'get_db_session',
    'get_db_write_connection',
    'get_db_write_session'
]



