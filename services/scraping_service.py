"""
/**
 * 
 *  ┌─────────────────────────────────────┐
 *  │    INSIGHT SCRAPING SERVICE         │
 *  └─────────────────────────────────────┘
 *  Business logic for scraping insights from external sources
 * 
 *  Manages the process of fetching new insights from various
 *  external data sources using the task queue system.
 * 
 *  Parameters:
 *  - None
 * 
 *  Returns:
 *  - InsightScrapingService instance
 * 
 *  Notes:
 *  - Creates scraping tasks via task queue
 *  - Supports multiple feed types
 *  - Does NOT handle symbol search (use SymbolService)
 */
"""

from typing import Dict, Any, List
import asyncio
from core import FeedType, TaskName
from tasks import get_task_queue
from debugger import debug_info, debug_error


class InsightScrapingService:
    """
     ┌─────────────────────────────────────┐
     │    INSIGHTSCRAPINGSERVICE           │
     └─────────────────────────────────────┘
     Service for scraping insights from external sources
     
     Manages creation of scraping tasks and coordination
     of external data fetching operations.
    """
    
    def __init__(self):
        self.queue = None  # Will be initialized async
    
    async def create_scraping_task(self, 
                            symbol: str, 
                            exchange: str, 
                            feed_type: str, 
                            max_items: int = 50) -> Dict[str, Any]:
        """
         ┌─────────────────────────────────────┐
         │     CREATE_SCRAPING_TASK            │
         └─────────────────────────────────────┘
         Create task to scrape insights from external sources
         
         Creates tasks for scraping operations via task queue.
         
         Parameters:
         - symbol: Trading symbol
         - exchange: Exchange name
         - feed_type: Feed type or "ALL"
         - max_items: Maximum items to fetch
         
         Returns:
         - Dictionary with task creation results
        """
        try:
            # Initialize queue if needed
            if not self.queue:
                self.queue = await get_task_queue()
            
            # Handle ALL feed type
            if feed_type == "ALL" or not feed_type:
                return await self._create_all_scraping_tasks(symbol, exchange, max_items)
            else:
                # Single feed type
                try:
                    ft = FeedType(feed_type)
                except ValueError:
                    return {
                        "success": False,
                        "message": f"Invalid feed type: {feed_type}",
                        "processed_items": 0,
                        "created_insights": 0,
                        "duplicate_insights": 0,
                        "failed_items": 0,
                        "results": []
                    }
                
                # Map feed type to task name
                task_name_map = {
                    FeedType.TD_NEWS: TaskName.SCRAPING_NEWS,
                    FeedType.TD_IDEAS_RECENT: TaskName.SCRAPING_IDEAS_RECENT,
                    FeedType.TD_IDEAS_POPULAR: TaskName.SCRAPING_IDEAS_POPULAR,
                    FeedType.TD_OPINIONS: TaskName.SCRAPING_OPINIONS
                }
                
                task_name = task_name_map.get(ft)
                if not task_name:
                    return {
                        "success": False,
                        "message": f"No task handler for feed type: {feed_type}",
                        "processed_items": 0,
                        "created_insights": 0,
                        "duplicate_insights": 0,
                        "failed_items": 0,
                        "results": []
                    }
                
                # Create task for specific feed type
                task_id = await self.queue.add_task(
                    task_name.value,
                    {
                        'symbol': symbol,
                        'exchange': exchange,
                        'limit': max_items
                    },
                    max_retries=1,  # Scraping typically shouldn't retry many times
                    entity_type='scraping',
                    entity_id=None
                )
                
                # Task creation logged by queue
                
                return {
                    "success": True,
                    "message": f"Created task to fetch {feed_type}",
                    "task_id": task_id,
                    "feed_type": feed_type,
                    "tasks_created": 1
                }
            
        except Exception as e:
            debug_error(f"Failed to create scraping task: {e}")
            return {
                "success": False,
                "message": f"Failed to create scraping task: {str(e)}",
                "processed_items": 0,
                "created_insights": 0,
                "duplicate_insights": 0,
                "failed_items": 0,
                "results": []
            }
    
    def get_available_feeds(self) -> List[Dict[str, str]]:
        """
         ┌─────────────────────────────────────┐
         │      GET_AVAILABLE_FEEDS            │
         └─────────────────────────────────────┘
         Get list of available feed types
         
         Returns:
         - List of feed type dictionaries
        """
        feeds = [
            {
                "name": feed_type.value,
                "value": feed_type.value,
                "description": f"{feed_type.value} feed"
            }
            for feed_type in FeedType
        ]
        
        # Add "ALL" option
        feeds.insert(0, {
            "name": "ALL",
            "value": "ALL",
            "description": "Fetch from all available feeds"
        })
        
        return feeds
    
    async def _create_all_scraping_tasks(self, symbol: str, exchange: str, max_items: int) -> Dict[str, Any]:
        """
         ┌─────────────────────────────────────┐
         │   _CREATE_ALL_SCRAPING_TASKS        │
         └─────────────────────────────────────┘
         Create scraping tasks for all feed types
         
         Parameters:
         - symbol: Trading symbol
         - exchange: Exchange name
         - max_items: Maximum items per feed
         
         Returns:
         - Dictionary with task creation results
        """
        # Creating multiple scraping tasks
        
        # Map feed types to task names
        feed_task_map = {
            FeedType.TD_NEWS: TaskName.SCRAPING_NEWS,
            FeedType.TD_IDEAS_RECENT: TaskName.SCRAPING_IDEAS_RECENT,
            FeedType.TD_IDEAS_POPULAR: TaskName.SCRAPING_IDEAS_POPULAR,
            FeedType.TD_OPINIONS: TaskName.SCRAPING_OPINIONS
        }
        
        tasks_created = 0
        task_ids = []
        
        for feed_type, task_name in feed_task_map.items():
            task_id = await self.queue.add_task(
                task_name.value,
                {
                    'symbol': symbol,
                    'exchange': exchange,
                    'limit': max_items
                },
                max_retries=1,
                entity_type='scraping',
                entity_id=None
            )
            
            task_ids.append(task_id)
            tasks_created += 1
            # Task creation logged by queue
        
        return {
            "success": True,
            "message": f"Created {tasks_created} scraping tasks for all feeds",
            "feed_type": "ALL",
            "tasks_created": tasks_created,
            "task_ids": task_ids
        }

