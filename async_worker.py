"""
 ┌─────────────────────────────────────┐
 │         ASYNC_WORKER                │
 └─────────────────────────────────────┘
 Background worker for processing async tasks

 Runs continuously to process queued tasks, handle retries,
 detect timeouts, and update task/insight statuses.
"""

import asyncio
import signal
import sys
from typing import Dict, Any, Optional
from datetime import datetime

from async_task_manager import AsyncTaskManager, TaskStatus, AsyncTask, get_task_manager
from ai_worker import do_ai_image_analysis_async, do_ai_summary_async, _check_openai_circuit_breaker
import items_management
from debugger import debug_info, debug_success, debug_error, debug_warning


class AsyncWorker:
    """
     ┌─────────────────────────────────────┐
     │         ASYNCWORKER                 │
     └─────────────────────────────────────┘
     Background worker for task processing
     
     Continuously polls for pending tasks and processes them with
     proper error handling, retries, and status updates.
    """
    
    def __init__(self, worker_id: int = 1):
        self.worker_id = worker_id
        self.task_manager = get_task_manager()
        self.running = False
        self.current_task: Optional[AsyncTask] = None
        
    async def process_ai_image_task(self, task: AsyncTask) -> Dict[str, Any]:
        """
         ┌─────────────────────────────────────┐
         │     PROCESS_AI_IMAGE_TASK           │
         └─────────────────────────────────────┘
         Process AI image analysis task
         
         Handles image analysis with proper status updates.
         
         Parameters:
         - task: AsyncTask with image analysis payload
         
         Returns:
         - Dictionary with analysis results
        """
        payload = task.payload
        symbol = payload.get('symbol', '')
        image_url = payload.get('imageURL', '')
        
        if not image_url:
            raise ValueError("No image URL provided for image analysis")
            
        # Update insight status
        items_management.update_ai_analysis_status(task.insight_id, 'processing')
        
        # Perform analysis
        result = await do_ai_image_analysis_async(symbol, image_url)
        
        if result:
            # Update insight with results
            debug_info(f"Updating insight {task.insight_id} with image analysis result (length: {len(result) if result else 0})")
            update_success = items_management.update_insight(
                task.insight_id,
                AIImageSummary=result
            )
            
            if not update_success:
                debug_error(f"Database update failed for insight {task.insight_id}. Insight may not exist.")
                raise Exception("Failed to update insight with image analysis")
                
            return {'AIImageSummary': result, 'success': True}
        else:
            raise Exception("AI image analysis returned no result")
            
    async def process_ai_summary_task(self, task: AsyncTask) -> Dict[str, Any]:
        """
         ┌─────────────────────────────────────┐
         │     PROCESS_AI_SUMMARY_TASK         │
         └─────────────────────────────────────┘
         Process AI summary generation task
         
         Handles summary generation with all AI fields.
         
         Parameters:
         - task: AsyncTask with summary payload
         
         Returns:
         - Dictionary with summary results
        """
        payload = task.payload
        
        # Extract required fields
        symbol = payload.get('symbol', '')
        item_type = payload.get('item_type', '')
        title = payload.get('title', '')
        content = payload.get('content', '')
        technical = payload.get('technical', '')
        
        if not all([symbol, item_type, title, content]):
            raise ValueError("Missing required fields for AI summary")
            
        # Update insight status
        items_management.update_ai_analysis_status(task.insight_id, 'processing')
        
        # Perform analysis
        result = await do_ai_summary_async(symbol, item_type, title, content, technical)
        
        if result:
            # Update insight with results
            debug_info(f"Updating insight {task.insight_id} with AI summary results")
            update_success = items_management.update_insight(
                task.insight_id,
                AISummary=result.get('AISummary'),
                AIAction=result.get('AIAction'),
                AIConfidence=result.get('AIConfidence'),
                AIEventTime=result.get('AIEventTime'),
                AILevels=result.get('AILevels')
            )
            
            if not update_success:
                debug_error(f"Database update failed for insight {task.insight_id} in summary task. Insight may not exist.")
                raise Exception("Failed to update insight with AI summary")
                
            # Mark as completed
            items_management.update_ai_analysis_status(task.insight_id, 'completed')
            
            return {'result': result, 'success': True}
        else:
            raise Exception("AI summary generation returned no result")
            
    async def process_task(self, task: AsyncTask):
        """
         ┌─────────────────────────────────────┐
         │         PROCESS_TASK                │
         └─────────────────────────────────────┘
         Process a single task
         
         Routes task to appropriate handler based on type.
         
         Parameters:
         - task: AsyncTask to process
        """
        self.current_task = task
        
        try:
            # Check circuit breaker before processing AI tasks
            if task.task_type in ['ai_image_analysis', 'ai_summary'] and _check_openai_circuit_breaker():
                debug_warning(f"OpenAI circuit breaker is open - postponing task #{task.id} ({task.task_type})")
                # Don't increment retry count for circuit breaker delays
                self.task_manager.postpone_task(task, delay_minutes=10)
                return
            
            # Check dependencies for AI summary tasks
            if task.task_type == 'ai_summary' and task.payload.get('requires_image_analysis'):
                depends_on_task_id = task.payload.get('depends_on')
                if depends_on_task_id:
                    # Check if the dependent image analysis task is completed
                    dependent_task = self.task_manager.get_task(depends_on_task_id)
                    if not dependent_task or dependent_task.status != TaskStatus.COMPLETED:
                        debug_info(f"Summary task #{task.id} waiting for image analysis task #{depends_on_task_id} to complete")
                        # Postpone this task and check again later
                        self.task_manager.postpone_task(task, delay_minutes=2)
                        return
                    
                    # Get the image analysis result and update the payload
                    if dependent_task.result and 'AIImageSummary' in dependent_task.result:
                        task.payload['technical'] = dependent_task.result['AIImageSummary']
                        debug_info(f"Updated summary task #{task.id} with image analysis result")
                    else:
                        debug_warning(f"Image analysis task #{depends_on_task_id} completed but no result found")
                
            # Mark task as processing
            self.task_manager.update_task_status(task.id, TaskStatus.PROCESSING)
            
            debug_info(f"Worker {self.worker_id} processing task #{task.id} (type: {task.task_type})")
            
            # Route to appropriate handler
            if task.task_type == 'ai_image_analysis':
                result = await self.process_ai_image_task(task)
            elif task.task_type == 'ai_summary':
                result = await self.process_ai_summary_task(task)
            else:
                raise ValueError(f"Unknown task type: {task.task_type}")
                
            # Mark task as completed
            self.task_manager.update_task_status(task.id, TaskStatus.COMPLETED, result=result)
            debug_success(f"Task #{task.id} completed successfully")
            
        except asyncio.CancelledError:
            # Task was cancelled
            debug_warning(f"Task #{task.id} was cancelled")
            self.task_manager.update_task_status(task.id, TaskStatus.CANCELLED,
                                               error_message="Task cancelled")
            items_management.update_ai_analysis_status(task.insight_id, 'failed')
            raise
            
        except Exception as e:
            error_msg = str(e)
            debug_error(f"Task #{task.id} failed: {error_msg}")
            
            # Check if we should retry
            if task.retry_count < task.max_retries:
                self.task_manager.retry_task(task)
                items_management.update_ai_analysis_status(task.insight_id, 'pending')
            else:
                # Max retries reached
                self.task_manager.update_task_status(task.id, TaskStatus.FAILED,
                                                   error_message=error_msg)
                items_management.update_ai_analysis_status(task.insight_id, 'failed')
                
        finally:
            self.current_task = None
            
    async def run(self):
        """
         ┌─────────────────────────────────────┐
         │            RUN                      │
         └─────────────────────────────────────┘
         Main worker loop
         
         Continuously processes tasks until stopped.
        """
        self.running = True
        debug_info(f"Worker {self.worker_id} started")
        
        while self.running:
            try:
                # Check for timeouts periodically
                if asyncio.get_event_loop().time() % 30 < 1:  # Every 30 seconds
                    self.task_manager.check_timeouts()
                    
                # Get pending tasks
                tasks = self.task_manager.get_pending_tasks(limit=1)
                
                if tasks:
                    task = tasks[0]
                    await self.process_task(task)
                else:
                    # No tasks, sleep briefly
                    await asyncio.sleep(1)
                    
            except asyncio.CancelledError:
                debug_info(f"Worker {self.worker_id} shutting down")
                break
                
            except Exception as e:
                debug_error(f"Worker {self.worker_id} error: {str(e)}")
                await asyncio.sleep(5)  # Sleep on error to avoid tight loop
                
        debug_info(f"Worker {self.worker_id} stopped")
        
    def stop(self):
        """Stop the worker"""
        self.running = False
        if self.current_task:
            debug_info(f"Worker {self.worker_id} stopping, current task: #{self.current_task.id}")


class WorkerManager:
    """
     ┌─────────────────────────────────────┐
     │        WORKERMANAGER                │
     └─────────────────────────────────────┘
     Manages multiple async workers
     
     Coordinates worker lifecycle and graceful shutdown.
    """
    
    def __init__(self, worker_count: int = 3):
        self.worker_count = worker_count
        self.workers = []
        self.tasks = []
        
    async def start(self):
        """Start all workers"""
        debug_info(f"Starting {self.worker_count} workers")
        
        for i in range(self.worker_count):
            worker = AsyncWorker(worker_id=i+1)
            self.workers.append(worker)
            task = asyncio.create_task(worker.run())
            self.tasks.append(task)
            
        debug_success(f"Started {self.worker_count} workers")
        
    async def stop(self):
        """Stop all workers gracefully"""
        debug_info("Stopping all workers")
        
        # Signal workers to stop
        for worker in self.workers:
            worker.stop()
            
        # Cancel tasks if they don't stop gracefully
        await asyncio.sleep(2)
        for task in self.tasks:
            if not task.done():
                task.cancel()
                
        # Wait for all tasks to complete
        await asyncio.gather(*self.tasks, return_exceptions=True)
        
        debug_success("All workers stopped")
        
    async def run_forever(self):
        """Run workers until interrupted"""
        await self.start()
        
        try:
            # Run forever
            while True:
                await asyncio.sleep(1)
                
        except asyncio.CancelledError:
            await self.stop()
            raise


async def create_ai_analysis_task(insight_id: int, insight_data: Dict[str, Any]) -> int:
    """
     ┌─────────────────────────────────────┐
     │    CREATE_AI_ANALYSIS_TASK          │
     └─────────────────────────────────────┘
     Create AI analysis tasks for an insight
     
     Creates image analysis task first (if imageURL exists), then creates
     summary task with dependency on image analysis completion.
     
     Parameters:
     - insight_id: Insight ID to analyze
     - insight_data: Insight data dictionary
     
     Returns:
     - int: Number of tasks created
    """
    task_manager = get_task_manager()
    tasks_created = 0
    
    # Create image analysis task if image URL exists
    if insight_data.get('imageURL'):
        image_task_id = task_manager.create_task(
            task_type='ai_image_analysis',
            insight_id=insight_id,
            payload={
                'symbol': insight_data.get('symbol', ''),
                'imageURL': insight_data['imageURL']
            }
        )
        tasks_created += 1
        debug_info(f"Created image analysis task #{image_task_id} for insight {insight_id}")
        
        # Create summary task that depends on image analysis completion
        summary_task_id = task_manager.create_task(
            task_type='ai_summary',
            insight_id=insight_id,
            payload={
                'symbol': insight_data.get('symbol', ''),
                'item_type': insight_data.get('type', ''),
                'title': insight_data.get('title', ''),
                'content': insight_data.get('content', ''),
                'technical': '',  # Will be populated after image analysis
                'depends_on': image_task_id,  # Dependency on image analysis
                'requires_image_analysis': True
            }
        )
        tasks_created += 1
        debug_info(f"Created summary task #{summary_task_id} for insight {insight_id} (depends on image analysis)")
        
    else:
        # No image URL - create summary task immediately
        summary_task_id = task_manager.create_task(
            task_type='ai_summary',
            insight_id=insight_id,
            payload={
                'symbol': insight_data.get('symbol', ''),
                'item_type': insight_data.get('type', ''),
                'title': insight_data.get('title', ''),
                'content': insight_data.get('content', ''),
                'technical': '',  # No image analysis available
                'depends_on': None,  # No dependencies
                'requires_image_analysis': False
            }
        )
        tasks_created += 1
        debug_info(f"Created summary task #{summary_task_id} for insight {insight_id} (no image analysis needed)")
    
    # Update insight status
    items_management.update_ai_analysis_status(insight_id, 'pending')
    
    return tasks_created


# Signal handlers for graceful shutdown
def signal_handler(signum, frame):
    """Handle shutdown signals"""
    debug_info(f"Received signal {signum}, shutting down...")
    sys.exit(0)


# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


if __name__ == "__main__":
    """Run workers as standalone process"""
    async def main():
        manager = WorkerManager(worker_count=3)
        
        try:
            await manager.run_forever()
        except KeyboardInterrupt:
            debug_info("Keyboard interrupt received")
        finally:
            await manager.stop()
            
    asyncio.run(main())
