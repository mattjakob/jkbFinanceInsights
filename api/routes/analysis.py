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
async def analyze_insights(request: Dict[str, Any]):
    """
     ┌─────────────────────────────────────┐
     │       ANALYZE_INSIGHTS              │
     └─────────────────────────────────────┘
     Trigger AI analysis for pending insights
     
     Creates analysis tasks for insights that need AI processing.
     If symbol is provided, only analyzes insights for that symbol.
     
     Parameters:
     - symbol: Optional symbol to filter insights (e.g., "BTCUSD")
    """
    try:
        # Extract symbol from request body
        symbol = request.get('symbol')
        
        # Use bulk analysis handler to create tasks
        result = await handle_bulk_analysis(symbol=symbol)
        
        if symbol:
            message = f"Created {result['tasks_created']} analysis tasks for {result['insights_found']} insights of symbol {symbol}"
        else:
            message = f"Created {result['tasks_created']} analysis tasks for {result['insights_found']} insights"
        
        return {
            "success": result['success'],
            "message": message,
            "insights_found": result['insights_found'],
            "tasks_created": result['tasks_created'],
            "symbol": symbol
        }
        
    except Exception as e:
        debug_error(f"Analysis trigger failed: {e}")
        return {
            "success": False,
            "message": f"Error triggering analysis: {str(e)}"
        }


@router.get("/pending")
async def get_pending_analysis():
    """
     ┌─────────────────────────────────────┐
     │       GET_PENDING_ANALYSIS          │
     └─────────────────────────────────────┘
     Get insights pending AI analysis
    """
    try:
        insights = insights_repo.find_for_ai_analysis()
        return {
            "success": True,
            "count": len(insights),
            "insights": [
                {
                    "id": i.id,
                    "symbol": i.symbol,
                    "title": i.title,
                    "ai_status": i.ai_analysis_status.value if i.ai_analysis_status else None,
                    "ai_summary": i.ai_summary[:50] if i.ai_summary else None
                }
                for i in insights
            ]
        }
    except Exception as e:
        debug_error(f"Failed to get pending analysis: {e}")
        return {"success": False, "error": str(e)}


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
        
        # Check if insight is in EMPTY status (ready for analysis)
        if insight.ai_analysis_status != AIAnalysisStatus.EMPTY:
            raise HTTPException(
                status_code=400, 
                detail=f"Insight {insight_id} is not ready for analysis. Current status: {insight.ai_analysis_status.value}"
            )
        
        # Update status to PENDING when task is queued
        insights_repo.update_ai_status(insight_id, AIAnalysisStatus.PENDING)
        
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


@router.post("/generate-report")
async def generate_ai_report(request: Dict[str, Any]):
    """
     ┌─────────────────────────────────────┐
     │       GENERATE_AI_REPORT            │
     └─────────────────────────────────────┘
     Generate AI analysis report for a symbol
     
     Creates an AI-generated comprehensive trading report
     for the specified symbol using all available insights.
     
     Parameters:
     - symbol: Trading symbol (required)
    """
    try:
        # Extract and validate symbol
        symbol = request.get('symbol', '').strip().upper()
        if not symbol:
            raise HTTPException(status_code=400, detail="Symbol is required")
        
        debug_info(f"Generating AI report for {symbol}")
        
        # Get all insights for the symbol to create context
        insights = insights_repo.find_all(symbol_filter=symbol)
        
        if not insights:
            return {
                "success": False,
                "error": f"No insights found for symbol {symbol}"
            }
        
        # Build content from insights
        content_parts = []
        for insight in insights[:20]:  # Limit to recent 20 insights
            if insight.ai_summary:
                content_parts.append(f"- {insight.ai_summary}")
        
        content = "\n".join(content_parts) if content_parts else f"Analysis data for {symbol}"
        
        # Create a task in the queue for report generation
        from tasks.queue import TaskQueue
        task_queue = TaskQueue()
        
        task_id = task_queue.add_task(
            task_type="ai_report_generation",
            payload={
                "symbol": symbol,
                "content": content,
                "insights_count": len(insights)
            },
            entity_type="symbol",
            entity_id=hash(symbol)  # Use hash of symbol as entity ID
        )
        
        debug_success(f"AI report generation task created for {symbol} (Task ID: {task_id})")
        
        return {
            "success": True,
            "symbol": symbol,
            "task_id": task_id,
            "message": f"AI report generation task created for {symbol}",
            "insights_count": len(insights)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        debug_error(f"Failed to generate AI report: {e}")
        return {
            "success": False,
            "error": str(e)
        }



