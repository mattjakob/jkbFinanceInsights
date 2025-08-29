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
from core import TaskStatus, TaskName
from debugger import debug_info, debug_error, debug_success, debug_warning


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
        
        # Update status to processing (this ensures consistency)
        insights_repo.update_ai_status(insight_id, TaskStatus.PROCESSING)
        debug_info(f"Updated insight {insight_id} status to PROCESSING")
        
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
        insights_repo.update_ai_status(insight_id, TaskStatus.COMPLETED)
        
        debug_success(f"AI analysis completed for #{insight_id} - status updated to COMPLETED")
        
        return {
            'success': True,
            'insight_id': insight_id,
            'updates': updates
        }
        
    except Exception as e:
        debug_error(f"AI analysis failed for insight {insight_id}: {e}")
        
        # Update status to failed
        try:
            insights_repo.update_ai_status(insight_id, TaskStatus.FAILED)
            debug_warning(f"Updated insight {insight_id} status to FAILED")
        except Exception as status_error:
            debug_error(f"Failed to update insight {insight_id} status to FAILED: {status_error}")
        
        return {
            'success': False,
            'insight_id': insight_id,
            'error': str(e),
            'should_retry': True
        }


async def handle_image_analysis(insight_id: int, **kwargs) -> Dict[str, Any]:
    """
     ┌─────────────────────────────────────┐
     │      HANDLE_IMAGE_ANALYSIS          │
     └─────────────────────────────────────┘
     Handle image analysis for an insight
     
     Performs image analysis and then creates a text analysis task.
     
     Parameters:
     - insight_id: ID of insight to analyze
     - **kwargs: Additional parameters
     
     Returns:
     - Dictionary with analysis results
     
     Notes:
     - This is the first phase of analysis
     - After completion, creates a text analysis task
    """
    try:
        # Get insight from database
        insight = insights_repo.get_by_id(insight_id)
        if not insight:
            debug_warning(f"Insight {insight_id} not found - likely deleted")
            return {
                'success': False,
                'insight_id': insight_id,
                'error': 'Insight not found - may have been deleted',
                'should_retry': False
            }
        
        # Update status to PROCESSING now that task is actually running
        insights_repo.update_ai_status(insight_id, TaskStatus.PROCESSING)
        debug_info(f"Updated insight {insight_id} status to PROCESSING")
        
        # Verify image URL still exists
        if not insight.image_url or not insight.image_url.strip():
            debug_warning(f"Insight {insight_id} has no valid image URL, skipping image analysis")
            # Create text analysis task directly
            await _create_text_analysis_task(insight_id)
            return {
                'success': True,
                'insight_id': insight_id,
                'message': 'No image URL, proceeding to text analysis'
            }
        
        # Import AI module here to avoid circular imports
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from analysis import AnalysisService, OpenAIProvider
        
        # Create analysis service
        service = AnalysisService(OpenAIProvider())
        
        # Perform image analysis
        debug_info(f"Analyzing image for insight {insight_id}")
        try:
            image_result = await service.analyze_image_async(
                insight.image_url,
                context={
                    'symbol': insight.symbol,
                    'insight_id': insight_id
                }
            )
            
            # Update database with image analysis result
            insights_repo.update(insight_id, {
                'ai_image_summary': image_result
            })
            
            debug_success(f"Image analysis completed for insight {insight_id}")
            
            # Create text analysis task
            await _create_text_analysis_task(insight_id)
            
            return {
                'success': True,
                'insight_id': insight_id,
                'image_result': image_result
            }
            
        except Exception as e:
            debug_error(f"Image analysis failed for insight {insight_id}: {e}")
            
            # Update status to failed
            insights_repo.update_ai_status(insight_id, TaskStatus.FAILED)
            
            return {
                'success': False,
                'insight_id': insight_id,
                'error': str(e),
                'should_retry': True
            }
        
    except Exception as e:
        debug_error(f"Image analysis handler failed for insight {insight_id}: {e}")
        
        # Update status to failed
        try:
            insights_repo.update_ai_status(insight_id, TaskStatus.FAILED)
        except Exception as status_error:
            debug_error(f"Failed to update insight {insight_id} status to FAILED: {status_error}")
        
        return {
            'success': False,
            'insight_id': insight_id,
            'error': str(e),
            'should_retry': True
        }


async def handle_text_analysis(insight_id: int, **kwargs) -> Dict[str, Any]:
    """
     ┌─────────────────────────────────────┐
     │      HANDLE_TEXT_ANALYSIS           │
     └─────────────────────────────────────┘
     Handle text analysis for an insight
     
     Performs text analysis using any available image analysis results.
     
     Parameters:
     - insight_id: ID of insight to analyze
     - **kwargs: Additional parameters
     
     Returns:
     - Dictionary with analysis results
     
     Notes:
     - This is the final phase of analysis
     - Uses image analysis results if available
    """
    try:
        # Get insight from database
        insight = insights_repo.get_by_id(insight_id)
        if not insight:
            debug_warning(f"Insight {insight_id} not found - likely deleted")
            return {
                'success': False,
                'insight_id': insight_id,
                'error': 'Insight not found - may have been deleted',
                'should_retry': False
            }
        
        # Update status to PROCESSING now that task is actually running
        insights_repo.update_ai_status(insight_id, TaskStatus.PROCESSING)
        debug_info(f"Updated insight {insight_id} status to PROCESSING")
        
        # Import AI module here to avoid circular imports
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from analysis import AnalysisService, OpenAIProvider
        
        # Create analysis service
        service = AnalysisService(OpenAIProvider())
        
        # Perform text analysis
        debug_info(f"Analyzing text for insight {insight_id}")
        
        # Get image analysis result if available
        image_context = insight.ai_image_summary if insight.ai_image_summary else ""
        
        analysis_result = await service.analyze_text_async(
            text=insight.content,
            context={
                'symbol': insight.symbol,
                'type': insight.type.value,
                'title': insight.title,
                'technical': image_context,
                'insight_id': insight_id
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
        insights_repo.update_ai_status(insight_id, TaskStatus.COMPLETED)
        
        debug_success(f"Text analysis completed for insight {insight_id} - status updated to COMPLETED")
        
        return {
            'success': True,
            'insight_id': insight_id,
            'updates': updates
        }
        
    except Exception as e:
        debug_error(f"Text analysis failed for insight {insight_id}: {e}")
        
        # Update status to failed
        try:
            insights_repo.update_ai_status(insight_id, TaskStatus.FAILED)
        except Exception as status_error:
            debug_error(f"Failed to update insight {insight_id} status to FAILED: {status_error}")
        
        return {
            'success': False,
            'insight_id': insight_id,
            'error': str(e),
            'should_retry': True
        }


async def _create_text_analysis_task(insight_id: int) -> str:
    """
     ┌─────────────────────────────────────┐
     │    _CREATE_TEXT_ANALYSIS_TASK       │
     └─────────────────────────────────────┘
     Helper function to create text analysis task
     
     Parameters:
     - insight_id: ID of insight for text analysis
     
     Returns:
     - Task ID of created task
    """
    try:
        from .queue import TaskQueue
        queue = TaskQueue()
        
        task_id = queue.add_task(
            TaskName.AI_TEXT_ANALYSIS.value,
            {'insight_id': insight_id},
            max_retries=None,  # Use config value
            entity_type='insight',
            entity_id=insight_id
        )
        
        debug_info(f"Created text analysis task {task_id} for insight {insight_id}")
        return task_id
        
    except Exception as e:
        debug_error(f"Failed to create text analysis task for insight {insight_id}: {e}")
        raise


async def handle_bulk_analysis(symbol: str = None, type_filter: str = None, **kwargs) -> Dict[str, Any]:
    """
     ┌─────────────────────────────────────┐
     │      HANDLE_BULK_ANALYSIS           │
     └─────────────────────────────────────┘
     Handle bulk AI analysis with proper sequencing
     
     Creates tasks in two phases:
     1. Image analysis tasks (only for insights with valid image URLs)
     2. Text analysis tasks (after image analysis completes or if no image needed)
     
     Parameters:
     - symbol: Optional symbol to filter insights
     - type_filter: Optional type to filter insights
     
     Returns:
     - Dictionary with task creation results
     
     Notes:
     - Image analysis must complete before text analysis
     - Only creates tasks when actually needed
     - Ensures proper dependency management
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
                'symbol': symbol,
                'type_filter': type_filter
            }
        
        # Debug: Show what we found
        debug_info(f"Found {len(insights)} total insights needing analysis")
        
        # Filter by symbol if provided
        if symbol:
            symbol = symbol.upper()
            original_count = len(insights)
            insights = [insight for insight in insights if insight.symbol and insight.symbol.upper() == symbol]
            debug_info(f"Filtered from {original_count} to {len(insights)} insights for symbol {symbol}")
        
        # Filter by type if provided
        if type_filter and type_filter != '':
            original_count = len(insights)
            insights = [insight for insight in insights if insight.type == type_filter]
            debug_info(f"Filtered from {original_count} to {len(insights)} insights for type {type_filter}")
        
        if not insights:
            filters = []
            if symbol:
                filters.append(f"symbol {symbol}")
            if type_filter:
                filters.append(f"type {type_filter}")
            
            if filters:
                debug_info(f"No insights need AI analysis for {', '.join(filters)}")
            else:
                debug_info("No insights need AI analysis")
            
            return {
                'success': True,
                'insights_found': 0,
                'tasks_created': 0,
                'symbol': symbol,
                'type_filter': type_filter
            }
        
        # Import task queue here
        from .queue import TaskQueue
        queue = TaskQueue()
        
        # Phase 1: Create image analysis tasks (only for insights with valid image URLs)
        image_tasks_created = 0
        text_tasks_created = 0
        failed_insights = []
        
        for insight in insights:
            try:
                # Check if insight needs image analysis
                needs_image_analysis = bool(insight.image_url and insight.image_url.strip())
                
                if needs_image_analysis:
                    # Create image analysis task first
                    insights_repo.update_ai_status(insight.id, TaskStatus.PENDING, TaskName.AI_IMAGE_ANALYSIS)
                    debug_info(f"Updated insight {insight.id} status to PENDING for image analysis")
                    
                    task_id = queue.add_task(
                        TaskName.AI_IMAGE_ANALYSIS.value,
                        {'insight_id': insight.id},
                        max_retries=None,  # Use config value
                        entity_type='insight',
                        entity_id=insight.id
                    )
                    image_tasks_created += 1
                    debug_info(f"Created image analysis task {task_id} for insight {insight.id}")
                else:
                    # No image needed, create text analysis task directly
                    insights_repo.update_ai_status(insight.id, TaskStatus.PENDING, TaskName.AI_TEXT_ANALYSIS)
                    debug_info(f"Updated insight {insight.id} status to PENDING for text analysis")
                    
                    task_id = queue.add_task(
                        TaskName.AI_TEXT_ANALYSIS.value,
                        {'insight_id': insight.id},
                        max_retries=None,  # Use config value
                        entity_type='insight',
                        entity_id=insight.id
                    )
                    text_tasks_created += 1
                    debug_info(f"Created text analysis task {task_id} for insight {insight.id}")
                
            except Exception as e:
                debug_error(f"Failed to create task for insight {insight.id}: {e}")
                failed_insights.append(insight.id)
                
                # Reset status back to EMPTY on task creation failure
                try:
                    insights_repo.update_ai_status(insight.id, TaskStatus.EMPTY)
                    debug_warning(f"Reset insight {insight.id} status back to EMPTY due to task creation failure")
                except Exception as reset_error:
                    debug_error(f"Failed to reset insight {insight.id} status: {reset_error}")
        
        if failed_insights:
            debug_warning(f"Failed to create tasks for {len(failed_insights)} insights: {failed_insights}")
        
        total_tasks = image_tasks_created + text_tasks_created
        
        # Build success message
        filters = []
        if symbol:
            filters.append(f"symbol {symbol}")
        if type_filter:
            filters.append(f"type {type_filter}")
        
        if filters:
            debug_success(f"Created {total_tasks} tasks for {', '.join(filters)}: {image_tasks_created} image + {text_tasks_created} text")
        else:
            debug_success(f"Created {total_tasks} tasks: {image_tasks_created} image + {text_tasks_created} text")
        
        return {
            'success': True,
            'insights_found': len(insights),
            'tasks_created': total_tasks,
            'image_tasks': image_tasks_created,
            'text_tasks': text_tasks_created,
            'symbol': symbol,
            'type_filter': type_filter
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
    
    # Get timeout from payload or use default
    timeout_seconds = payload.get('timeout_seconds', 10)
    
    # Simulate work time (will timeout if longer than TASK_PROCESSING_TIMEOUT)
    work_time = random.randint(1, int(timeout_seconds * 2))
    time.sleep(work_time)
    
    return {
        'success': True,
        'work_time': work_time,
        'message': f'Test task completed in {work_time} seconds'
    }


def handle_create_timeout_test(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
     ┌─────────────────────────────────────┐
     │      HANDLE_CREATE_TIMEOUT_TEST      │
     └─────────────────────────────────────┘
     Create a test task that will likely timeout
     
     Useful for testing timeout and retry functionality.
    """
    try:
        from .queue import TaskQueue
        from config import TASK_PROCESSING_TIMEOUT
        
        queue = TaskQueue()
        
        # Create a test task with a timeout that will likely exceed TASK_PROCESSING_TIMEOUT
        timeout_seconds = payload.get('timeout_seconds', TASK_PROCESSING_TIMEOUT / 1000.0 * 1.5)
        
        task_id = queue.add_task(
            'test_timeout',
            {'timeout_seconds': timeout_seconds},
            max_retries=None  # Use config value
        )
        
        return {
            'success': True,
            'task_id': task_id,
            'timeout_seconds': timeout_seconds,
            'config_timeout_ms': TASK_PROCESSING_TIMEOUT,
            'message': f'Created timeout test task {task_id} with {timeout_seconds}s work time'
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'message': f'Failed to create timeout test: {str(e)}'
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
        from core.models import ReportModel, AIAction
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
            ai_levels=levels_str
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
    TaskName.AI_ANALYSIS.value: handle_ai_analysis,
    TaskName.AI_IMAGE_ANALYSIS.value: handle_image_analysis,
    TaskName.AI_TEXT_ANALYSIS.value: handle_text_analysis,
    TaskName.BULK_ANALYSIS.value: handle_bulk_analysis,
    TaskName.CLEANUP.value: handle_cleanup,
    TaskName.REPORT_GENERATION.value: handle_ai_report_generation,
    'test_timeout': handle_test_timeout,
    'create_timeout_test': handle_create_timeout_test
}
