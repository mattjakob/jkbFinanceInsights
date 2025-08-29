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
from typing import Optional, Dict, Any, List, Tuple
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
            # Check if table exists
            table_exists = conn.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='simple_tasks'
            """).fetchone() is not None
            
            if not table_exists:
                # Create new table with all columns
                conn.execute("""
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
                        entity_id INTEGER
                    )
                """)
            else:
                # Add columns if they don't exist (for migration)
                try:
                    conn.execute("ALTER TABLE simple_tasks ADD COLUMN entity_type TEXT")
                    debug_info("Added entity_type column to simple_tasks")
                except:
                    pass  # Column already exists
                
                try:
                    conn.execute("ALTER TABLE simple_tasks ADD COLUMN entity_id INTEGER")
                    debug_info("Added entity_id column to simple_tasks")
                except:
                    pass  # Column already exists
            
            # Create indexes
            conn.execute("CREATE INDEX IF NOT EXISTS idx_simple_tasks_status ON simple_tasks(status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_simple_tasks_type ON simple_tasks(task_type)")
            
            # Only create entity index if columns exist
            try:
                conn.execute("CREATE INDEX IF NOT EXISTS idx_simple_tasks_entity ON simple_tasks(entity_type, entity_id)")
            except:
                pass  # Columns may not exist in older schemas
    
    def add_task(self, task_type: str, payload: Dict[str, Any], max_retries: int = 3, entity_type: str = None, entity_id: int = None) -> str:
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
        # Extract entity information from payload if not provided
        if not entity_type and task_type == 'ai_analysis' and 'insight_id' in payload:
            entity_type = 'insight'
            entity_id = payload['insight_id']
        
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
                    result, error, entity_type, entity_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data['id'], data['task_type'], data['payload'],
                data['status'], data['retries'], data['max_retries'],
                data['created_at'], data['started_at'], data['completed_at'],
                data['result'], data['error'], entity_type, entity_id
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
    
    def fail_task(self, task_id: str, error: str, permanent: bool = False):
        """
         ┌─────────────────────────────────────┐
         │          FAIL_TASK                  │
         └─────────────────────────────────────┘
         Mark task as failed with retry logic
         
         Parameters:
         - task_id: Task that failed
         - error: Error message
         - permanent: If True, fail immediately without retry
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
            
            # Check for permanent failure or if we should retry
            if not permanent and retries < max_retries:
                # Retry - mark as pending again
                conn.execute("""
                    UPDATE simple_tasks
                    SET status = ?, retries = ?, error = ?, started_at = NULL
                    WHERE id = ?
                """, (TaskStatus.PENDING.value, retries + 1, error, task_id))
                
                debug_warning(f"Task {task_id} failed, retry {retries + 1}/{max_retries}")
            else:
                # Final failure or permanent failure
                conn.execute("""
                    UPDATE simple_tasks
                    SET status = ?, completed_at = ?, error = ?
                    WHERE id = ?
                """, (TaskStatus.FAILED.value, datetime.now().isoformat(), error, task_id))
                
                if permanent:
                    debug_error(f"Task {task_id} permanently failed: {error}")
                else:
                    debug_error(f"Task {task_id} failed after {max_retries} retries")
                
                # Update entity status when task fails
                self._update_entity_status_on_failure(task_id, error)
    
    def _update_entity_status_on_failure(self, task_id: str, error: str):
        """
         ┌─────────────────────────────────────┐
         │   UPDATE_ENTITY_STATUS_ON_FAILURE   │
         └─────────────────────────────────────┘
         Update the status of the entity associated with a failed task
         
         Parameters:
         - task_id: ID of the failed task
         - error: Error message from the task failure
        """
        try:
            with get_db_session() as conn:
                # Get task details including entity information
                task_row = conn.execute("""
                    SELECT task_type, entity_type, entity_id, payload
                    FROM simple_tasks
                    WHERE id = ?
                """, (task_id,)).fetchone()
                
                if not task_row:
                    return
                
                task_type = task_row['task_type']
                entity_type = task_row['entity_type']
                entity_id = task_row['entity_id']
                payload = json.loads(task_row['payload']) if task_row['payload'] else {}
                
                # Update entity status based on task type and entity type
                if entity_type == 'insight' and entity_id:
                    # Update insight AI analysis status to EMPTY so it can be retried
                    conn.execute("""
                        UPDATE insights
                        SET AIAnalysisStatus = ?
                        WHERE id = ?
                    """, ('empty', entity_id))
                    debug_info(f"Updated insight {entity_id} AI status to EMPTY due to task {task_id} failure")
                
                elif entity_type == 'symbol' and task_type == 'ai_report_generation':
                    # For report generation tasks, we need to find the most recent report
                    # and mark it as failed, or create a failed report entry
                    symbol = payload.get('symbol')
                    if symbol:
                        # Try to find existing report for this symbol
                        report_row = conn.execute("""
                            SELECT id FROM reports
                            WHERE symbol = ? AND AIAnalysisStatus = 'completed'
                            ORDER BY timeFetched DESC
                            LIMIT 1
                        """, (symbol,)).fetchone()
                        
                        if report_row:
                            # Update existing report to failed
                            conn.execute("""
                                UPDATE reports
                                SET AIAnalysisStatus = ?
                                WHERE id = ?
                            """, ('failed', report_row['id']))
                            debug_info(f"Updated report {report_row['id']} status to failed due to task {task_id}")
                        else:
                            # Create a failed report entry
                            from datetime import datetime
                            conn.execute("""
                                INSERT INTO reports (timeFetched, symbol, AISummary, AIAction, 
                                                   AIConfidence, AIEventTime, AILevels, AIAnalysisStatus)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                            """, (
                                datetime.now().isoformat(),
                                symbol,
                                f"Failed to generate report: {error}",
                                'HOLD',
                                0.0,
                                None,
                                None,
                                'failed'
                            ))
                            debug_info(f"Created failed report entry for {symbol} due to task {task_id}")
                
        except Exception as e:
            debug_error(f"Failed to update entity status for task {task_id}: {e}")
    
    def _update_entity_status_bulk(self, conn, tasks: List[Dict[str, Any]], error: str):
        """
         ┌─────────────────────────────────────┐
         │    UPDATE_ENTITY_STATUS_BULK        │
         └─────────────────────────────────────┘
         Update the status of multiple entities in a single database connection
         
         Parameters:
         - conn: Database connection to use
         - tasks: List of tasks to update entity status for
         - error: Error message for the status update
        """
        try:
            # Collect all insight IDs and report symbols that need updates
            insight_ids = []
            report_symbols = []
            
            for task in tasks:
                task_type = task['task_type']
                entity_type = task['entity_type']
                entity_id = task['entity_id']
                payload = json.loads(task['payload']) if task['payload'] else {}
                
                if entity_type == 'insight' and entity_id:
                    insight_ids.append(entity_id)
                elif entity_type == 'symbol' and task_type == 'ai_report_generation':
                    symbol = payload.get('symbol')
                    if symbol:
                        report_symbols.append(symbol)
            
            # Bulk update insights
            if insight_ids:
                placeholders = ','.join(['?' for _ in insight_ids])
                conn.execute(f"""
                    UPDATE insights
                    SET AIAnalysisStatus = ?
                    WHERE id IN ({placeholders})
                """, ['failed'] + insight_ids)
                debug_info(f"Bulk updated {len(insight_ids)} insights to failed status")
            
            # Handle report updates
            if report_symbols:
                for symbol in report_symbols:
                    # Try to find existing report for this symbol
                    report_row = conn.execute("""
                        SELECT id FROM reports
                        WHERE symbol = ? AND AIAnalysisStatus = 'completed'
                        ORDER BY timeFetched DESC
                        LIMIT 1
                    """, (symbol,)).fetchone()
                    
                    if report_row:
                        # Update existing report to failed
                        conn.execute("""
                            UPDATE reports
                            SET AIAnalysisStatus = ?
                            WHERE id = ?
                        """, ('failed', report_row['id']))
                        debug_info(f"Updated report {report_row['id']} status to failed for symbol {symbol}")
                    else:
                        # Create a failed report entry
                        from datetime import datetime
                        conn.execute("""
                            INSERT INTO reports (timeFetched, symbol, AISummary, AIAction, 
                                               AIConfidence, AIEventTime, AILevels, AIAnalysisStatus)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            datetime.now().isoformat(),
                            symbol,
                            f"Failed to generate report: {error}",
                            'HOLD',
                            0.0,
                            None,
                            None,
                            'failed'
                        ))
                        debug_info(f"Created failed report entry for {symbol}")
                
        except Exception as e:
            debug_error(f"Failed to bulk update entity status: {e}")
    
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
            
            # Update entity status when task is cancelled
            self._update_entity_status_on_failure(task_id, "Task cancelled")
    
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
    
    def cleanup_old_tasks(self, days: int = 7) -> int:
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
            
            return deleted
    
    def get_orphaned_tasks(self) -> List[Dict[str, Any]]:
        """
         ┌─────────────────────────────────────┐
         │       GET_ORPHANED_TASKS            │
         └─────────────────────────────────────┘
         Find tasks where the referenced entity no longer exists
         
         Returns:
         - List of orphaned tasks
        """
        with get_db_session() as conn:
            # Find tasks with entity references that don't exist
            orphaned = conn.execute("""
                SELECT t.* FROM simple_tasks t
                LEFT JOIN insights i ON t.entity_type = 'insight' AND t.entity_id = i.id
                WHERE t.entity_type IS NOT NULL 
                AND t.entity_id IS NOT NULL
                AND i.id IS NULL
                AND t.status IN (?, ?)
            """, (TaskStatus.PENDING.value, TaskStatus.PROCESSING.value)).fetchall()
            
            return [dict(row) for row in orphaned]
    
    def purge_orphaned_tasks(self) -> int:
        """
         ┌─────────────────────────────────────┐
         │      PURGE_ORPHANED_TASKS           │
         └─────────────────────────────────────┘
         Remove tasks where the referenced entity no longer exists
         
         Returns:
         - Number of tasks purged
        """
        orphaned = self.get_orphaned_tasks()
        purged = 0
        
        with get_db_session() as conn:
            for task in orphaned:
                conn.execute("""
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
                debug_warning(f"Purged orphaned task {task['id']} (type: {task['task_type']})")
        
        if purged > 0:
            debug_info(f"Purged {purged} orphaned tasks")
        
        return purged
    
    def purge_invalid_tasks(self) -> int:
        """
         ┌─────────────────────────────────────┐
         │      PURGE_INVALID_TASKS            │
         └─────────────────────────────────────┘
         Remove invalid tasks including orphaned ones
         
         Returns:
         - Total number of tasks purged
        """
        return self.purge_orphaned_tasks()
    
    def get_stuck_tasks(self, timeout_hours: int = 1) -> List[Dict[str, Any]]:
        """
         ┌─────────────────────────────────────┐
         │        GET_STUCK_TASKS              │
         └─────────────────────────────────────┘
         Find tasks stuck in processing state
         
         Parameters:
         - timeout_hours: Hours before considering task stuck
         
         Returns:
         - List of stuck tasks
        """
        cutoff = datetime.now() - timedelta(hours=timeout_hours)
        
        with get_db_session() as conn:
            stuck = conn.execute("""
                SELECT * FROM simple_tasks
                WHERE status = ?
                AND started_at < ?
            """, (TaskStatus.PROCESSING.value, cutoff.isoformat())).fetchall()
            
            return [dict(row) for row in stuck]
    
    def reset_stuck_tasks(self, timeout_hours: int = 1) -> int:
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
        stuck_tasks = self.get_stuck_tasks(timeout_hours)
        reset_count = 0
        
        with get_db_session() as conn:
            for task in stuck_tasks:
                if task['retries'] < task['max_retries']:
                    # Reset to pending for retry
                    conn.execute("""
                        UPDATE simple_tasks
                        SET status = ?, started_at = NULL, retries = ?
                        WHERE id = ?
                    """, (TaskStatus.PENDING.value, task['retries'] + 1, task['id']))
                    debug_warning(f"Reset stuck task {task['id']} for retry")
                else:
                    # Mark as failed
                    conn.execute("""
                        UPDATE simple_tasks
                        SET status = ?, completed_at = ?, error = ?
                        WHERE id = ?
                    """, (
                        TaskStatus.FAILED.value,
                        datetime.now().isoformat(),
                        "Task timeout after max retries",
                        task['id']
                    ))
                    debug_error(f"Failed stuck task {task['id']} after max retries")
                
                reset_count += 1
        
        if reset_count > 0:
            debug_info(f"Reset {reset_count} stuck tasks")
        
        return reset_count
    
    def get_health_metrics(self) -> Dict[str, Any]:
        """
         ┌─────────────────────────────────────┐
         │       GET_HEALTH_METRICS            │
         └─────────────────────────────────────┘
         Get comprehensive health metrics for the queue
         
         Returns:
         - Dictionary with health metrics
        """
        stats = self.get_stats()
        orphaned = self.get_orphaned_tasks()
        stuck = self.get_stuck_tasks()
        
        # Calculate health score
        total_active = stats.get(TaskStatus.PENDING.value, 0) + stats.get(TaskStatus.PROCESSING.value, 0)
        total_tasks = sum(stats.values())
        
        health_score = 100
        issues = []
        
        # Deduct points for various issues
        if len(stuck) > 0:
            health_score -= min(30, len(stuck) * 10)
            issues.append(f"{len(stuck)} stuck tasks")
        
        if len(orphaned) > 0:
            health_score -= min(20, len(orphaned) * 5)
            issues.append(f"{len(orphaned)} orphaned tasks")
        
        failed_count = stats.get(TaskStatus.FAILED.value, 0)
        if total_tasks > 0 and failed_count / total_tasks > 0.1:
            health_score -= 20
            issues.append(f"High failure rate ({failed_count}/{total_tasks})")
        
        # Determine health status
        if health_score >= 90:
            health_status = "healthy"
        elif health_score >= 70:
            health_status = "warning"
        else:
            health_status = "critical"
        
        return {
            "health_score": max(0, health_score),
            "health_status": health_status,
            "stats": stats,
            "stuck_tasks": len(stuck),
            "orphaned_tasks": len(orphaned),
            "issues": issues,
            "recommendations": self._get_health_recommendations(health_status, issues)
        }
    
    def _get_health_recommendations(self, status: str, issues: List[str]) -> List[str]:
        """Get recommendations based on health status"""
        recommendations = []
        
        if "stuck tasks" in str(issues):
            recommendations.append("Run purge-stuck-tasks to reset stuck tasks")
        
        if "orphaned tasks" in str(issues):
            recommendations.append("Run cleanup to remove orphaned tasks")
        
        if "High failure rate" in str(issues):
            recommendations.append("Check logs for recurring errors")
            recommendations.append("Consider adjusting retry settings")
        
        if status == "critical":
            recommendations.append("Immediate attention required")
        
        return recommendations
    
    def cancel_all_tasks(self) -> int:
        """
         ┌─────────────────────────────────────┐
         │        CANCEL_ALL_TASKS             │
         └─────────────────────────────────────┘
         Cancel all pending, processing, and failed tasks
         
         Returns:
         - Number of tasks cancelled
        """
        with get_db_session() as conn:
            # First, get all tasks that will be cancelled to update their entity status
            tasks_to_cancel = conn.execute("""
                SELECT id, task_type, entity_type, entity_id, payload
                FROM simple_tasks
                WHERE status IN (?, ?, ?)
            """, (
                TaskStatus.PENDING.value,
                TaskStatus.PROCESSING.value,
                TaskStatus.FAILED.value
            )).fetchall()
            
            # Cancel all tasks
            cancelled = conn.execute("""
                UPDATE simple_tasks
                SET status = ?, completed_at = ?, error = ?
                WHERE status IN (?, ?, ?)
            """, (
                TaskStatus.CANCELLED.value,
                datetime.now().isoformat(),
                "Cancelled during queue reset",
                TaskStatus.PENDING.value,
                TaskStatus.PROCESSING.value,
                TaskStatus.FAILED.value
            )).rowcount
            
            if cancelled > 0:
                debug_info(f"Cancelled {cancelled} tasks during queue reset")
                
                # Update entity status for all cancelled tasks in a single transaction
                self._update_entity_status_bulk(conn, tasks_to_cancel, "Task cancelled during queue reset")
            
            return cancelled



