"""
Task queue system for JKB Finance Insights

This module provides a simple, reusable task queue system
for async processing with database persistence.
"""

# Task system - all async
from .queue import TaskQueue, get_task_queue
from .worker import TaskWorker, WorkerPool
from .handlers import HANDLERS, handle_ai_analysis, handle_bulk_analysis, handle_cleanup

__all__ = [
    # Queue
    'TaskQueue',
    'get_task_queue',
    # Worker
    'TaskWorker', 
    'WorkerPool',
    # Handlers
    'HANDLERS',
    'handle_ai_analysis',
    'handle_bulk_analysis',
    'handle_cleanup'
]



