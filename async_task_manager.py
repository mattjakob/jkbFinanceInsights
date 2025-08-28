"""
 ┌─────────────────────────────────────┐
 │      ASYNC_TASK_MANAGER             │
 └─────────────────────────────────────┘
 Robust async task management system for AI analysis

 Provides persistent task tracking, automatic retries, timeout handling,
 and recovery from failures. Ensures AI analysis tasks complete even if
 the user closes the page or the server restarts.

 Features:
 - Persistent task queue in database
 - Automatic retry with exponential backoff
 - Timeout detection and handling
 - Background task processing
 - Status tracking and reporting
 - Graceful shutdown handling
"""

import asyncio
import json
import sqlite3
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import threading
from contextlib import contextmanager

from debugger import debug_info, debug_success, debug_error, debug_warning
from config import AI_WORKER_MAX_RETRIES, AI_WORKER_TIMEOUT_SECONDS


class TaskStatus(Enum):
    """Task status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


@dataclass
class AsyncTask:
    """
     ┌─────────────────────────────────────┐
     │          ASYNCTASK                  │
     └─────────────────────────────────────┘
     Represents an async task in the system
     
     Stores all information needed to process and track an async task,
     including retry information and processing history.
    """
    id: Optional[int] = None
    task_type: str = None
    insight_id: int = None
    status: str = TaskStatus.PENDING.value
    payload: Dict[str, Any] = None
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = AI_WORKER_MAX_RETRIES
    timeout_seconds: int = AI_WORKER_TIMEOUT_SECONDS
    created_at: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    next_retry_at: Optional[str] = None


class AsyncTaskManager:
    """
     ┌─────────────────────────────────────┐
     │       ASYNCTASKMANAGER              │
     └─────────────────────────────────────┘
     Main async task management system
     
     Handles task lifecycle, persistence, retries, and monitoring.
     Runs background workers to process tasks continuously.
    """
    
    def __init__(self, database_path: str = "finance_insights.db", worker_count: int = 3):
        self.database_path = database_path
        self.worker_count = worker_count
        self.running = False
        self.workers = []
        self._initialize_database()
        
    def _initialize_database(self):
        """
         ┌─────────────────────────────────────┐
         │      _INITIALIZE_DATABASE           │
         └─────────────────────────────────────┘
         Create async_tasks table if it doesn't exist
         
         Sets up the persistent storage for async tasks with all necessary
         fields for tracking and recovery.
        """
        with self._get_connection() as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS async_tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_type TEXT NOT NULL,
                    insight_id INTEGER NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    payload TEXT NOT NULL,
                    result TEXT,
                    error_message TEXT,
                    retry_count INTEGER DEFAULT 0,
                    max_retries INTEGER DEFAULT 3,
                    timeout_seconds INTEGER DEFAULT 300,
                    created_at TEXT NOT NULL,
                    started_at TEXT,
                    completed_at TEXT,
                    next_retry_at TEXT,
                    FOREIGN KEY (insight_id) REFERENCES insights(id)
                )
            ''')
            
            # Create indexes for performance
            conn.execute('CREATE INDEX IF NOT EXISTS idx_async_tasks_status ON async_tasks(status)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_async_tasks_insight_id ON async_tasks(insight_id)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_async_tasks_next_retry ON async_tasks(next_retry_at)')
            
            conn.commit()
            
    @contextmanager
    def _get_connection(self):
        """Get database connection with context manager"""
        conn = sqlite3.connect(self.database_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
            
    def create_task(self, task_type: str, insight_id: int, payload: Dict[str, Any], 
                   max_retries: int = 3, timeout_seconds: int = 300) -> int:
        """
         ┌─────────────────────────────────────┐
         │         CREATE_TASK                 │
         └─────────────────────────────────────┘
         Create a new async task
         
         Adds a task to the queue for processing by background workers.
         
         Parameters:
         - task_type: Type of task (e.g., "ai_image_analysis", "ai_summary")
         - insight_id: Related insight ID
         - payload: Task-specific data as dictionary
         - max_retries: Maximum retry attempts
         - timeout_seconds: Task timeout in seconds
         
         Returns:
         - int: Task ID
        """
        task = AsyncTask(
            task_type=task_type,
            insight_id=insight_id,
            payload=payload,
            max_retries=max_retries,
            timeout_seconds=timeout_seconds,
            created_at=datetime.now().isoformat()
        )
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO async_tasks (
                    task_type, insight_id, status, payload, retry_count,
                    max_retries, timeout_seconds, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                task.task_type,
                task.insight_id,
                task.status,
                json.dumps(task.payload),
                task.retry_count,
                task.max_retries,
                task.timeout_seconds,
                task.created_at
            ))
            
            task_id = cursor.lastrowid
            conn.commit()
            
            debug_info(f"Created async task #{task_id} for insight #{insight_id} (type: {task_type})")
            return task_id
            
    def get_pending_tasks(self, limit: int = 10) -> List[AsyncTask]:
        """
         ┌─────────────────────────────────────┐
         │       GET_PENDING_TASKS             │
         └─────────────────────────────────────┘
         Get tasks ready for processing
         
         Retrieves pending tasks and tasks due for retry, ordered by priority.
         
         Parameters:
         - limit: Maximum number of tasks to retrieve
         
         Returns:
         - List of AsyncTask objects
        """
        with self._get_connection() as conn:
            current_time = datetime.now().isoformat()
            
            # Get pending tasks and tasks due for retry
            rows = conn.execute('''
                SELECT * FROM async_tasks
                WHERE (status = ? OR (status = ? AND next_retry_at <= ?))
                ORDER BY created_at ASC
                LIMIT ?
            ''', (TaskStatus.PENDING.value, TaskStatus.FAILED.value, current_time, limit)).fetchall()
            
            tasks = []
            for row in rows:
                task = AsyncTask(
                    id=row['id'],
                    task_type=row['task_type'],
                    insight_id=row['insight_id'],
                    status=row['status'],
                    payload=json.loads(row['payload']),
                    result=json.loads(row['result']) if row['result'] else None,
                    error_message=row['error_message'],
                    retry_count=row['retry_count'],
                    max_retries=row['max_retries'],
                    timeout_seconds=row['timeout_seconds'],
                    created_at=row['created_at'],
                    started_at=row['started_at'],
                    completed_at=row['completed_at'],
                    next_retry_at=row['next_retry_at']
                )
                tasks.append(task)
                
            return tasks
            
    def update_task_status(self, task_id: int, status: TaskStatus, 
                         result: Optional[Dict[str, Any]] = None,
                         error_message: Optional[str] = None):
        """
         ┌─────────────────────────────────────┐
         │      UPDATE_TASK_STATUS             │
         └─────────────────────────────────────┘
         Update task status and related fields
         
         Updates task status, timestamps, and results/errors as appropriate.
         
         Parameters:
         - task_id: Task ID to update
         - status: New status
         - result: Task result (for completed tasks)
         - error_message: Error message (for failed tasks)
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            updates = {'status': status.value}
            
            if status == TaskStatus.PROCESSING:
                updates['started_at'] = datetime.now().isoformat()
            elif status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.TIMEOUT]:
                updates['completed_at'] = datetime.now().isoformat()
                
            if result:
                updates['result'] = json.dumps(result)
            if error_message:
                updates['error_message'] = error_message
                
            # Build update query
            set_clause = ', '.join(f"{k} = ?" for k in updates.keys())
            values = list(updates.values()) + [task_id]
            
            cursor.execute(f'UPDATE async_tasks SET {set_clause} WHERE id = ?', values)
            conn.commit()
            
    def retry_task(self, task: AsyncTask):
        """
         ┌─────────────────────────────────────┐
         │         RETRY_TASK                  │
         └─────────────────────────────────────┘
         Schedule task for retry with exponential backoff
         
         Increments retry count and sets next retry time using exponential
         backoff strategy to avoid overwhelming external services.
         
         Parameters:
         - task: AsyncTask to retry
        """
        task.retry_count += 1
        
        # Exponential backoff: 30s, 60s, 120s, etc.
        backoff_seconds = min(30 * (2 ** (task.retry_count - 1)), 3600)  # Max 1 hour
        next_retry = datetime.now() + timedelta(seconds=backoff_seconds)
        
        with self._get_connection() as conn:
            conn.execute('''
                UPDATE async_tasks 
                SET retry_count = ?, next_retry_at = ?, status = ?
                WHERE id = ?
            ''', (task.retry_count, next_retry.isoformat(), TaskStatus.FAILED.value, task.id))
            conn.commit()
            
        debug_info(f"Task #{task.id} scheduled for retry #{task.retry_count} at {next_retry.isoformat()}")
    
    def postpone_task(self, task: AsyncTask, delay_minutes: int = 10):
        """
         ┌─────────────────────────────────────┐
         │         POSTPONE_TASK               │
         └─────────────────────────────────────┘
         Postpone task without incrementing retry count
         
         Used when external conditions (like circuit breaker) prevent processing.
         
         Parameters:
         - task: AsyncTask to postpone
         - delay_minutes: Minutes to delay before next attempt
        """
        next_retry = datetime.now() + timedelta(minutes=delay_minutes)
        
        with self._get_connection() as conn:
            conn.execute('''
                UPDATE async_tasks 
                SET next_retry_at = ?, status = ?
                WHERE id = ?
            ''', (next_retry.isoformat(), TaskStatus.FAILED.value, task.id))
            conn.commit()
            
        debug_info(f"Task #{task.id} postponed for {delay_minutes} minutes until {next_retry.isoformat()}")
        
    def check_timeouts(self):
        """
         ┌─────────────────────────────────────┐
         │        CHECK_TIMEOUTS               │
         └─────────────────────────────────────┘
         Check for timed out tasks
         
         Identifies tasks that have been processing longer than their timeout
         and marks them as timed out for retry or failure.
        """
        with self._get_connection() as conn:
            current_time = datetime.now()
            
            # Find tasks that have timed out
            rows = conn.execute('''
                SELECT id, started_at, timeout_seconds, retry_count, max_retries
                FROM async_tasks
                WHERE status = ? AND started_at IS NOT NULL
            ''', (TaskStatus.PROCESSING.value,)).fetchall()
            
            for row in rows:
                started_at = datetime.fromisoformat(row['started_at'])
                timeout_delta = timedelta(seconds=row['timeout_seconds'])
                
                if current_time > started_at + timeout_delta:
                    # Task has timed out
                    if row['retry_count'] < row['max_retries']:
                        # Schedule for retry
                        debug_warning(f"Task #{row['id']} timed out, scheduling retry")
                        task = self.get_task(row['id'])
                        self.update_task_status(row['id'], TaskStatus.TIMEOUT, 
                                              error_message="Task timed out")
                        self.retry_task(task)
                    else:
                        # Max retries reached
                        debug_error(f"Task #{row['id']} timed out and max retries reached")
                        self.update_task_status(row['id'], TaskStatus.TIMEOUT,
                                              error_message="Task timed out after max retries")
                        
    def get_task(self, task_id: int) -> Optional[AsyncTask]:
        """Get task by ID"""
        with self._get_connection() as conn:
            row = conn.execute('SELECT * FROM async_tasks WHERE id = ?', (task_id,)).fetchone()
            
            if not row:
                return None
                
            return AsyncTask(
                id=row['id'],
                task_type=row['task_type'],
                insight_id=row['insight_id'],
                status=row['status'],
                payload=json.loads(row['payload']),
                result=json.loads(row['result']) if row['result'] else None,
                error_message=row['error_message'],
                retry_count=row['retry_count'],
                max_retries=row['max_retries'],
                timeout_seconds=row['timeout_seconds'],
                created_at=row['created_at'],
                started_at=row['started_at'],
                completed_at=row['completed_at'],
                next_retry_at=row['next_retry_at']
            )
            
    def cancel_insight_tasks(self, insight_id: int):
        """
         ┌─────────────────────────────────────┐
         │      CANCEL_INSIGHT_TASKS           │
         └─────────────────────────────────────┘
         Cancel all pending tasks for an insight
         
         Used when an insight is deleted or no longer needs processing.
         
         Parameters:
         - insight_id: Insight ID to cancel tasks for
        """
        with self._get_connection() as conn:
            conn.execute('''
                UPDATE async_tasks 
                SET status = ?, completed_at = ?, error_message = ?
                WHERE insight_id = ? AND status IN (?, ?)
            ''', (
                TaskStatus.CANCELLED.value,
                datetime.now().isoformat(),
                "Task cancelled",
                insight_id,
                TaskStatus.PENDING.value,
                TaskStatus.PROCESSING.value
            ))
            conn.commit()
            
    def get_task_stats(self) -> Dict[str, int]:
        """
         ┌─────────────────────────────────────┐
         │        GET_TASK_STATS               │
         └─────────────────────────────────────┘
         Get task statistics
         
         Returns counts of tasks by status for monitoring.
         
         Returns:
         - Dictionary with status counts
        """
        with self._get_connection() as conn:
            stats = {}
            
            rows = conn.execute('''
                SELECT status, COUNT(*) as count
                FROM async_tasks
                GROUP BY status
            ''').fetchall()
            
            for row in rows:
                stats[row['status']] = row['count']
                
            return stats
            
    def cleanup_old_tasks(self, days: int = 7):
        """
         ┌─────────────────────────────────────┐
         │       CLEANUP_OLD_TASKS             │
         └─────────────────────────────────────┘
         Remove old completed/failed tasks
         
         Cleans up task history to prevent database bloat.
         
         Parameters:
         - days: Keep tasks from last N days
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        with self._get_connection() as conn:
            deleted = conn.execute('''
                DELETE FROM async_tasks
                WHERE completed_at < ? AND status IN (?, ?, ?)
            ''', (
                cutoff_date.isoformat(),
                TaskStatus.COMPLETED.value,
                TaskStatus.FAILED.value,
                TaskStatus.CANCELLED.value
            )).rowcount
            
            conn.commit()
            
            if deleted > 0:
                debug_info(f"Cleaned up {deleted} old tasks")


# Global instance
_task_manager: Optional[AsyncTaskManager] = None


def get_task_manager() -> AsyncTaskManager:
    """
     ┌─────────────────────────────────────┐
     │       GET_TASK_MANAGER              │
     └─────────────────────────────────────┘
     Get global task manager instance
     
     Creates singleton instance if not already created.
     
     Returns:
     - AsyncTaskManager instance
    """
    global _task_manager
    if _task_manager is None:
        _task_manager = AsyncTaskManager()
    return _task_manager
