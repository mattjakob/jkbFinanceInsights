"""
/**
 * 
 *  ┌─────────────────────────────────────┐
 *  │        ANALYSIS ROUTES              │
 *  └─────────────────────────────────────┘
 *  API routes for AI analysis operations
 * 
 *  Provides endpoints for triggering and managing AI analysis
 *  using the refactored task and analysis systems.
 * 
 *  Parameters:
 *  - None
 * 
 *  Returns:
 *  - FastAPI router with analysis endpoints
 * 
 *  Notes:
 *  - Uses task queue for async processing
 *  - Supports individual and bulk analysis
 */
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from tasks import TaskQueue, handle_bulk_analysis
from data import InsightsRepository
from debugger import debug_info, debug_error, debug_success

# Create router
router = APIRouter(prefix="/api/analysis", tags=["analysis"])

# Initialize dependencies
task_queue = TaskQueue()
insights_repo = InsightsRepository()


@router.post("/analyze")
async def analyze_insights():
    """
     ┌─────────────────────────────────────┐
     │       ANALYZE_INSIGHTS              │
     └─────────────────────────────────────┘
     Trigger AI analysis for all pending insights
     
     Creates analysis tasks for insights that need AI processing.
    """
    try:
        # Use bulk analysis handler to create tasks
        result = await handle_bulk_analysis()
        
        return {
            "success": result['success'],
            "message": f"Created {result['tasks_created']} analysis tasks for {result['insights_found']} insights",
            "insights_found": result['insights_found'],
            "tasks_created": result['tasks_created']
        }
        
    except Exception as e:
        debug_error(f"Analysis trigger failed: {e}")
        return {
            "success": False,
            "message": f"Error triggering analysis: {str(e)}"
        }


@router.post("/analyze/{insight_id}")
async def analyze_single_insight(insight_id: int):
    """
     ┌─────────────────────────────────────┐
     │     ANALYZE_SINGLE_INSIGHT          │
     └─────────────────────────────────────┘
     Trigger AI analysis for a specific insight
    """
    try:
        # Check if insight exists
        insight = insights_repo.get_by_id(insight_id)
        if not insight:
            raise HTTPException(status_code=404, detail="Insight not found")
        
        # Create analysis task
        task_id = task_queue.add_task(
            'ai_analysis',
            {'insight_id': insight_id},
            max_retries=3
        )
        
        debug_success(f"Created analysis task {task_id} for insight {insight_id}")
        
        return {
            "success": True,
            "message": f"Analysis started for insight {insight_id}",
            "insight_id": insight_id,
            "task_id": task_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        debug_error(f"Single analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))



