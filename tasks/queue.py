"""
/**
 * 
 *  ┌─────────────────────────────────────┐
 *  │          TASK QUEUE                 │
 *  └─────────────────────────────────────┘
 *  Simple task queue implementation
 * 
 *  Provides a lightweight task queue system for async processing
 *  with database persistence and retry logic.
 * 
 *  Parameters:
 *  - None
 * 
 *  Returns:
 *  - TaskQueue instance
 * 
 *  Notes:
 *  - Uses SQLite for persistence
 *  - Supports retries and timeouts
 */
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, Dict, Any, List
import json
import uuid

from core import get_db_session
from debugger import debug_info, debug_error, debug_warning


class TaskStatus(str, Enum):
    """Task lifecycle states"""
    PENDING = "pending"
    PROCESSING = "processing" 
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Task:
    """
     ┌─────────────────────────────────────┐
     │             TASK                    │
     └─────────────────────────────────────┘
     Represents a task in the queue
     
     Simple data structure for task information.
    """
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
        data = asdict(self)
        # Convert enums and datetimes
        data['status'] = self.status.value
        data['created_at'] = self.created_at.isoformat()
        data['started_at'] = self.started_at.isoformat() if self.started_at else None
        data['completed_at'] = self.completed_at.isoformat() if self.completed_at else None
        data['payload'] = json.dumps(self.payload)
        data['result'] = json.dumps(self.result) if self.result else None
        return data
    
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
     │          TASKQUEUE                  │
     └─────────────────────────────────────┘
     Simple task queue with database persistence
     
     Manages task lifecycle with minimal complexity.
    """
    
    def __init__(self):
        self._initialize_schema()
    
    def _initialize_schema(self):
        """Create tasks table if it doesn't exist"""
        with get_db_session() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS simple_tasks (
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
                    error TEXT
                )
            """)
            
            # Create indexes
            conn.execute("CREATE INDEX IF NOT EXISTS idx_simple_tasks_status ON simple_tasks(status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_simple_tasks_type ON simple_tasks(task_type)")
    
    def add_task(self, task_type: str, payload: Dict[str, Any], max_retries: int = 3) -> str:
        """
         ┌─────────────────────────────────────┐
         │          ADD_TASK                   │
         └─────────────────────────────────────┘
         Add a new task to the queue
         
         Parameters:
         - task_type: Type identifier for routing
         - payload: Task-specific data
         - max_retries: Maximum retry attempts
         
         Returns:
         - Task ID
        """
        task = Task(
            task_type=task_type,
            payload=payload,
            max_retries=max_retries
        )
        
        with get_db_session() as conn:
            data = task.to_dict()
            conn.execute("""
                INSERT INTO simple_tasks (
                    id, task_type, payload, status, retries,
                    max_retries, created_at, started_at, completed_at,
                    result, error
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data['id'], data['task_type'], data['payload'],
                data['status'], data['retries'], data['max_retries'],
                data['created_at'], data['started_at'], data['completed_at'],
                data['result'], data['error']
            ))
        
        debug_info(f"Added task {task.id} of type {task_type}")
        return task.id
    
    def get_next_task(self) -> Optional[Task]:
        """
         ┌─────────────────────────────────────┐
         │        GET_NEXT_TASK                │
         └─────────────────────────────────────┘
         Get the next pending task
         
         Returns the oldest pending task and marks it
         as processing.
         
         Returns:
         - Task instance or None
        """
        with get_db_session() as conn:
            # Find oldest pending task
            row = conn.execute("""
                SELECT * FROM simple_tasks
                WHERE status = ?
                ORDER BY created_at ASC
                LIMIT 1
            """, (TaskStatus.PENDING.value,)).fetchone()
            
            if not row:
                return None
            
            # Mark as processing
            conn.execute("""
                UPDATE simple_tasks
                SET status = ?, started_at = ?
                WHERE id = ?
            """, (TaskStatus.PROCESSING.value, datetime.now().isoformat(), row['id']))
            
            # Return task
            task = Task.from_dict(dict(row))
            task.status = TaskStatus.PROCESSING
            task.started_at = datetime.now()
            
            debug_info(f"Processing task {task.id} of type {task.task_type}")
            return task
    
    def complete_task(self, task_id: str, result: Optional[Dict[str, Any]] = None):
        """
         ┌─────────────────────────────────────┐
         │        COMPLETE_TASK                │
         └─────────────────────────────────────┘
         Mark task as completed
         
         Parameters:
         - task_id: Task to complete
         - result: Optional result data
        """
        with get_db_session() as conn:
            conn.execute("""
                UPDATE simple_tasks
                SET status = ?, completed_at = ?, result = ?
                WHERE id = ?
            """, (
                TaskStatus.COMPLETED.value,
                datetime.now().isoformat(),
                json.dumps(result) if result else None,
                task_id
            ))
        
        debug_info(f"Completed task {task_id}")
    
    def fail_task(self, task_id: str, error: str):
        """
         ┌─────────────────────────────────────┐
         │          FAIL_TASK                  │
         └─────────────────────────────────────┘
         Mark task as failed with retry logic
         
         Parameters:
         - task_id: Task that failed
         - error: Error message
        """
        with get_db_session() as conn:
            # Get current task state
            row = conn.execute(
                "SELECT retries, max_retries FROM simple_tasks WHERE id = ?",
                (task_id,)
            ).fetchone()
            
            if not row:
                return
            
            retries = row['retries']
            max_retries = row['max_retries']
            
            if retries < max_retries:
                # Retry - mark as pending again
                conn.execute("""
                    UPDATE simple_tasks
                    SET status = ?, retries = ?, error = ?, started_at = NULL
                    WHERE id = ?
                """, (TaskStatus.PENDING.value, retries + 1, error, task_id))
                
                debug_warning(f"Task {task_id} failed, retry {retries + 1}/{max_retries}")
            else:
                # Final failure
                conn.execute("""
                    UPDATE simple_tasks
                    SET status = ?, completed_at = ?, error = ?
                    WHERE id = ?
                """, (TaskStatus.FAILED.value, datetime.now().isoformat(), error, task_id))
                
                debug_error(f"Task {task_id} failed after {max_retries} retries")
    
    def cancel_task(self, task_id: str):
        """Cancel a pending task"""
        with get_db_session() as conn:
            conn.execute("""
                UPDATE simple_tasks
                SET status = ?, completed_at = ?, error = ?
                WHERE id = ? AND status = ?
            """, (
                TaskStatus.CANCELLED.value,
                datetime.now().isoformat(),
                "Task cancelled",
                task_id,
                TaskStatus.PENDING.value
            ))
    
    def get_stats(self) -> Dict[str, int]:
        """Get task statistics"""
        with get_db_session() as conn:
            stats = {}
            
            rows = conn.execute("""
                SELECT status, COUNT(*) as count
                FROM simple_tasks
                GROUP BY status
            """).fetchall()
            
            for row in rows:
                stats[row['status']] = row['count']
            
            return stats
    
    def cleanup_old_tasks(self, days: int = 7):
        """Remove old completed/failed tasks"""
        cutoff = datetime.now() - timedelta(days=days)
        
        with get_db_session() as conn:
            deleted = conn.execute("""
                DELETE FROM simple_tasks
                WHERE completed_at < ? 
                AND status IN (?, ?, ?)
            """, (
                cutoff.isoformat(),
                TaskStatus.COMPLETED.value,
                TaskStatus.FAILED.value,
                TaskStatus.CANCELLED.value
            )).rowcount
            
            if deleted > 0:
                debug_info(f"Cleaned up {deleted} old tasks")



