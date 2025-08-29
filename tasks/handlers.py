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
            # Insight has been deleted - gracefully handle this
            debug_warning(f"Insight {insight_id} not found - likely deleted")
            return {
                'success': False,
                'insight_id': insight_id,
                'error': 'Insight not found - may have been deleted',
                'should_retry': False
            }
        
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
                    context={
                        'symbol': insight.symbol,
                        'insight_id': insight_id  # Pass insight_id in context
                    }
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
                'technical': results.get('image_analysis', ''),
                'insight_id': insight_id  # Pass insight_id in context
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
        
        debug_success(f"AI analysis completed for #{insight_id}")
        
        return {
            'success': True,
            'insight_id': insight_id,
            'updates': updates
        }
        
    except Exception as e:
        debug_error(f"AI analysis failed for insight {insight_id}: {e}")
        
        # Only update status if insight still exists
        try:
            if insights_repo.get_by_id(insight_id):
                # Reset status to EMPTY on failure so it can be retried
                insights_repo.update_ai_status(insight_id, AIAnalysisStatus.EMPTY)
        except Exception:
            debug_warning(f"Could not update status for insight {insight_id} - may have been deleted")
        
        # Check if this is a recoverable error
        error_msg = str(e).lower()
        should_retry = not any(phrase in error_msg for phrase in [
            'not found',
            'deleted',
            'does not exist',
            'invalid insight'
        ])
        
        if not should_retry:
            # Don't retry for permanent failures
            return {
                'success': False,
                'insight_id': insight_id,
                'error': str(e),
                'should_retry': False
            }
        
        # Re-raise for retry-able errors
        raise


async def handle_bulk_analysis(symbol: str = None, **kwargs) -> Dict[str, Any]:
    """
     ┌─────────────────────────────────────┐
     │      HANDLE_BULK_ANALYSIS           │
     └─────────────────────────────────────┘
     Handle bulk AI analysis
     
     Creates individual analysis tasks for insights
     needing analysis. If symbol is provided, only
     processes insights for that symbol.
     
     Parameters:
     - symbol: Optional symbol to filter insights
     
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
                'tasks_created': 0,
                'symbol': symbol
            }
        
        # Debug: Show what we found
        debug_info(f"Found {len(insights)} total insights needing analysis")
        
        # Filter by symbol if provided
        if symbol:
            symbol = symbol.upper()
            original_count = len(insights)
            insights = [insight for insight in insights if insight.symbol and insight.symbol.upper() == symbol]
            debug_info(f"Filtered from {original_count} to {len(insights)} insights for symbol {symbol}")
        
        if not insights:
            debug_info(f"No insights need AI analysis for symbol {symbol}" if symbol else "No insights need AI analysis")
            return {
                'success': True,
                'insights_found': 0,
                'tasks_created': 0,
                'symbol': symbol
            }
        
        # Import task queue here
        from .queue import TaskQueue
        queue = TaskQueue()
        
        # Create tasks for each insight and update status to PENDING
        task_ids = []
        for insight in insights:
            # Update status to PENDING when task is queued
            insights_repo.update_ai_status(insight.id, AIAnalysisStatus.PENDING)
            
            task_id = queue.add_task(
                'ai_analysis',
                {'insight_id': insight.id},
                max_retries=3
            )
            task_ids.append(task_id)
        
        debug_success(f"Created {len(task_ids)} AI analysis tasks for symbol {symbol}" if symbol else f"Created {len(task_ids)} AI analysis tasks")
        
        return {
            'success': True,
            'insights_found': len(insights),
            'tasks_created': len(task_ids),
            'task_ids': task_ids,
            'symbol': symbol
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


def handle_test_timeout(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
     ┌─────────────────────────────────────┐
     │        HANDLE_TEST_TIMEOUT           │
     └─────────────────────────────────────┘
     Test handler for timeout functionality
     
     Simulates a long-running operation to test task timeout.
    """
    import time
    import random
    
    # Simulate work time (random between 1-10 seconds)
    work_time = random.randint(1, 10)
    time.sleep(work_time)
    
    return {
        'success': True,
        'work_time': work_time,
        'message': f'Test task completed in {work_time} seconds'
    }


def handle_ai_report_generation(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
     ┌─────────────────────────────────────┐
     │    HANDLE_AI_REPORT_GENERATION      │
     └─────────────────────────────────────┘
     Handle AI report generation task
     
     Generates a comprehensive AI report for a symbol
     using all available insights.
    """
    try:
        symbol = payload.get('symbol')
        content = payload.get('content')
        insights_count = payload.get('insights_count', 0)
        
        if not symbol:
            debug_error("No symbol provided for report generation")
            return {'success': False, 'should_retry': False, 'error': 'No symbol provided'}
        
        debug_info(f"Generating AI report for {symbol} with {insights_count} insights")
        
        # Import analysis service
        from analysis.service import AnalysisService
        service = AnalysisService()
        
        # Generate the report using AI
        result = service.analyze_report(symbol=symbol, content=content)
        
        # Create a report entry in the database
        from data.repositories.reports import get_reports_repository
        from core.models import ReportModel, AIAnalysisStatus, AIAction
        from datetime import datetime
        
        reports_repo = get_reports_repository()
        
        # Parse the OpenAI response and convert to the expected format
        # OpenAI returns confidence as 0-100, convert to 0-1
        confidence_normalized = result.confidence / 100.0 if result.confidence is not None else 0.0
        
        # Convert action to uppercase and map to AIAction enum
        action_str = result.action.upper() if result.action else "HOLD"
        
        # Format levels as string
        levels_str = result.format_levels() if result.levels else None
        
        report = ReportModel(
            time_fetched=datetime.now(),
            symbol=symbol,
            ai_summary=result.summary,
            ai_action=AIAction(action_str),
            ai_confidence=confidence_normalized,
            ai_event_time=result.event_time,
            ai_levels=levels_str,
            ai_analysis_status=AIAnalysisStatus.COMPLETED
        )
        
        report_id = reports_repo.create(report)
        
        debug_success(f"AI report generated for {symbol} (Report ID: {report_id})")
        
        return {
            'success': True,
            'should_retry': False,
            'report_id': report_id,
            'symbol': symbol,
            'message': f'AI report generated successfully for {symbol}'
        }
        
    except Exception as e:
        debug_error(f"AI report generation failed: {e}")
        return {'success': False, 'should_retry': True, 'error': str(e)}


# Handler registry for easy registration
HANDLERS = {
    'ai_analysis': handle_ai_analysis,
    'bulk_analysis': handle_bulk_analysis,
    'cleanup': handle_cleanup,
    'ai_report_generation': handle_ai_report_generation,
    'test_timeout': handle_test_timeout
}
