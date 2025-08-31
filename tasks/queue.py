"""
/**
 * 
 *  ┌─────────────────────────────────────┐
 *  │       TASK QUEUE V2                 │
 *  └─────────────────────────────────────┘
 *  Improved task queue with better performance
 * 
 *  Addresses database locking issues and improves task
 *  processing flow with async operations and better concurrency.
 * 
 *  Parameters:
 *  - None
 * 
 *  Returns:
 *  - TaskQueue instance
 * 
 *  Notes:
 *  - Uses async database operations
 *  - Implements exponential backoff for retries
 *  - Better handling of concurrent access
 */
"""

import asyncio
import json
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
try:
    import aiosqlite
except ImportError:
    # Fallback to regular sqlite3 if aiosqlite not available
    import sqlite3 as aiosqlite
import threading

from core.models import TaskStatus, TaskName
from debugger import debug_info, debug_error, debug_warning, debug_success
from config import (
    DATABASE_URL, DATABASE_TIMEOUT, DATABASE_WAL_MODE,
    TASK_MAX_RETRIES, TASK_PROCESSING_TIMEOUT, TASK_PENDING_TIMEOUT
)


@dataclass
class Task:
    """Task structure for queue"""
    task_type: str
    payload: Dict[str, Any]
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: TaskStatus = TaskStatus.PENDING
    retries: int = 0
    max_retries: int = 3
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            'id': self.id,
            'task_type': self.task_type,
            'payload': json.dumps(self.payload),
            'status': self.status.value,
            'retries': self.retries,
            'max_retries': self.max_retries,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'result': json.dumps(self.result) if self.result else None,
            'error': self.error
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        """Create from dictionary"""
        return cls(
            id=data['id'],
            task_type=data['task_type'],
            payload=json.loads(data['payload']),
            status=TaskStatus(data['status']),
            retries=data['retries'],
            max_retries=data['max_retries'],
            created_at=datetime.fromisoformat(data['created_at']),
            started_at=datetime.fromisoformat(data['started_at']) if data['started_at'] else None,
            completed_at=datetime.fromisoformat(data['completed_at']) if data['completed_at'] else None,
            result=json.loads(data['result']) if data['result'] else None,
            error=data['error']
        )


class TaskQueue:
    """
     ┌─────────────────────────────────────┐
     │         TASKQUEUE                   │
     └─────────────────────────────────────┘
     Task queue with async operations
     
     Uses async SQLite operations and better concurrency
     control to reduce delays and improve throughput.
    """
    
    _instance = None
    _initialized = False
    _db_pool: List[aiosqlite.Connection] = []
    _pool_size = 5
    _pool_lock = None
    
    def __new__(cls):
        """Singleton pattern"""
        if cls._instance is None:
            cls._instance = super(TaskQueue, cls).__new__(cls)
        return cls._instance
    
    async def initialize(self):
        """Initialize the queue (async version)"""
        if not TaskQueue._initialized:
            await self._initialize_schema()
            await self._setup_connection_pool()
            TaskQueue._initialized = True
    
    async def _setup_connection_pool(self):
        """Setup connection pool for better concurrency"""
        for _ in range(self._pool_size):
            conn = await aiosqlite.connect(
                DATABASE_URL,
                timeout=DATABASE_TIMEOUT
            )
            
            # Enable WAL mode for better concurrency
            if DATABASE_WAL_MODE:
                await conn.execute("PRAGMA journal_mode=WAL")
                await conn.execute("PRAGMA synchronous=NORMAL")
                await conn.execute("PRAGMA busy_timeout=5000")
                await conn.execute("PRAGMA wal_autocheckpoint=1000")
            
            # Enable row factory
            conn.row_factory = aiosqlite.Row
            
            self._db_pool.append(conn)
    
    async def _get_connection(self) -> aiosqlite.Connection:
        """Get a connection from the pool"""
        if self._pool_lock is None:
            self._pool_lock = asyncio.Lock()
        async with self._pool_lock:
            if self._db_pool:
                return self._db_pool.pop()
        
        # Create new connection if pool is empty
        conn = await aiosqlite.connect(
            DATABASE_URL,
            timeout=DATABASE_TIMEOUT
        )
        
        if DATABASE_WAL_MODE:
            await conn.execute("PRAGMA journal_mode=WAL")
            await conn.execute("PRAGMA synchronous=NORMAL")
            await conn.execute("PRAGMA busy_timeout=5000")
        
        conn.row_factory = aiosqlite.Row
        return conn
    
    async def _return_connection(self, conn: aiosqlite.Connection):
        """Return connection to pool"""
        if self._pool_lock is None:
            self._pool_lock = asyncio.Lock()
        async with self._pool_lock:
            if len(self._db_pool) < self._pool_size:
                self._db_pool.append(conn)
            else:
                await conn.close()
    
    async def _execute_with_retry(self, func, max_retries=3):
        """Execute database operation with exponential backoff retry"""
        for attempt in range(max_retries):
            try:
                return await func()
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e) and attempt < max_retries - 1:
                    wait_time = (2 ** attempt) * 0.1  # Exponential backoff
                    debug_warning(f"Database locked, retrying in {wait_time:.2f}s (attempt {attempt + 1}/{max_retries})")
                    await asyncio.sleep(wait_time)
                else:
                    raise
    
    async def _initialize_schema(self):
        """Create tasks table if it doesn't exist"""
        conn = await self._get_connection()
        try:
            # Check if table exists
            cursor = await conn.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='simple_tasks'
            """)
            table_exists = await cursor.fetchone() is not None
            
            if not table_exists:
                await conn.execute("""
                    CREATE TABLE simple_tasks (
                        id TEXT PRIMARY KEY,
                        task_type TEXT NOT NULL,
                        payload TEXT NOT NULL,
                        status TEXT NOT NULL,
                        retries INTEGER DEFAULT 0,
                        max_retries INTEGER DEFAULT 3,
                        created_at TEXT NOT NULL,
                        started_at TEXT,
                        completed_at TEXT,
                        result TEXT,
                        error TEXT,
                        entity_type TEXT,
                        entity_id INTEGER,
                        priority INTEGER DEFAULT 0
                    )
                """)
            else:
                # Add priority column if it doesn't exist
                try:
                    await conn.execute("ALTER TABLE simple_tasks ADD COLUMN priority INTEGER DEFAULT 0")
                    debug_info("Added priority column to simple_tasks")
                except:
                    pass
            
            # Create indexes
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_simple_tasks_status ON simple_tasks(status)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_simple_tasks_type ON simple_tasks(task_type)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_simple_tasks_priority ON simple_tasks(priority DESC, created_at ASC)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_simple_tasks_entity ON simple_tasks(entity_type, entity_id)")
            
            await conn.commit()
        finally:
            await self._return_connection(conn)
    
    async def add_task(self, task_type: str, payload: Dict[str, Any], 
                      max_retries: int = None, entity_type: str = None, 
                      entity_id: int = None, priority: int = 0) -> str:
        """
         ┌─────────────────────────────────────┐
         │          ADD_TASK                   │
         └─────────────────────────────────────┘
         Add a new task to the queue (async)
         
         Parameters:
         - task_type: Type identifier for routing
         - payload: Task-specific data
         - max_retries: Maximum retry attempts
         - priority: Task priority (higher = more important)
         
         Returns:
         - Task ID
        """
        # Extract entity information from payload if not provided
        if not entity_type and task_type == 'ai_analysis' and 'insight_id' in payload:
            entity_type = 'insight'
            entity_id = payload['insight_id']
        
        # Use config value if max_retries not provided
        if max_retries is None:
            max_retries = TASK_MAX_RETRIES
        
        task = Task(
            task_type=task_type,
            payload=payload,
            max_retries=max_retries
        )
        
        async def insert_task():
            conn = await self._get_connection()
            try:
                data = task.to_dict()
                await conn.execute("""
                    INSERT INTO simple_tasks (
                        id, task_type, payload, status, retries,
                        max_retries, created_at, started_at, completed_at,
                        result, error, entity_type, entity_id, priority
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    data['id'], data['task_type'], data['payload'],
                    data['status'], data['retries'], data['max_retries'],
                    data['created_at'], data['started_at'], data['completed_at'],
                    data['result'], data['error'], entity_type, entity_id, priority
                ))
                await conn.commit()
            finally:
                await self._return_connection(conn)
        
        await self._execute_with_retry(insert_task)
        debug_info(f"Task {task.id} created for {task_type}")
        return task.id
    
    async def get_next_task(self) -> Optional[Task]:
        """
         ┌─────────────────────────────────────┐
         │        GET_NEXT_TASK                │
         └─────────────────────────────────────┘
         Get the next pending task (async)
         
         Uses priority and creation time for ordering.
         Implements atomic claim to prevent race conditions.
         
         Returns:
         - Task instance or None
        """
        async def claim_task():
            conn = await self._get_connection()
            try:
                # Use a transaction for atomic claim
                await conn.execute("BEGIN IMMEDIATE")
                
                # Find next task (priority first, then oldest)
                cursor = await conn.execute("""
                    SELECT * FROM simple_tasks
                    WHERE status = ?
                    ORDER BY priority DESC, created_at ASC
                    LIMIT 1
                """, (TaskStatus.PENDING.value,))
                
                row = await cursor.fetchone()
                if not row:
                    await conn.rollback()
                    return None
                
                # Claim the task
                start_time = datetime.now().isoformat()
                await conn.execute("""
                    UPDATE simple_tasks
                    SET status = ?, started_at = ?
                    WHERE id = ? AND status = ?
                """, (
                    TaskStatus.PROCESSING.value,
                    start_time,
                    row['id'],
                    TaskStatus.PENDING.value
                ))
                
                if conn.total_changes == 0:
                    await conn.rollback()
                    return None
                
                await conn.commit()
                
                # Convert to Task object
                task_dict = dict(row)
                task = Task.from_dict(task_dict)
                task.status = TaskStatus.PROCESSING
                task.started_at = datetime.now()
                
                return task
                
            except Exception as e:
                await conn.rollback()
                raise
            finally:
                await self._return_connection(conn)
        
        return await self._execute_with_retry(claim_task)
    
    async def complete_task(self, task_id: str, result: Optional[Dict[str, Any]] = None):
        """Complete a task (async)"""
        async def update_task():
            conn = await self._get_connection()
            try:
                # Get task type for logging
                cursor = await conn.execute(
                    "SELECT task_type FROM simple_tasks WHERE id = ?",
                    (task_id,)
                )
                row = await cursor.fetchone()
                task_type = row['task_type'] if row else 'unknown'
                
                await conn.execute("""
                    UPDATE simple_tasks
                    SET status = ?, completed_at = ?, result = ?
                    WHERE id = ?
                """, (
                    TaskStatus.COMPLETED.value,
                    datetime.now().isoformat(),
                    json.dumps(result) if result else None,
                    task_id
                ))
                await conn.commit()
                
                debug_success(f"Task {task_id} complete ({task_type})")
                
            finally:
                await self._return_connection(conn)
        
        await self._execute_with_retry(update_task)
    
    async def fail_task(self, task_id: str, error: str, permanent: bool = False):
        """Fail a task with retry logic (async)"""
        async def update_task():
            conn = await self._get_connection()
            try:
                # Get current task state
                cursor = await conn.execute(
                    "SELECT retries, max_retries, entity_type, entity_id FROM simple_tasks WHERE id = ?",
                    (task_id,)
                )
                row = await cursor.fetchone()
                
                if not row:
                    return
                
                retries = row['retries']
                max_retries = row['max_retries']
                
                # Check for permanent failure or if we should retry
                if not permanent and retries < max_retries:
                    # Retry with exponential backoff on priority
                    new_priority = -retries  # Lower priority for retries
                    await conn.execute("""
                        UPDATE simple_tasks
                        SET status = ?, retries = ?, error = ?, started_at = NULL, priority = ?
                        WHERE id = ?
                    """, (TaskStatus.PENDING.value, retries + 1, error, new_priority, task_id))
                    
                    debug_warning(f"Task {task_id} failed, retry {retries + 1}/{max_retries}")
                else:
                    # Final failure
                    await conn.execute("""
                        UPDATE simple_tasks
                        SET status = ?, completed_at = ?, error = ?
                        WHERE id = ?
                    """, (TaskStatus.FAILED.value, datetime.now().isoformat(), error, task_id))
                    
                    if permanent:
                        debug_error(f"Task {task_id} permanently failed: {error}")
                    else:
                        debug_error(f"Task {task_id} failed after {max_retries} retries")
                    
                    # Update entity status if needed
                    if row['entity_type'] == 'insight' and row['entity_id']:
                        await self._update_entity_status(conn, row['entity_id'], TaskStatus.FAILED)
                
                await conn.commit()
                
            finally:
                await self._return_connection(conn)
        
        await self._execute_with_retry(update_task)
    
    async def _update_entity_status(self, conn: aiosqlite.Connection, entity_id: int, status: TaskStatus):
        """Update entity status"""
        try:
            await conn.execute("""
                UPDATE insights
                SET TaskStatus = ?
                WHERE id = ?
            """, (status.value, entity_id))
        except Exception as e:
            debug_error(f"Failed to update entity status: {e}")
    
    async def get_stats(self) -> Dict[str, int]:
        """Get task statistics (async)"""
        conn = await self._get_connection()
        try:
            stats = {
                'pending': 0,
                'processing': 0,
                'completed': 0,
                'failed': 0,
                'cancelled': 0
            }
            
            cursor = await conn.execute("""
                SELECT status, COUNT(*) as count
                FROM simple_tasks
                GROUP BY status
            """)
            
            async for row in cursor:
                stats[row['status']] = row['count']
            
            return stats
            
        finally:
            await self._return_connection(conn)
    
    async def cleanup_old_tasks(self, days: int = 7) -> int:
        """Remove old completed/failed tasks (async)"""
        cutoff = datetime.now() - timedelta(days=days)
        
        async def delete_tasks():
            conn = await self._get_connection()
            try:
                await conn.execute("""
                    DELETE FROM simple_tasks
                    WHERE completed_at < ? 
                    AND status IN (?, ?, ?)
                """, (
                    cutoff.isoformat(),
                    TaskStatus.COMPLETED.value,
                    TaskStatus.FAILED.value,
                    TaskStatus.CANCELLED.value
                ))
                
                deleted = conn.total_changes
                await conn.commit()
                
                if deleted > 0:
                    debug_info(f"Cleaned up {deleted} old tasks")
                
                return deleted
                
            finally:
                await self._return_connection(conn)
        
        return await self._execute_with_retry(delete_tasks)
    
    async def cleanup_stale_pending_tasks(self, timeout_ms: Optional[int] = None) -> int:
        """
         ┌─────────────────────────────────────┐
         │    CLEANUP_STALE_PENDING_TASKS     │
         └─────────────────────────────────────┘
         Clean up pending tasks that have exceeded timeout
         
         Parameters:
         - timeout_ms: Timeout in milliseconds (uses TASK_PENDING_TIMEOUT if not provided)
         
         Returns:
         - Number of tasks cleaned up
        """
        if timeout_ms is None:
            from config import TASK_PENDING_TIMEOUT
            timeout_ms = TASK_PENDING_TIMEOUT
            
        timeout_seconds = timeout_ms / 1000.0
        cutoff = datetime.now() - timedelta(seconds=timeout_seconds)
        
        async def cleanup_tasks():
            conn = await self._get_connection()
            try:
                # Find stale pending tasks
                cursor = await conn.execute("""
                    SELECT id, entity_type, entity_id FROM simple_tasks
                    WHERE status = ? AND created_at < ?
                """, (TaskStatus.PENDING.value, cutoff.isoformat()))
                
                stale_tasks = await cursor.fetchall()
                
                if not stale_tasks:
                    return 0
                
                # Update tasks to CANCELLED
                task_ids = [task['id'] for task in stale_tasks]
                placeholders = ','.join(['?' for _ in task_ids])
                await conn.execute(f"""
                    UPDATE simple_tasks
                    SET status = ?, completed_at = ?, error = ?
                    WHERE id IN ({placeholders})
                """, [TaskStatus.CANCELLED.value, datetime.now().isoformat(), 
                      f"Task cancelled after {timeout_seconds}s pending timeout"] + task_ids)
                
                await conn.commit()
                return len(stale_tasks)
                
            finally:
                await self._return_connection(conn)
        
        return await self._execute_with_retry(cleanup_tasks)
    
    async def reset_stuck_tasks(self, timeout_hours: int = 1) -> int:
        """
         ┌─────────────────────────────────────┐
         │       RESET_STUCK_TASKS             │
         └─────────────────────────────────────┘
         Reset tasks stuck in processing state
         
         Parameters:
         - timeout_hours: Hours before considering task stuck
         
         Returns:
         - Number of tasks reset
        """
        cutoff = datetime.now() - timedelta(hours=timeout_hours)
        
        async def reset_tasks():
            conn = await self._get_connection()
            try:
                # Find stuck tasks
                cursor = await conn.execute("""
                    SELECT * FROM simple_tasks
                    WHERE status = ? AND started_at < ?
                """, (TaskStatus.PROCESSING.value, cutoff.isoformat()))
                
                stuck_tasks = await cursor.fetchall()
                reset_count = 0
                
                for task in stuck_tasks:
                    if task['retries'] < task['max_retries']:
                        # Reset to pending for retry
                        await conn.execute("""
                            UPDATE simple_tasks
                            SET status = ?, started_at = NULL, retries = ?
                            WHERE id = ?
                        """, (TaskStatus.PENDING.value, task['retries'] + 1, task['id']))
                    else:
                        # Mark as failed
                        await conn.execute("""
                            UPDATE simple_tasks
                            SET status = ?, completed_at = ?, error = ?
                            WHERE id = ?
                        """, (
                            TaskStatus.FAILED.value,
                            datetime.now().isoformat(),
                            "Task timeout after max retries",
                            task['id']
                        ))
                    
                    reset_count += 1
                
                await conn.commit()
                return reset_count
                
            finally:
                await self._return_connection(conn)
        
        return await self._execute_with_retry(reset_tasks)
    
    async def cancel_all_tasks(self) -> int:
        """
         ┌─────────────────────────────────────┐
         │        CANCEL_ALL_TASKS             │
         └─────────────────────────────────────┘
         Cancel all pending and processing tasks
         
         Returns:
         - Number of tasks cancelled
        """
        async def cancel_tasks():
            conn = await self._get_connection()
            try:
                # Cancel all active tasks
                result = await conn.execute("""
                    UPDATE simple_tasks
                    SET status = ?, completed_at = ?, error = ?
                    WHERE status IN (?, ?)
                """, (
                    TaskStatus.CANCELLED.value,
                    datetime.now().isoformat(),
                    "Cancelled during queue reset",
                    TaskStatus.PENDING.value,
                    TaskStatus.PROCESSING.value
                ))
                
                await conn.commit()
                return result.rowcount
                
            finally:
                await self._return_connection(conn)
        
        return await self._execute_with_retry(cancel_tasks)
    
    async def purge_invalid_tasks(self) -> int:
        """
         ┌─────────────────────────────────────┐
         │      PURGE_INVALID_TASKS            │
         └─────────────────────────────────────┘
         Remove invalid tasks including orphaned ones
         
         Returns:
         - Number of tasks purged
        """
        async def purge_tasks():
            conn = await self._get_connection()
            try:
                # Find orphaned tasks
                cursor = await conn.execute("""
                    SELECT t.* FROM simple_tasks t
                    LEFT JOIN insights i ON t.entity_type = 'insight' AND t.entity_id = i.id
                    WHERE t.entity_type IS NOT NULL 
                    AND t.entity_id IS NOT NULL
                    AND i.id IS NULL
                    AND t.status IN (?, ?)
                """, (TaskStatus.PENDING.value, TaskStatus.PROCESSING.value))
                
                orphaned = await cursor.fetchall()
                purged = 0
                
                for task in orphaned:
                    await conn.execute("""
                        UPDATE simple_tasks
                        SET status = ?, completed_at = ?, error = ?
                        WHERE id = ?
                    """, (
                        TaskStatus.CANCELLED.value,
                        datetime.now().isoformat(),
                        "Referenced entity no longer exists",
                        task['id']
                    ))
                    purged += 1
                
                await conn.commit()
                return purged
                
            finally:
                await self._return_connection(conn)
        
        return await self._execute_with_retry(purge_tasks)
    
    async def get_health_metrics(self) -> Dict[str, Any]:
        """
         ┌─────────────────────────────────────┐
         │       GET_HEALTH_METRICS            │
         └─────────────────────────────────────┘
         Get basic health metrics for the queue
         
         Returns:
         - Dictionary with health metrics
        """
        stats = await self.get_stats()
        total_tasks = sum(stats.values())
        failed_count = stats.get('failed', 0)
        
        # Simple health check
        health_status = "critical" if total_tasks > 0 and failed_count / total_tasks > 0.2 else "healthy"
        
        return {
            "health_status": health_status,
            "stats": stats,
            "total_tasks": total_tasks,
            "failure_rate": failed_count / total_tasks if total_tasks > 0 else 0
        }
    
    async def close(self):
        """Close all connections in the pool"""
        if self._pool_lock is None:
            self._pool_lock = asyncio.Lock()
        async with self._pool_lock:
            for conn in self._db_pool:
                await conn.close()
            self._db_pool.clear()


# Global queue instance
_global_queue: Optional[TaskQueue] = None


async def get_task_queue() -> TaskQueue:
    """
     ┌─────────────────────────────────────┐
     │        GET_TASK_QUEUE               │
     └─────────────────────────────────────┘
     Get the singleton task queue instance
     
     Returns:
     - TaskQueue singleton instance
     
     Notes:
     - Must be called from async context
     - Automatically initializes on first use
    """
    global _global_queue
    if _global_queue is None:
        _global_queue = TaskQueue()
        await _global_queue.initialize()
    return _global_queue
