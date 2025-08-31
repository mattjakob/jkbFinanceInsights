"""
 ┌─────────────────────────────────────┐
 │          TEST_RUNNER                │
 └─────────────────────────────────────┘
 Main test runner and orchestrator
 
 Provides unified interface to run all tests and generate reports.
"""

import sys
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .base_test import TestSuite
from .test_scrapers import ScraperTests
from .test_analysis import AnalysisTests
from .test_reports import ReportTests
from .test_data_flow import DataFlowTests

class TestRunner:
    """
     ┌─────────────────────────────────────┐
     │         TESTRUNNER                  │
     └─────────────────────────────────────┘
     Orchestrate test execution and reporting
     
     Manages test suite execution and provides summary results.
    """
    
    def __init__(self):
        self.test_classes = {
            'scrapers': ScraperTests,
            'analysis': AnalysisTests,
            'reports': ReportTests,
            'data_flow': DataFlowTests
        }
        self.results = []
        
    def run_suite(self, suite_name: str) -> Optional[TestSuite]:
        """Run a specific test suite"""
        if suite_name not in self.test_classes:
            print(f"❌ Unknown test suite: {suite_name}")
            print(f"Available suites: {', '.join(self.test_classes.keys())}")
            return None
            
        print(f"\n🚀 Starting {suite_name} tests...")
        test_class = self.test_classes[suite_name]
        test_instance = test_class()
        
        try:
            suite_result = test_instance.run_all()
            test_instance.print_summary()
            return suite_result
        except Exception as e:
            print(f"💥 Error running {suite_name}: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
            
    def run_all(self, exclude: List[str] = None) -> Dict[str, Any]:
        """Run all test suites"""
        exclude = exclude or []
        start_time = datetime.now()
        
        print(f"\n{'='*80}")
        print(f"🧪 JKB Finance Insights - Comprehensive Test Suite")
        print(f"Started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*80}")
        
        for suite_name in self.test_classes:
            if suite_name in exclude:
                print(f"\n⏭️  Skipping {suite_name} tests (excluded)")
                continue
                
            result = self.run_suite(suite_name)
            if result:
                self.results.append(result)
                
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Generate summary
        summary = self._generate_summary(duration)
        self._print_final_summary(summary)
        
        return summary
        
    def run_specific(self, suite_name: str, test_name: str) -> bool:
        """Run a specific test within a suite"""
        if suite_name not in self.test_classes:
            print(f"❌ Unknown test suite: {suite_name}")
            return False
            
        test_class = self.test_classes[suite_name]
        test_instance = test_class()
        
        # Find test method
        test_method_name = f"test_{test_name.replace(' ', '_').lower()}"
        if not hasattr(test_instance, test_method_name):
            print(f"❌ Test '{test_name}' not found in {suite_name}")
            # List available tests
            available = [
                m.replace('test_', '').replace('_', ' ').title()
                for m in dir(test_instance) 
                if m.startswith('test_')
            ]
            print(f"Available tests: {', '.join(available)}")
            return False
            
        # Run single test
        test_instance.setup()
        test_method = getattr(test_instance, test_method_name)
        result = test_instance.run_test(test_method, test_name)
        test_instance.teardown()
        
        # Print result
        print(f"\n{'='*60}")
        print(f"Test: {test_name}")
        print(f"Status: {result.status.value}")
        print(f"Duration: {result.duration:.3f}s")
        if result.message:
            print(f"Message: {result.message}")
        if result.details:
            print(f"Details: {json.dumps(result.details, indent=2)}")
            
        return result.status.value == 'PASSED'
        
    def _generate_summary(self, duration: float) -> Dict[str, Any]:
        """Generate test summary"""
        total_tests = sum(suite.total for suite in self.results)
        total_passed = sum(suite.passed for suite in self.results)
        total_failed = sum(suite.failed for suite in self.results)
        total_errors = sum(suite.errors for suite in self.results)
        total_skipped = sum(suite.skipped for suite in self.results)
        
        suite_summaries = []
        for suite in self.results:
            suite_summaries.append({
                'name': suite.name,
                'total': suite.total,
                'passed': suite.passed,
                'failed': suite.failed,
                'errors': suite.errors,
                'skipped': suite.skipped,
                'success_rate': suite.success_rate,
                'duration': suite.duration
            })
            
        return {
            'total_suites': len(self.results),
            'total_tests': total_tests,
            'passed': total_passed,
            'failed': total_failed,
            'errors': total_errors,
            'skipped': total_skipped,
            'success_rate': (total_passed / total_tests * 100) if total_tests > 0 else 0,
            'duration': duration,
            'suites': suite_summaries
        }
        
    def _print_final_summary(self, summary: Dict[str, Any]):
        """Print final test summary"""
        print(f"\n{'='*80}")
        print(f"🏁 FINAL TEST SUMMARY")
        print(f"{'='*80}")
        print(f"Total Suites: {summary['total_suites']}")
        print(f"Total Tests: {summary['total_tests']}")
        print(f"✅ Passed: {summary['passed']}")
        print(f"❌ Failed: {summary['failed']}")
        print(f"💥 Errors: {summary['errors']}")
        print(f"⏭️  Skipped: {summary['skipped']}")
        print(f"Success Rate: {summary['success_rate']:.1f}%")
        print(f"Total Duration: {summary['duration']:.3f}s")
        
        # Suite breakdown
        print(f"\n{'='*80}")
        print("Suite Breakdown:")
        print(f"{'='*80}")
        for suite in summary['suites']:
            print(f"\n{suite['name']}:")
            print(f"  Tests: {suite['total']} | Passed: {suite['passed']} | Failed: {suite['failed']} | Errors: {suite['errors']}")
            print(f"  Success Rate: {suite['success_rate']:.1f}% | Duration: {suite['duration']:.3f}s")
            
        # Overall result
        print(f"\n{'='*80}")
        if summary['failed'] == 0 and summary['errors'] == 0:
            print("✅ ALL TESTS PASSED! 🎉")
        else:
            print("❌ SOME TESTS FAILED - Please review the results above")
        print(f"{'='*80}")


def run_quick_test():
    """Run a quick test suite for development"""
    runner = TestRunner()
    # Run only essential tests
    print("\n🚀 Running Quick Test Suite (scrapers only)...")
    runner.run_specific('scrapers', 'single_feed_basic')
    runner.run_specific('scrapers', 'item_count_accuracy')
    

def run_full_test():
    """Run complete test suite"""
    runner = TestRunner()
    runner.run_all()
    

async def run_fetch_test(item_count: int = 50):
    """Test fetching with specific item count"""
    runner = TestRunner()
    print(f"\n🔍 Testing fetch with {item_count} items...")
    
    # First run a custom test
    from services import InsightScrapingService
    from tasks import get_task_queue
    import time
    
    service = InsightScrapingService()
    queue = await get_task_queue()
    
    # Test with high item count
    print(f"\n📥 Creating scraping task for {item_count} items...")
    result = service.create_scraping_task(
        symbol='BTCUSD',
        exchange='BITSTAMP',
        feed_type='TD NEWS',
        max_items=item_count
    )
    
    print(f"Task created: {result.get('success')}")
    print(f"Task ID: {result.get('task_id')}")
    
    if result.get('success'):
        # Wait for completion
        print("\n⏳ Waiting for task completion...")
        task_id = result.get('task_id')
        
        for i in range(60):  # Wait up to 60 seconds
            task = queue.get_task(task_id)
            if task and task.status.value == 'completed':
                print(f"\n✅ Task completed!")
                if task.result:
                    print(f"Items processed: {task.result.get('processed_items', 0)}")
                    print(f"Items created: {task.result.get('created_insights', 0)}")
                    print(f"Duplicates found: {task.result.get('duplicate_insights', 0)}")
                    print(f"Failed items: {task.result.get('failed_items', 0)}")
                break
            elif task and task.status.value == 'failed':
                print(f"\n❌ Task failed!")
                print(f"Error: {task.error}")
                break
            # Remove blocking wait - async system processes immediately
            break
    

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Run JKB Finance Insights tests')
    parser.add_argument('--suite', type=str, help='Run specific test suite')
    parser.add_argument('--test', type=str, help='Run specific test (requires --suite)')
    parser.add_argument('--quick', action='store_true', help='Run quick test suite')
    parser.add_argument('--fetch-test', type=int, help='Test fetch with specific item count')
    
    args = parser.parse_args()
    
    if args.fetch_test:
        import asyncio
        asyncio.run(run_fetch_test(args.fetch_test))
    elif args.quick:
        run_quick_test()
    elif args.suite:
        runner = TestRunner()
        if args.test:
            runner.run_specific(args.suite, args.test)
        else:
            runner.run_suite(args.suite)
    else:
        run_full_test()
