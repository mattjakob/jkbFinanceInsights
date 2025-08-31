"""
Queue management API routes
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from tasks import get_task_queue
from debugger import debug_info, debug_error, debug_success

router = APIRouter(prefix="/api/queue", tags=["queue"])


@router.get("/health")
async def get_queue_health() -> Dict[str, Any]:
    """
     ┌─────────────────────────────────────┐
     │         GET_QUEUE_HEALTH            │
     └─────────────────────────────────────┘
     Get queue health metrics
     
     Returns:
     - Queue health metrics including stats, stuck tasks, and health status
    """
    try:
        queue = await get_task_queue()
        health = await queue.get_health_metrics()
        return {
            "success": True,
            "data": health
        }
    except Exception as e:
        debug_error(f"Failed to get queue health: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_queue_stats() -> Dict[str, Any]:
    """
     ┌─────────────────────────────────────┐
     │         GET_QUEUE_STATS             │
     └─────────────────────────────────────┘
     Get basic queue statistics
     
     Returns:
     - Queue statistics by status
    """
    try:
        queue = await get_task_queue()
        stats = await queue.get_stats()
        return {
            "success": True,
            "data": stats
        }
    except Exception as e:
        debug_error(f"Failed to get queue stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cleanup")
async def trigger_cleanup(days: int = 7) -> Dict[str, Any]:
    """
     ┌─────────────────────────────────────┐
     │         TRIGGER_CLEANUP             │
     └─────────────────────────────────────┘
     Manually trigger cleanup of old tasks
     
     Parameters:
     - days: Number of days to keep tasks (default: 7)
     
     Returns:
     - Number of tasks cleaned up
    """
    try:
        queue = await get_task_queue()
        
        # Clean up old tasks
        cleaned = await queue.cleanup_old_tasks(days=days)
        
        # Also purge invalid tasks
        purged = await queue.purge_invalid_tasks()
        
        debug_info(f"Manual cleanup: {cleaned} old tasks removed, {purged} invalid tasks purged")
        
        return {
            "success": True,
            "data": {
                "cleaned": cleaned,
                "purged": purged,
                "total": cleaned + purged
            }
        }
    except Exception as e:
        debug_error(f"Failed to trigger cleanup: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/purge-stuck")
async def purge_stuck_tasks() -> Dict[str, Any]:
    """
     ┌─────────────────────────────────────┐
     │         PURGE_STUCK_TASKS           │
     └─────────────────────────────────────┘
     Purge tasks that are stuck in processing state
     
     Returns:
     - Number of stuck tasks reset
    """
    try:
        queue = await get_task_queue()
        
        # Use the built-in reset_stuck_tasks method
        stuck_count = await queue.reset_stuck_tasks(timeout_hours=1)
        
        debug_info(f"Reset {stuck_count} stuck tasks")
        
        return {
            "success": True,
            "data": {
                "stuck_tasks_reset": stuck_count
            }
        }
    except Exception as e:
        debug_error(f"Failed to purge stuck tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reset-queue")
async def reset_queue() -> Dict[str, Any]:
    """
     ┌─────────────────────────────────────┐
     │         RESET_QUEUE                 │
     └─────────────────────────────────────┘
     Reset entire task queue - cancels all tasks
     and resets insights to pending status
    """
    try:
        queue = await get_task_queue()
        
        # Get queue stats before reset
        stats = await queue.get_stats()
        
        # Cancel all pending and processing tasks
        cancelled_count = await queue.cancel_all_tasks()
        
        # Reset all insights with failed AI analysis back to EMPTY
        from data import InsightsRepository
        from core.models import TaskStatus
        
        insights_repo = InsightsRepository()
        
        # Reset insights with failed status back to EMPTY
        failed_reset_count = insights_repo.reset_failed_ai_analysis()
        
        # Reset insights with processing status back to EMPTY
        processing_reset_count = insights_repo.reset_processing_ai_analysis()
        
        total_reset_count = failed_reset_count + processing_reset_count
        
        debug_success(f"Queue reset completed: {cancelled_count} tasks cancelled, {total_reset_count} insights reset")
        
        return {
            "success": True,
            "message": "Queue reset completed successfully",
            "data": {
                "tasks_cancelled": cancelled_count,
                "insights_reset": total_reset_count,
                "failed_insights_reset": failed_reset_count,
                "processing_insights_reset": processing_reset_count,
                "previous_stats": stats
            }
        }
        
    except Exception as e:
        debug_error(f"Failed to reset queue: {e}")
        raise HTTPException(status_code=500, detail=str(e))
