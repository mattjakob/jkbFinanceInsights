"""
/**
 * 
 *  ┌─────────────────────────────────────┐
 *  │       TASK WORKER V2                │
 *  └─────────────────────────────────────┘
 *  Improved worker with async queue support
 * 
 *  Features better concurrency control, reduced delays,
 *  and improved error handling.
 * 
 *  Parameters:
 *  - None
 * 
 *  Returns:
 *  - AsyncTaskWorker instance
 * 
 *  Notes:
 *  - Uses async queue operations
 *  - Implements adaptive polling
 *  - Better resource management
 */
"""

import asyncio
import signal
import sys
from datetime import datetime, timedelta
from typing import Dict, Callable, Any, Optional, List
from contextlib import asynccontextmanager

from .queue import TaskQueue, Task, get_task_queue
from debugger import debug_info, debug_error, debug_warning, debug_success
from config import TASK_PROCESSING_TIMEOUT, TASK_POLLING_INTERVAL


class TaskWorker:
    """
     ┌─────────────────────────────────────┐
     │         TASKWORKER                  │
     └─────────────────────────────────────┘
     Worker for processing tasks
     
     Improved performance with adaptive polling and
     better resource management.
    """
    
    def __init__(self, worker_id: int = 1, queue: Optional[TaskQueue] = None):
        self.worker_id = worker_id
        self.queue = queue  # Will be set in async context
        self.handlers: Dict[str, Callable] = {}
        self.running = False
        self._current_task: Optional[Task] = None
    
    def register_handler(self, task_type: str, handler: Callable):
        """Register a handler for a task type"""
        self.handlers[task_type] = handler
    
    async def process_task(self, task: Task):
        """
         ┌─────────────────────────────────────┐
         │        PROCESS_TASK                 │
         └─────────────────────────────────────┘
         Process a single task with improved error handling
         
         Parameters:
         - task: Task to process
        """
        self._current_task = task
        
        try:
            # Get handler
            handler = self.handlers.get(task.task_type)
            if not handler:
                raise ValueError(f"No handler registered for task type: {task.task_type}")
            
            # Call handler with timeout (all handlers are async)
            timeout_seconds = TASK_PROCESSING_TIMEOUT / 1000.0
            
            try:
                result = await asyncio.wait_for(
                    handler(**task.payload), 
                    timeout=timeout_seconds
                )
                    
            except asyncio.TimeoutError:
                error_msg = f"Task {task.id} timed out after {timeout_seconds:.1f}s"
                debug_error(error_msg)
                await self.queue.fail_task(task.id, error_msg, permanent=False)
                return
            
            # Check handler result
            if isinstance(result, dict) and not result.get('success', True):
                if not result.get('should_retry', True):
                    # Permanent failure
                    await self.queue.fail_task(
                        task.id, 
                        result.get('error', 'Handler indicated permanent failure'), 
                        permanent=True
                    )
                    debug_warning(f"Task {task.id} permanently failed: {result.get('error')}")
                    return
            
            # Mark complete
            await self.queue.complete_task(task.id, result)
            
        except asyncio.CancelledError:
            # Worker is shutting down
            debug_warning(f"Task {task.id} cancelled during shutdown")
            await self.queue.fail_task(task.id, "Worker shutdown")
            raise
            
        except Exception as e:
            error_msg = str(e)
            debug_error(f"Task {task.id} failed: {error_msg}")
            await self.queue.fail_task(task.id, error_msg)
            
        finally:
            self._current_task = None
    
    async def run(self):
        """
         ┌─────────────────────────────────────┐
         │             RUN                     │
         └─────────────────────────────────────┘
         Main worker loop with improved performance
         
         Uses adaptive polling and better error handling.
        """
        # Initialize queue if not provided
        if not self.queue:
            self.queue = await get_task_queue()
        
        self.running = True
        debug_info(f"Worker {self.worker_id} started")
        
        iteration = 0
        
        while self.running:
            try:
                # Simple periodic maintenance every 1000 iterations (worker 1 only)
                if self.worker_id == 1 and iteration % 1000 == 0 and iteration > 0:
                    asyncio.create_task(self._perform_maintenance())
                
                # Get next task
                task = await self.queue.get_next_task()
                
                if task:
                    await self.process_task(task)
                else:
                    await asyncio.sleep(TASK_POLLING_INTERVAL / 1000.0)
                
                iteration += 1
                    
            except asyncio.CancelledError:
                debug_info(f"Worker {self.worker_id} shutting down")
                break
                
            except Exception as e:
                debug_error(f"Worker {self.worker_id} error: {str(e)}")
                await asyncio.sleep(5)  # Sleep on error
        
        debug_info(f"Worker {self.worker_id} stopped")
    
    async def _perform_maintenance(self):
        """Perform simple periodic maintenance"""
        try:
            await self.queue.cleanup_old_tasks(days=7)
            debug_info("Periodic maintenance completed")
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
     
     Improved coordination and resource management.
    """
    
    def __init__(self, worker_count: int = 3):
        self.worker_count = worker_count
        self.workers: List[TaskWorker] = []
        self.tasks: List[asyncio.Task] = []
        self._handlers: Dict[str, Callable] = {}
        self.shared_queue: Optional[TaskQueue] = None
        self._shutdown_event = None
    
    def register_handler(self, task_type: str, handler: Callable):
        """Register handler for all workers"""
        self._handlers[task_type] = handler
    
    @asynccontextmanager
    async def _worker_context(self):
        """Context manager for worker lifecycle"""
        try:
            yield
        finally:
            await self.stop()
    
    async def start(self):
        """Start all workers"""
        # Initialize shared queue
        self.shared_queue = await get_task_queue()
        
        # Create and start workers
        for i in range(self.worker_count):
            worker = TaskWorker(worker_id=i + 1, queue=self.shared_queue)
            
            # Register all handlers
            for task_type, handler in self._handlers.items():
                worker.register_handler(task_type, handler)
            
            self.workers.append(worker)
            # Start worker as background task (non-blocking)
            task = asyncio.create_task(worker.run())
            self.tasks.append(task)
        
        debug_success(f"Started {self.worker_count} workers in background")
    
    async def stop(self):
        """Stop all workers gracefully"""
        debug_info("Stopping all workers...")
        
        # Signal workers to stop
        for worker in self.workers:
            worker.stop()
        
        # Set shutdown event
        if self._shutdown_event is None:
            self._shutdown_event = asyncio.Event()
        self._shutdown_event.set()
        
        # Wait briefly for graceful shutdown
        await asyncio.sleep(1)
        
        # Cancel tasks if still running
        for task in self.tasks:
            if not task.done():
                task.cancel()
        
        # Wait for all tasks to complete
        if self.tasks:
            await asyncio.gather(*self.tasks, return_exceptions=True)
        
        # Close queue connections
        if self.shared_queue:
            await self.shared_queue.close()
        
        debug_success("All workers stopped")
    
    async def run_forever(self):
        """Run workers until interrupted"""
        async with self._worker_context():
            await self.start()
            
            try:
                # Wait for shutdown signal
                if self._shutdown_event is None:
                    self._shutdown_event = asyncio.Event()
                await self._shutdown_event.wait()
                
            except asyncio.CancelledError:
                debug_info("Worker pool cancelled")
                raise


# Signal handlers for graceful shutdown
_shutdown_event = None


def signal_handler(signum, frame):
    """Handle shutdown signals"""
    global _shutdown_event
    debug_info(f"Received signal {signum}, initiating shutdown...")
    if _shutdown_event is None:
        import asyncio
        _shutdown_event = asyncio.Event()
    _shutdown_event.set()


# Signal handlers are registered by the main application
# Not at module level to avoid import-time issues


async def get_shutdown_event():
    """Get the global shutdown event"""
    global _shutdown_event
    if _shutdown_event is None:
        _shutdown_event = asyncio.Event()
    return _shutdown_event
