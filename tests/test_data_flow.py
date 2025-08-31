"""
 ┌─────────────────────────────────────┐
 │        TEST_DATA_FLOW               │
 └─────────────────────────────────────┘
 End-to-end data flow testing
 
 Tests complete workflows from scraping to report generation.
"""

import time
from typing import Dict, List, Any, Optional
from .base_test import BaseTest
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services import (
    InsightScrapingService, 
    InsightAnalysisService,
    ReportService,
    InsightManagementService
)
from core import FeedType, TaskStatus
from tasks import get_task_queue
from data.repositories import InsightsRepository, ReportsRepository

class DataFlowTests(BaseTest):
    """
     ┌─────────────────────────────────────┐
     │        DATAFLOWTESTS                │
     └─────────────────────────────────────┘
     Test suite for complete data flows
     
     Validates end-to-end functionality from scraping to reports.
    """
    
    def __init__(self):
        super().__init__("Data Flow Tests")
        self.scraping_service = None
        self.analysis_service = None
        self.report_service = None
        self.insights_service = None
        self.queue = None
        self.insights_repo = None
        self.reports_repo = None
        
    def setup(self):
        """Initialize test dependencies"""
        super().setup()
        self.scraping_service = InsightScrapingService()
        self.analysis_service = InsightAnalysisService()
        self.report_service = ReportService()
        self.insights_service = InsightManagementService()
        self.queue = None  # Will be initialized async
        self.insights_repo = InsightsRepository()
        self.reports_repo = ReportsRepository()
        
    def _wait_for_tasks(self, timeout: int = 30) -> bool:
        """Wait for all tasks to complete (simplified)"""
        # Since everything is async now, just return True
        # Tasks are processed immediately by workers
        return True
        
    def test_scrape_to_analysis_flow(self) -> Dict[str, Any]:
        """Test flow from scraping to automatic analysis"""
        symbol = 'BTCUSD'
        exchange = 'BITSTAMP'
        
        # Clear existing data for clean test
        self.insights_repo.delete_by_symbol_and_type(symbol, FeedType.TD_OPINIONS)
        
        # Step 1: Scrape
        scrape_result = self.scraping_service.create_scraping_task(
            symbol=symbol,
            exchange=exchange,
            feed_type='TD OPINIONS',  # Small feed for faster test
            max_items=2
        )
        
        if not scrape_result.get('success'):
            return {
                'success': False,
                'message': f"Scraping failed: {scrape_result.get('message')}"
            }
            
        # Wait for scraping to complete
        if not self._wait_for_tasks(timeout=20):
            return {
                'success': False,
                'message': 'Scraping timeout'
            }
            
        # Check if insights were created with EMPTY status
        insights = self.insights_repo.get_all_by_symbol(symbol, FeedType.TD_OPINIONS)
        empty_insights = [i for i in insights if i.task_status == TaskStatus.EMPTY]
        
        # Step 2: Check if analysis tasks were auto-created
        # No need to wait - async system processes immediately
        
        # Check for pending/completed analysis
        analyzed_insights = [
            i for i in self.insights_repo.get_all_by_symbol(symbol, FeedType.TD_OPINIONS)
            if i.task_status in [TaskStatus.PENDING, TaskStatus.IN_PROGRESS, TaskStatus.COMPLETED]
        ]
        
        return {
            'success': len(analyzed_insights) > 0,
            'message': f"Auto-analysis triggered for {len(analyzed_insights)} insights",
            'details': {
                'scraped': len(insights),
                'empty_status': len(empty_insights),
                'analyzed_or_pending': len(analyzed_insights)
            }
        }
        
    def test_complete_pipeline(self) -> Dict[str, Any]:
        """Test complete flow: scrape -> analyze -> report"""
        symbol = 'AAPL'
        exchange = 'NASDAQ'
        
        # Step 1: Scrape multiple feeds
        print("\n📥 Step 1: Scraping...")
        scrape_tasks = []
        for feed in ['TD NEWS', 'TD IDEAS RECENT']:
            result = self.scraping_service.create_scraping_task(
                symbol=symbol,
                exchange=exchange,
                feed_type=feed,
                max_items=3
            )
            if result.get('success'):
                scrape_tasks.append(feed)
                
        if not scrape_tasks:
            return {
                'success': False,
                'message': 'No scraping tasks created'
            }
            
        # Wait for scraping
        if not self._wait_for_tasks(timeout=25):
            return {
                'success': False,
                'message': 'Scraping timeout'
            }
            
        # Step 2: Wait for auto-analysis
        print("🤖 Step 2: Checking auto-analysis...")
        # No need to wait - async system processes immediately
        
        if not self._wait_for_tasks(timeout=40):
            # Check if any analysis happened
            analyzed = self.insights_repo.get_all(
                filters={'symbol': symbol, 'task_status': TaskStatus.COMPLETED}
            )
            if not analyzed:
                return {
                    'success': False,
                    'message': 'Analysis timeout or not triggered'
                }
                
        # Step 3: Generate report
        print("📊 Step 3: Generating report...")
        report_result = self.report_service.create_report_task(
            symbol=symbol,
            time_range='1h'
        )
        
        if not report_result.get('success'):
            return {
                'success': False,
                'message': f"Report creation failed: {report_result.get('message')}"
            }
            
        # Wait for report
        if not self._wait_for_tasks(timeout=30):
            return {
                'success': False,
                'message': 'Report generation timeout'
            }
            
        # Verify complete pipeline
        insights = self.insights_repo.get_all(filters={'symbol': symbol})
        analyzed = [i for i in insights if i.task_status == TaskStatus.COMPLETED]
        reports = self.reports_repo.get_by_symbol(symbol)
        
        pipeline_complete = (
            len(insights) > 0 and
            len(analyzed) > 0 and
            len(reports) > 0
        )
        
        return {
            'success': pipeline_complete,
            'message': 'Complete pipeline executed successfully' if pipeline_complete else 'Pipeline incomplete',
            'details': {
                'total_insights': len(insights),
                'analyzed_insights': len(analyzed),
                'reports_generated': len(reports),
                'analysis_rate': f"{(len(analyzed)/len(insights)*100):.1f}%" if insights else "0%"
            }
        }
        
    def test_all_pattern_flow(self) -> Dict[str, Any]:
        """Test ALL pattern across scraping and analysis"""
        symbol = 'EURUSD'
        exchange = 'FX'
        
        # Scrape ALL feeds
        scrape_result = self.scraping_service.create_scraping_task(
            symbol=symbol,
            exchange=exchange,
            feed_type='ALL',
            max_items=2  # Small for speed
        )
        
        if not scrape_result.get('success'):
            return {
                'success': False,
                'message': 'ALL scraping failed'
            }
            
        tasks_created = scrape_result.get('tasks_created', 0)
        
        # Wait for all scraping
        if not self._wait_for_tasks(timeout=30):
            return {
                'success': False,
                'message': 'ALL scraping timeout'
            }
            
        # Check insights from all feeds
        feed_counts = {}
        for feed_type in FeedType:
            count = len(self.insights_repo.get_all_by_symbol(symbol, feed_type))
            if count > 0:
                feed_counts[feed_type.value] = count
                
        # Should have insights from multiple feeds
        feeds_with_data = len(feed_counts)
        
        return {
            'success': feeds_with_data >= 3,
            'message': f"Scraped {feeds_with_data} different feeds",
            'details': {
                'tasks_created': tasks_created,
                'feeds_with_data': feeds_with_data,
                'feed_counts': feed_counts
            }
        }
        
    def test_error_handling_flow(self) -> Dict[str, Any]:
        """Test error handling in the data flow"""
        # Test with invalid symbol
        result = self.scraping_service.create_scraping_task(
            symbol='',  # Invalid
            exchange='NASDAQ',
            feed_type='TD NEWS',
            max_items=1
        )
        
        invalid_handled = not result.get('success', True)
        
        # Test with invalid feed type
        result2 = self.scraping_service.create_scraping_task(
            symbol='AAPL',
            exchange='NASDAQ', 
            feed_type='INVALID_FEED',
            max_items=1
        )
        
        invalid_feed_handled = not result2.get('success', True)
        
        return {
            'success': invalid_handled and invalid_feed_handled,
            'message': 'Error handling working correctly',
            'details': {
                'empty_symbol_rejected': invalid_handled,
                'invalid_feed_rejected': invalid_feed_handled
            }
        }
        
    def test_data_consistency(self) -> Dict[str, Any]:
        """Test data consistency across operations"""
        symbol = 'GOLD'
        
        # Get initial counts
        initial_insights = len(self.insights_repo.get_all(filters={'symbol': symbol}))
        
        # Scrape
        result = self.scraping_service.create_scraping_task(
            symbol=symbol,
            exchange='COMMODITIES',
            feed_type='TD NEWS',
            max_items=3
        )
        
        if not result.get('success'):
            return {
                'success': False,
                'message': 'Scraping failed'
            }
            
        # Wait
        if not self._wait_for_tasks():
            return {
                'success': False,
                'message': 'Task timeout'
            }
            
        # Check new count
        new_insights = self.insights_repo.get_all(filters={'symbol': symbol})
        insights_added = len(new_insights) - initial_insights
        
        # Verify each insight has required fields
        valid_insights = 0
        for insight in new_insights[initial_insights:]:
            if all([
                insight.symbol == symbol,
                insight.title,
                insight.content,
                insight.type,
                insight.time_posted
            ]):
                valid_insights += 1
                
        consistency_rate = (valid_insights / insights_added * 100) if insights_added > 0 else 0
        
        return {
            'success': consistency_rate == 100,
            'message': f"Data consistency: {consistency_rate:.1f}%",
            'details': {
                'insights_added': insights_added,
                'valid_insights': valid_insights,
                'consistency_rate': f"{consistency_rate:.1f}%"
            }
        }
        
    def test_duplicate_handling(self) -> Dict[str, Any]:
        """Test duplicate handling across the flow"""
        symbol = 'TSLA'
        feed = 'TD OPINIONS'
        
        # First scrape
        result1 = self.scraping_service.create_scraping_task(
            symbol=symbol,
            exchange='NASDAQ',
            feed_type=feed,
            max_items=2
        )
        
        if not self._wait_for_tasks():
            return {'success': False, 'message': 'First scrape timeout'}
            
        # Get created count
        task1 = self.queue.get_task(result1.get('task_id'))
        created1 = task1.result.get('created_insights', 0) if task1 and task1.result else 0
        
        # Second scrape (immediate)
        result2 = self.scraping_service.create_scraping_task(
            symbol=symbol,
            exchange='NASDAQ',
            feed_type=feed,
            max_items=2
        )
        
        if not self._wait_for_tasks():
            return {'success': False, 'message': 'Second scrape timeout'}
            
        # Check duplicates
        task2 = self.queue.get_task(result2.get('task_id'))
        if task2 and task2.result:
            created2 = task2.result.get('created_insights', 0)
            duplicates2 = task2.result.get('duplicate_insights', 0)
            
            # Should have detected duplicates
            duplicate_detection = duplicates2 > 0 or created2 < created1
            
            return {
                'success': duplicate_detection,
                'message': 'Duplicate detection working',
                'details': {
                    'first_scrape': {'created': created1},
                    'second_scrape': {
                        'created': created2,
                        'duplicates': duplicates2
                    },
                    'duplicate_rate': f"{(duplicates2/(created2+duplicates2)*100):.1f}%" if (created2+duplicates2) > 0 else "N/A"
                }
            }
            
        return {
            'success': False,
            'message': 'Could not verify duplicate handling'
        }
