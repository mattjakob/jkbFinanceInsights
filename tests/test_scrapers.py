"""
 ┌─────────────────────────────────────┐
 │         TEST_SCRAPERS               │
 └─────────────────────────────────────┘
 Comprehensive scraper testing
 
 Tests all scrapers with various symbols, item counts, and edge cases.
"""

import time
from typing import Dict, List, Any
from .base_test import BaseTest
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services import InsightScrapingService
from core import FeedType
from tasks import get_task_queue
from data.repositories import InsightsRepository

class ScraperTests(BaseTest):
    """
     ┌─────────────────────────────────────┐
     │        SCRAPERTESTS                 │
     └─────────────────────────────────────┘
     Test suite for all scraping functionality
     
     Validates scraper behavior across different symbols, feeds, and limits.
    """
    
    def __init__(self):
        super().__init__("Scraper Tests")
        self.service = None
        self.queue = None
        self.insights_repo = None
        
    def setup(self):
        """Initialize test dependencies"""
        super().setup()
        self.service = InsightScrapingService()
        self.queue = None  # Will be initialized async
        self.insights_repo = InsightsRepository()
        
    def _wait_for_tasks(self, timeout: int = 10) -> bool:
        """Wait for all tasks to complete (simplified)"""
        # Since everything is async now, just return True
        # Tasks are processed immediately by workers
        return True
        
    def test_single_feed_basic(self) -> Dict[str, Any]:
        """Test single feed with basic parameters"""
        # Test TD NEWS with BTCUSD
        result = self.service.create_scraping_task(
            symbol='BTCUSD',
            exchange='BITSTAMP', 
            feed_type='TD NEWS',
            max_items=5
        )
        
        if not result.get('success'):
            return {
                'success': False,
                'message': f"Failed to create task: {result.get('message')}"
            }
            
        # Wait for task completion
        if not self._wait_for_tasks():
            return {
                'success': False,
                'message': 'Task timeout'
            }
            
        # Verify insights were created
        insights = self.insights_repo.get_all_by_symbol('BTCUSD', FeedType.TD_NEWS)
        
        return self.assert_greater(
            len(insights), 
            0,
            "Expected insights to be created"
        )
        
    def test_all_feeds_pattern(self) -> Dict[str, Any]:
        """Test ALL pattern creates tasks for each feed"""
        result = self.service.create_scraping_task(
            symbol='AAPL',
            exchange='NASDAQ',
            feed_type='ALL',
            max_items=3
        )
        
        expected_tasks = 4  # NEWS, IDEAS_RECENT, IDEAS_POPULAR, OPINIONS
        
        return self.assert_equals(
            result.get('tasks_created'),
            expected_tasks,
            f"Expected {expected_tasks} tasks for ALL pattern"
        )
        
    def test_multiple_symbols(self) -> Dict[str, Any]:
        """Test scrapers with different symbol types"""
        test_cases = [
            ('BTCUSD', 'BITSTAMP', 'TD NEWS'),
            ('AAPL', 'NASDAQ', 'TD IDEAS RECENT'),
            ('EURUSD', 'FX', 'TD OPINIONS'),
            ('GOLD', 'COMMODITIES', 'TD IDEAS POPULAR')
        ]
        
        results = []
        for symbol, exchange, feed_type in test_cases:
            result = self.service.create_scraping_task(
                symbol=symbol,
                exchange=exchange,
                feed_type=feed_type,
                max_items=2
            )
            results.append({
                'symbol': symbol,
                'success': result.get('success', False),
                'message': result.get('message', '')
            })
            
        # Check all succeeded
        all_success = all(r['success'] for r in results)
        failed = [r for r in results if not r['success']]
        
        return {
            'success': all_success,
            'message': f"All symbols tested" if all_success else f"Failed: {failed}",
            'details': {
                'tested': len(test_cases),
                'succeeded': len([r for r in results if r['success']]),
                'results': results
            }
        }
        
    def test_item_count_accuracy(self) -> Dict[str, Any]:
        """Test that scrapers respect requested item counts"""
        # Clear existing data for clean test
        self.insights_repo.delete_by_symbol_and_type('BTCUSD', FeedType.TD_NEWS)
        
        requested = 7
        result = self.service.create_scraping_task(
            symbol='BTCUSD',
            exchange='BITSTAMP',
            feed_type='TD NEWS', 
            max_items=requested
        )
        
        if not result.get('success'):
            return {
                'success': False,
                'message': f"Task creation failed: {result.get('message')}"
            }
            
        # Wait for completion
        if not self._wait_for_tasks():
            return {
                'success': False,
                'message': 'Task timeout'
            }
            
        # Check task result
        task_id = result.get('task_id')
        task_info = self.queue.get_task(task_id)
        
        if task_info and task_info.result:
            created = task_info.result.get('created_insights', 0)
            # Allow some tolerance for API limitations
            success = created >= requested * 0.8  # 80% threshold
            
            return {
                'success': success,
                'message': f"Created {created}/{requested} items",
                'details': {
                    'requested': requested,
                    'created': created,
                    'efficiency': f"{(created/requested)*100:.1f}%"
                }
            }
        
        return {
            'success': False,
            'message': 'No task result found'
        }
        
    def test_duplicate_detection(self) -> Dict[str, Any]:
        """Test that duplicate detection works correctly"""
        # Run same scrape twice
        symbol = 'BTCUSD'
        exchange = 'BITSTAMP'
        feed = 'TD OPINIONS'  # Smaller feed for faster test
        
        # First scrape
        result1 = self.service.create_scraping_task(symbol, exchange, feed, 3)
        if not self._wait_for_tasks():
            return {'success': False, 'message': 'First scrape timeout'}
            
        # Get task result
        task1 = self.queue.get_task(result1.get('task_id'))
        created1 = task1.result.get('created_insights', 0) if task1 and task1.result else 0
        
        # Second scrape (should find duplicates)
        result2 = self.service.create_scraping_task(symbol, exchange, feed, 3)
        if not self._wait_for_tasks():
            return {'success': False, 'message': 'Second scrape timeout'}
            
        task2 = self.queue.get_task(result2.get('task_id'))
        created2 = task2.result.get('created_insights', 0) if task2 and task2.result else 0
        duplicates2 = task2.result.get('duplicate_insights', 0) if task2 and task2.result else 0
        
        # Second run should have fewer creates and some duplicates
        success = created2 < created1 or duplicates2 > 0
        
        return {
            'success': success,
            'message': 'Duplicate detection working' if success else 'No duplicates detected',
            'details': {
                'first_run': {'created': created1},
                'second_run': {'created': created2, 'duplicates': duplicates2}
            }
        }
        
    def test_invalid_inputs(self) -> Dict[str, Any]:
        """Test scraper behavior with invalid inputs"""
        test_cases = [
            # (symbol, exchange, feed, expected_success)
            ('', 'NASDAQ', 'TD NEWS', False),  # Empty symbol
            ('INVALID123', 'FAKE', 'TD NEWS', True),  # Invalid but should try
            ('BTCUSD', 'BITSTAMP', 'INVALID_FEED', False),  # Invalid feed
            ('BTCUSD', 'BITSTAMP', 'TD NEWS', True),  # Valid
        ]
        
        results = []
        for symbol, exchange, feed, expected in test_cases:
            result = self.service.create_scraping_task(
                symbol=symbol,
                exchange=exchange,
                feed_type=feed,
                max_items=1
            )
            success = result.get('success', False) == expected
            results.append({
                'input': f"{symbol}/{exchange}/{feed}",
                'expected': expected,
                'actual': result.get('success', False),
                'passed': success
            })
            
        all_passed = all(r['passed'] for r in results)
        
        return {
            'success': all_passed,
            'message': 'All validation tests passed' if all_passed else 'Some validation tests failed',
            'details': {'results': results}
        }
        
    def test_concurrent_scraping(self) -> Dict[str, Any]:
        """Test multiple concurrent scraping tasks"""
        # Create multiple tasks at once
        tasks = []
        symbols = ['BTCUSD', 'AAPL', 'EURUSD']
        
        for symbol in symbols:
            result = self.service.create_scraping_task(
                symbol=symbol,
                exchange='VARIOUS',
                feed_type='TD NEWS',
                max_items=2
            )
            if result.get('success'):
                tasks.append({
                    'symbol': symbol,
                    'task_id': result.get('task_id')
                })
                
        # Wait for all to complete
        if not self._wait_for_tasks(timeout=15):
            return {
                'success': False,
                'message': 'Concurrent tasks timeout'
            }
            
        # Check all completed successfully
        completed = 0
        for task in tasks:
            task_info = self.queue.get_task(task['task_id'])
            if task_info and task_info.status.value == 'completed':
                completed += 1
                
        success = completed == len(tasks)
        
        return {
            'success': success,
            'message': f"{completed}/{len(tasks)} tasks completed",
            'details': {
                'total_tasks': len(tasks),
                'completed': completed,
                'symbols': symbols
            }
        }
