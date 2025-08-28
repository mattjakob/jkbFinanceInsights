"""
/**
 * 
 *  ┌─────────────────────────────────────┐
 *  │         TASK HANDLERS               │
 *  └─────────────────────────────────────┘
 *  Handler functions for different task types
 * 
 *  Implements the business logic for each task type,
 *  keeping task processing separate from queue management.
 * 
 *  Parameters:
 *  - Task-specific parameters via payload
 * 
 *  Returns:
 *  - Task-specific results
 * 
 *  Notes:
 *  - Each handler is a standalone function
 *  - Can be sync or async
 */
"""

from typing import Dict, Any, Optional

from data import InsightsRepository
from core import AIAnalysisStatus
from debugger import debug_info, debug_error, debug_success


# Initialize repository
insights_repo = InsightsRepository()


async def handle_ai_analysis(insight_id: int, **kwargs) -> Dict[str, Any]:
    """
     ┌─────────────────────────────────────┐
     │      HANDLE_AI_ANALYSIS             │
     └─────────────────────────────────────┘
     Handle AI analysis for an insight
     
     Performs complete AI analysis including image and text.
     
     Parameters:
     - insight_id: ID of insight to analyze
     - **kwargs: Additional parameters
     
     Returns:
     - Dictionary with analysis results
    """
    try:
        # Get insight from database
        insight = insights_repo.get_by_id(insight_id)
        if not insight:
            raise ValueError(f"Insight {insight_id} not found")
        
        # Update status to processing
        insights_repo.update_ai_status(insight_id, AIAnalysisStatus.PROCESSING)
        
        # Import AI module here to avoid circular imports
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from analysis import AnalysisService, OpenAIProvider
        
        # Create analysis service
        service = AnalysisService(OpenAIProvider())
        
        results = {}
        
        # Perform image analysis if URL exists
        if insight.image_url:
            debug_info(f"Analyzing image for insight {insight_id}")
            try:
                image_result = await service.analyze_image_async(
                    insight.image_url,
                    context={'symbol': insight.symbol}
                )
                results['image_analysis'] = image_result
                
                # Update database
                insights_repo.update(insight_id, {
                    'ai_image_summary': image_result
                })
            except Exception as e:
                debug_error(f"Image analysis failed: {e}")
        
        # Perform text analysis
        debug_info(f"Analyzing text for insight {insight_id}")
        analysis_result = await service.analyze_text_async(
            text=insight.content,
            context={
                'symbol': insight.symbol,
                'type': insight.type.value,
                'title': insight.title,
                'technical': results.get('image_analysis', '')
            }
        )
        
        # Update database with results
        updates = {
            'ai_summary': analysis_result.summary,
            'ai_action': analysis_result.action.value,
            'ai_confidence': analysis_result.confidence,
            'ai_event_time': analysis_result.event_time,
            'ai_levels': analysis_result.format_levels()
        }
        
        insights_repo.update(insight_id, updates)
        insights_repo.update_ai_status(insight_id, AIAnalysisStatus.COMPLETED)
        
        debug_success(f"AI analysis completed for insight {insight_id}")
        
        return {
            'success': True,
            'insight_id': insight_id,
            'updates': updates
        }
        
    except Exception as e:
        debug_error(f"AI analysis failed for insight {insight_id}: {e}")
        insights_repo.update_ai_status(insight_id, AIAnalysisStatus.FAILED)
        raise


async def handle_bulk_analysis(**kwargs) -> Dict[str, Any]:
    """
     ┌─────────────────────────────────────┐
     │      HANDLE_BULK_ANALYSIS           │
     └─────────────────────────────────────┘
     Handle bulk AI analysis
     
     Creates individual analysis tasks for insights
     needing analysis.
     
     Returns:
     - Dictionary with task creation results
    """
    try:
        # Get insights needing analysis
        insights = insights_repo.find_for_ai_analysis()
        
        if not insights:
            debug_info("No insights need AI analysis")
            return {
                'success': True,
                'insights_found': 0,
                'tasks_created': 0
            }
        
        # Import task queue here
        from .queue import TaskQueue
        queue = TaskQueue()
        
        # Create tasks for each insight
        task_ids = []
        for insight in insights:
            task_id = queue.add_task(
                'ai_analysis',
                {'insight_id': insight.id},
                max_retries=3
            )
            task_ids.append(task_id)
        
        debug_success(f"Created {len(task_ids)} AI analysis tasks")
        
        return {
            'success': True,
            'insights_found': len(insights),
            'tasks_created': len(task_ids),
            'task_ids': task_ids
        }
        
    except Exception as e:
        debug_error(f"Bulk analysis failed: {e}")
        raise


def handle_cleanup(days: int = 7, **kwargs) -> Dict[str, Any]:
    """
     ┌─────────────────────────────────────┐
     │        HANDLE_CLEANUP               │
     └─────────────────────────────────────┘
     Handle cleanup of old tasks and data
     
     Parameters:
     - days: Keep data from last N days
     
     Returns:
     - Cleanup statistics
    """
    from .queue import TaskQueue
    queue = TaskQueue()
    
    # Cleanup old tasks
    queue.cleanup_old_tasks(days)
    
    return {
        'success': True,
        'message': f'Cleaned up tasks older than {days} days'
    }


# Handler registry for easy registration
HANDLERS = {
    'ai_analysis': handle_ai_analysis,
    'bulk_analysis': handle_bulk_analysis,
    'cleanup': handle_cleanup
}
