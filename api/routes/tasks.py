"""
/**
 * 
 *  ┌─────────────────────────────────────┐
 *  │          TASKS ROUTES               │
 *  └─────────────────────────────────────┘
 *  API routes for task management
 * 
 *  Provides endpoints for monitoring and managing
 *  background tasks in the queue system.
 * 
 *  Parameters:
 *  - None
 * 
 *  Returns:
 *  - FastAPI router with task endpoints
 * 
 *  Notes:
 *  - Read-only operations for task monitoring
 *  - Management operations for cleanup
 */
"""

from fastapi import APIRouter, HTTPException, Response
from typing import Dict, Any
from datetime import datetime

from tasks import TaskQueue
from debugger import debug_info, debug_error, debug_success

# Create router
router = APIRouter(prefix="/api/tasks", tags=["tasks"])

# Initialize task queue
task_queue = TaskQueue()


@router.get("/stats")
async def get_task_stats():
    """
     ┌─────────────────────────────────────┐
     │        GET_TASK_STATS               │
     └─────────────────────────────────────┘
     Get task queue statistics
     
     Returns counts of tasks by status.
    """
    try:
        stats = task_queue.get_stats()
        
        return {
            "stats": stats,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        debug_error(f"Error getting task stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status", response_class=Response)
async def get_tasks_status():
    """
     ┌─────────────────────────────────────┐
     │       GET_TASKS_STATUS              │
     └─────────────────────────────────────┘
     Get detailed task status
     
     Returns a plain text summary of current tasks,
     useful for debugging and monitoring.
    """
    try:
        # Get stats
        stats = task_queue.get_stats()
        
        # Build response text
        lines = []
        lines.append("🔄 TASK QUEUE STATUS")
        lines.append("=" * 50)
        lines.append("")
        
        # Summary
        lines.append("📊 SUMMARY:")
        for status, count in stats.items():
            lines.append(f"  {status.upper()}: {count}")
        lines.append("")
        
        # Get active tasks
        from core import get_db_session
        with get_db_session() as conn:
            rows = conn.execute("""
                SELECT id, task_type, status, retries, max_retries,
                       created_at, started_at, error
                FROM simple_tasks
                WHERE status IN ('pending', 'processing', 'failed')
                ORDER BY created_at DESC
                LIMIT 50
            """).fetchall()
            
            lines.append("📋 ACTIVE TASKS:")
            lines.append("-" * 50)
            
            if not rows:
                lines.append("No active tasks")
            else:
                for row in rows:
                    status_emoji = {
                        'pending': '⏳',
                        'processing': '⚡',
                        'failed': '❌'
                    }.get(row['status'], '❓')
                    
                    retry_info = f" (retry {row['retries']}/{row['max_retries']})" if row['retries'] > 0 else ""
                    
                    lines.append(
                        f"{status_emoji} {row['id'][:8]} | {row['task_type']} | "
                        f"{row['status'].upper()}{retry_info}"
                    )
                    
                    if row['error']:
                        lines.append(f"   Error: {row['error'][:80]}...")
                    
                    lines.append("")
        
        return Response(
            content="\n".join(lines),
            media_type="text/plain"
        )
        
    except Exception as e:
        error_text = f"Error getting task status: {str(e)}"
        return Response(content=error_text, media_type="text/plain", status_code=500)


@router.post("/cleanup")
async def cleanup_old_tasks(days: int = 7):
    """
     ┌─────────────────────────────────────┐
     │       CLEANUP_OLD_TASKS             │
     └─────────────────────────────────────┘
     Clean up old completed tasks
     
     Removes tasks older than specified days.
    """
    try:
        task_queue.cleanup_old_tasks(days)
        
        return {
            "success": True,
            "message": f"Cleaned up tasks older than {days} days"
        }
        
    except Exception as e:
        debug_error(f"Cleanup failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/all")
async def clear_all_tasks():
    """
     ┌─────────────────────────────────────┐
     │        CLEAR_ALL_TASKS              │
     └─────────────────────────────────────┘
     Clear all tasks from the queue
     
     WARNING: This is a destructive operation.
    """
    try:
        # Clear the simple_tasks table
        from core import get_db_session
        with get_db_session() as conn:
            deleted = conn.execute("DELETE FROM simple_tasks").rowcount
        
        debug_success(f"Cleared all {deleted} tasks")
        
        return {
            "success": True,
            "message": f"Cleared all {deleted} tasks from the system",
            "tasks_cleared": deleted
        }
        
    except Exception as e:
        debug_error(f"Clear tasks failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
