"""
/**
 * 
 *  ┌─────────────────────────────────────┐
 *  │          TASK WORKER                │
 *  └─────────────────────────────────────┘
 *  Worker for processing queued tasks
 * 
 *  Polls the task queue and routes tasks to registered handlers
 *  with automatic error handling and retries.
 * 
 *  Parameters:
 *  - None
 * 
 *  Returns:
 *  - TaskWorker instance
 * 
 *  Notes:
 *  - Handlers are registered by task type
 *  - Supports async and sync handlers
 */
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Callable, Any, Optional, List
import signal
import sys

from .queue import TaskQueue, Task
from debugger import debug_info, debug_error, debug_warning, debug_success
from config import TASK_PROCESSING_TIMEOUT


class TaskWorker:
    """
     ┌─────────────────────────────────────┐
     │          TASKWORKER                 │
     └─────────────────────────────────────┘
     Worker for processing tasks from queue
     
     Continuously polls for tasks and routes them to
     appropriate handlers.
    """
    
    def __init__(self, worker_id: int = 1):
        self.worker_id = worker_id
        self.queue = TaskQueue()
        self.handlers: Dict[str, Callable] = {}
        self.running = False
        self._current_task: Optional[Task] = None
    
    def register_handler(self, task_type: str, handler: Callable):
        """
         ┌─────────────────────────────────────┐
         │       REGISTER_HANDLER              │
         └─────────────────────────────────────┘
         Register a handler for a task type
         
         Parameters:
         - task_type: Type to handle
         - handler: Function to process tasks
         
         Notes:
         - Handler receives task payload as kwargs
         - Can be sync or async function
        """
        self.handlers[task_type] = handler
        debug_info(f"Registered handler for task type: {task_type}")
    
    async def process_task(self, task: Task):
        """
         ┌─────────────────────────────────────┐
         │        PROCESS_TASK                 │
         └─────────────────────────────────────┘
         Process a single task
         
         Routes task to handler and manages lifecycle.
         
         Parameters:
         - task: Task to process
        """
        self._current_task = task
        
        try:
            # Get handler
            handler = self.handlers.get(task.task_type)
            if not handler:
                raise ValueError(f"No handler registered for task type: {task.task_type}")
            
            debug_info(f"Worker {self.worker_id} processing {task.task_type} task {task.id}")
            
            # Call handler with timeout
            timeout_seconds = TASK_PROCESSING_TIMEOUT / 1000.0
            try:
                if asyncio.iscoroutinefunction(handler):
                    result = await asyncio.wait_for(handler(**task.payload), timeout=timeout_seconds)
                else:
                    # Run sync handler in thread pool with timeout
                    loop = asyncio.get_event_loop()
                    # Check if handler expects a payload parameter or individual parameters
                    import inspect
                    sig = inspect.signature(handler)
                    if 'payload' in sig.parameters:
                        # Handler expects a single payload parameter
                        result = await asyncio.wait_for(
                            loop.run_in_executor(None, handler, task.payload), 
                            timeout=timeout_seconds
                        )
                    else:
                        # Handler expects individual parameters
                        result = await asyncio.wait_for(
                            loop.run_in_executor(None, handler, **task.payload), 
                            timeout=timeout_seconds
                        )
            except asyncio.TimeoutError:
                error_msg = f"Task {task.id} timed out after {timeout_seconds:.1f}s (config: {TASK_PROCESSING_TIMEOUT}ms)"
                debug_error(error_msg)
                # Handle timeout as a regular failure (allows retries)
                self.queue.fail_task(task.id, error_msg, permanent=False)
                # Note: fail_task will automatically call _update_entity_status_on_failure
                return
            
            # Check if handler returned a failure that shouldn't be retried
            if isinstance(result, dict) and not result.get('success', True):
                if not result.get('should_retry', True):
                    # Mark as failed without retry
                    self.queue.fail_task(task.id, result.get('error', 'Handler indicated permanent failure'), permanent=True)
                    debug_warning(f"Task {task.id} permanently failed: {result.get('error')}")
                    # Note: fail_task will automatically call _update_entity_status_on_failure
                    return
            
            # Mark complete
            self.queue.complete_task(task.id, result)
            debug_success(f"Task {task.id} completed successfully")
            
        except asyncio.CancelledError:
            # Worker is shutting down
            debug_warning(f"Task {task.id} cancelled during shutdown")
            self.queue.fail_task(task.id, "Worker shutdown")
            # Note: fail_task will automatically call _update_entity_status_on_failure
            raise
            
        except Exception as e:
            error_msg = str(e)
            debug_error(f"Task {task.id} failed: {error_msg}")
            self.queue.fail_task(task.id, error_msg)
            # Note: fail_task will automatically call _update_entity_status_on_failure
            
        finally:
            self._current_task = None
    
    async def run(self):
        """
         ┌─────────────────────────────────────┐
         │             RUN                     │
         └─────────────────────────────────────┘
         Main worker loop
         
         Continuously processes tasks until stopped.
        """
        self.running = True
        debug_info(f"Worker {self.worker_id} started")
        
        last_cleanup = datetime.now()
        cleanup_interval = timedelta(minutes=30)  # Cleanup every 30 minutes
        
        while self.running:
            try:
                # Periodic maintenance only on worker 1
                if self.worker_id == 1 and datetime.now() - last_cleanup > cleanup_interval:
                    await self._perform_maintenance()
                    last_cleanup = datetime.now()
                
                # Get next task
                task = self.queue.get_next_task()
                
                if task:
                    await self.process_task(task)
                else:
                    # No tasks, sleep briefly
                    await asyncio.sleep(1)
                    
            except asyncio.CancelledError:
                debug_info(f"Worker {self.worker_id} shutting down")
                break
                
            except Exception as e:
                debug_error(f"Worker {self.worker_id} error: {str(e)}")
                await asyncio.sleep(5)  # Sleep on error
        
        debug_info(f"Worker {self.worker_id} stopped")
    
    async def _perform_maintenance(self):
        """
         ┌─────────────────────────────────────┐
         │       _PERFORM_MAINTENANCE          │
         └─────────────────────────────────────┘
         Perform periodic maintenance tasks
         
         Cleans up orphaned tasks and resets stuck tasks.
        """
        try:
            debug_info(f"Worker {self.worker_id} performing maintenance")
            
            # Purge orphaned tasks
            orphaned_count = self.queue.purge_orphaned_tasks()
            if orphaned_count > 0:
                debug_info(f"Purged {orphaned_count} orphaned tasks")
            
            # Reset stuck tasks
            stuck_count = self.queue.reset_stuck_tasks(timeout_hours=2)
            if stuck_count > 0:
                debug_info(f"Reset {stuck_count} stuck tasks")
            
            # Clean up old tasks
            cleaned_count = self.queue.cleanup_old_tasks(days=7)
            if cleaned_count > 0:
                debug_info(f"Cleaned up {cleaned_count} old tasks")
            
            # Clean up stale pending tasks
            stale_count = self.queue.cleanup_stale_pending_tasks()
            if stale_count > 0:
                debug_info(f"Cleaned up {stale_count} stale pending tasks")
            
            # Log health metrics
            health = self.queue.get_health_metrics()
            if health['health_status'] != 'healthy':
                debug_warning(f"Queue health: {health['health_status']} (score: {health['health_score']})")
                for issue in health['issues']:
                    debug_warning(f"  - {issue}")
            
        except Exception as e:
            debug_error(f"Maintenance error: {e}")
    
    def stop(self):
        """Stop the worker"""
        self.running = False
        if self._current_task:
            debug_info(f"Worker {self.worker_id} stopping, current task: {self._current_task.id}")


class WorkerPool:
    """
     ┌─────────────────────────────────────┐
     │         WORKERPOOL                  │
     └─────────────────────────────────────┘
     Manages multiple workers
     
     Coordinates worker lifecycle and provides a single
     interface for managing multiple workers.
    """
    
    def __init__(self, worker_count: int = 3):
        self.worker_count = worker_count
        self.workers: List[TaskWorker] = []
        self.tasks: List[asyncio.Task] = []
        self._handlers: Dict[str, Callable] = {}
    
    def register_handler(self, task_type: str, handler: Callable):
        """Register handler that will be used by all workers"""
        self._handlers[task_type] = handler
    
    async def start(self):
        """Start all workers"""
        debug_info(f"Starting {self.worker_count} workers")
        
        for i in range(self.worker_count):
            worker = TaskWorker(worker_id=i + 1)
            
            # Register all handlers
            for task_type, handler in self._handlers.items():
                worker.register_handler(task_type, handler)
            
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


# Signal handlers for graceful shutdown
def signal_handler(signum, frame):
    """Handle shutdown signals"""
    debug_info(f"Received signal {signum}, shutting down...")
    sys.exit(0)


# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)
