"""
 ┌─────────────────────────────────────┐
 │           BASE_TEST                 │
 └─────────────────────────────────────┘
 Base test class with common utilities
 
 Provides shared functionality for all test classes including timing,
 logging, and result aggregation.
"""

import time
import traceback
from typing import Dict, List, Any, Callable, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

class TestStatus(Enum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    ERROR = "ERROR"

@dataclass
class TestResult:
    test_name: str
    status: TestStatus
    duration: float
    message: str = ""
    error: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'test_name': self.test_name,
            'status': self.status.value,
            'duration': round(self.duration, 3),
            'message': self.message,
            'error': self.error,
            'details': self.details
        }

@dataclass 
class TestSuite:
    name: str
    tests: List[TestResult] = field(default_factory=list)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    @property
    def duration(self) -> float:
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0
    
    @property
    def passed(self) -> int:
        return len([t for t in self.tests if t.status == TestStatus.PASSED])
    
    @property
    def failed(self) -> int:
        return len([t for t in self.tests if t.status == TestStatus.FAILED])
    
    @property
    def errors(self) -> int:
        return len([t for t in self.tests if t.status == TestStatus.ERROR])
    
    @property
    def skipped(self) -> int:
        return len([t for t in self.tests if t.status == TestStatus.SKIPPED])
    
    @property
    def total(self) -> int:
        return len(self.tests)
    
    @property
    def success_rate(self) -> float:
        if self.total == 0:
            return 0.0
        return (self.passed / self.total) * 100

class BaseTest:
    """
     ┌─────────────────────────────────────┐
     │          BASETEST                   │
     └─────────────────────────────────────┘
     Base class for all test suites
     
     Provides common test utilities and result tracking.
    """
    
    def __init__(self, name: str):
        self.name = name
        self.suite = TestSuite(name=name)
        self._setup_complete = False
        
    def setup(self):
        """Override to perform test setup"""
        self._setup_complete = True
        
    def teardown(self):
        """Override to perform test cleanup"""
        pass
        
    def run_test(self, test_func: Callable, test_name: str, **kwargs) -> TestResult:
        """
         ┌─────────────────────────────────────┐
         │          RUN_TEST                   │
         └─────────────────────────────────────┘
         Execute a single test and capture results
         
         Handles timing, error capture, and result recording.
         
         Parameters:
         - test_func: Test function to execute
         - test_name: Name for reporting
         - **kwargs: Arguments to pass to test function
         
         Returns:
         - TestResult with execution details
        """
        print(f"\n🧪 Running: {test_name}")
        start_time = time.time()
        
        try:
            # Ensure setup is complete
            if not self._setup_complete:
                self.setup()
            
            # Run the test
            result = test_func(**kwargs)
            duration = time.time() - start_time
            
            # Determine status based on result
            if isinstance(result, dict):
                if result.get('success', False):
                    status = TestStatus.PASSED
                    message = result.get('message', 'Test passed')
                    details = result.get('details', {})
                else:
                    status = TestStatus.FAILED
                    message = result.get('message', 'Test failed')
                    details = result.get('details', {})
            elif isinstance(result, bool):
                status = TestStatus.PASSED if result else TestStatus.FAILED
                message = 'Test passed' if result else 'Test failed'
                details = {}
            else:
                status = TestStatus.PASSED
                message = 'Test completed'
                details = {'result': result}
                
            test_result = TestResult(
                test_name=test_name,
                status=status,
                duration=duration,
                message=message,
                details=details
            )
            
            # Print result
            status_icon = "✅" if status == TestStatus.PASSED else "❌"
            print(f"{status_icon} {test_name}: {message} ({duration:.3f}s)")
            
        except Exception as e:
            duration = time.time() - start_time
            test_result = TestResult(
                test_name=test_name,
                status=TestStatus.ERROR,
                duration=duration,
                message=f"Test error: {str(e)}",
                error=traceback.format_exc()
            )
            print(f"💥 {test_name}: ERROR - {str(e)} ({duration:.3f}s)")
            
        self.suite.tests.append(test_result)
        return test_result
        
    def assert_equals(self, actual: Any, expected: Any, message: str = "") -> Dict[str, Any]:
        """Assert two values are equal"""
        success = actual == expected
        if not success:
            message = message or f"Expected {expected}, got {actual}"
        return {
            'success': success,
            'message': message,
            'details': {
                'actual': actual,
                'expected': expected
            }
        }
        
    def assert_greater(self, actual: Any, threshold: Any, message: str = "") -> Dict[str, Any]:
        """Assert value is greater than threshold"""
        success = actual > threshold
        if not success:
            message = message or f"Expected > {threshold}, got {actual}"
        return {
            'success': success,
            'message': message,
            'details': {
                'actual': actual,
                'threshold': threshold
            }
        }
        
    def assert_contains(self, container: Any, item: Any, message: str = "") -> Dict[str, Any]:
        """Assert container contains item"""
        success = item in container
        if not success:
            message = message or f"Expected {item} in {container}"
        return {
            'success': success,
            'message': message,
            'details': {
                'container': str(container)[:100],
                'item': item
            }
        }
        
    def assert_not_none(self, value: Any, message: str = "") -> Dict[str, Any]:
        """Assert value is not None"""
        success = value is not None
        if not success:
            message = message or "Expected non-None value"
        return {
            'success': success,
            'message': message,
            'details': {
                'value': value
            }
        }
        
    def run_all(self) -> TestSuite:
        """Run all tests in the suite"""
        self.suite.start_time = datetime.now()
        
        # Run all test methods (those starting with test_)
        test_methods = [
            method for method in dir(self) 
            if method.startswith('test_') and callable(getattr(self, method))
        ]
        
        print(f"\n{'='*60}")
        print(f"🚀 Running {self.name} ({len(test_methods)} tests)")
        print(f"{'='*60}")
        
        for method_name in test_methods:
            method = getattr(self, method_name)
            # Convert method name to readable format
            test_name = method_name.replace('test_', '').replace('_', ' ').title()
            self.run_test(method, test_name)
            
        self.suite.end_time = datetime.now()
        self.teardown()
        
        return self.suite
        
    def print_summary(self):
        """Print test suite summary"""
        print(f"\n{'='*60}")
        print(f"📊 {self.name} Summary")
        print(f"{'='*60}")
        print(f"Total Tests: {self.suite.total}")
        print(f"✅ Passed: {self.suite.passed}")
        print(f"❌ Failed: {self.suite.failed}")
        print(f"💥 Errors: {self.suite.errors}")
        print(f"⏭️  Skipped: {self.suite.skipped}")
        print(f"Success Rate: {self.suite.success_rate:.1f}%")
        print(f"Duration: {self.suite.duration:.3f}s")
        
        # Print failed test details
        if self.suite.failed > 0 or self.suite.errors > 0:
            print(f"\n{'='*60}")
            print("Failed Tests:")
            for test in self.suite.tests:
                if test.status in [TestStatus.FAILED, TestStatus.ERROR]:
                    print(f"\n❌ {test.test_name}:")
                    print(f"   Message: {test.message}")
                    if test.error:
                        print(f"   Error:\n{test.error}")
                    if test.details:
                        print(f"   Details: {test.details}")
