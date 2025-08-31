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

from tasks import get_task_queue
from data import InsightsRepository
from debugger import debug_info, debug_error, debug_success

# Create router
router = APIRouter(prefix="/api/tasks", tags=["tasks"])

# Initialize repositories
insights_repo = InsightsRepository()


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
        queue = await get_task_queue()
        stats = await queue.get_stats()
        
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
        queue = await get_task_queue()
        stats = await queue.get_stats()
        
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
        queue = await get_task_queue()
        await queue.cleanup_old_tasks(days)
        
        return {
            "success": True,
            "message": f"Cleaned up tasks older than {days} days"
        }
        
    except Exception as e:
        debug_error(f"Cleanup failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cleanup-stale-pending")
async def cleanup_stale_pending_tasks():
    """
     ┌─────────────────────────────────────┐
     │    CLEANUP_STALE_PENDING_TASKS     │
     └─────────────────────────────────────┘
     Clean up pending tasks that have exceeded timeout
     
     Uses TASK_PENDING_TIMEOUT from config.
    """
    try:
        queue = await get_task_queue()
        count = await queue.cleanup_stale_pending_tasks()
        
        return {
            "success": True,
            "cleaned": count,
            "message": f"Cleaned up {count} stale pending tasks"
        }
        
    except Exception as e:
        debug_error(f"Error cleaning up stale pending tasks: {e}")
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


@router.post("/reset")
async def reset_tasks(request: Dict[str, Any] = {}):
    """
     ┌─────────────────────────────────────┐
     │          RESET_TASKS                │
     └─────────────────────────────────────┘
     Reset tasks - either all or by symbol/type
     
     Can reset all tasks or filter by symbol and type.
     Sets insight statuses to EMPTY.
     
     Parameters:
     - symbol: Optional symbol to filter by
     - type: Optional type to filter by
    """
    try:
        symbol = request.get('symbol')
        type_filter = request.get('type')
        
        if symbol:
            # Reset specific symbol/type
            feed_type = None
            if type_filter:
                from core import FeedType
                try:
                    feed_type = FeedType(type_filter)
                except ValueError:
                    raise HTTPException(status_code=400, detail=f"Invalid feed type: {type_filter}")
            
            insights_reset, tasks_cancelled = insights_repo.reset_insights_by_symbol_and_type(symbol, feed_type)
            
            debug_info(f"Reset completed for {symbol}: {insights_reset} insights reset, {tasks_cancelled} tasks cancelled")
            
            return {
                "success": True,
                "tasks_cleared": tasks_cancelled,
                "insights_reset": insights_reset,
                "symbol": symbol,
                "type": type_filter,
                "message": f"Reset completed for {symbol}: {insights_reset} insights reset, {tasks_cancelled} tasks cancelled"
            }
        else:
            # Reset all tasks
            queue = await get_task_queue()
            tasks_cleared = await queue.cancel_all_tasks()
            
            # Reset all insight statuses that are stuck in PENDING or PROCESSING
            insights_reset = insights_repo.reset_stuck_insights()
            
            debug_info(f"Reset completed: {tasks_cleared} tasks cancelled, {insights_reset} insights reset")
            
            return {
                "success": True,
                "tasks_cleared": tasks_cleared,
                "insights_reset": insights_reset,
                "message": f"Reset completed: {tasks_cleared} tasks cancelled, {insights_reset} insights reset"
            }
        
    except Exception as e:
        debug_error(f"Reset tasks failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

