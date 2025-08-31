"""
JKB Finance Insights Test Suite

This package contains comprehensive tests for core application capabilities.
Run these tests after any significant refactoring or new functionality.
"""

from .test_runner import TestRunner
from .test_scrapers import ScraperTests
from .test_analysis import AnalysisTests
from .test_reports import ReportTests
from .test_data_flow import DataFlowTests

__all__ = [
    'TestRunner',
    'ScraperTests',
    'AnalysisTests', 
    'ReportTests',
    'DataFlowTests'
]
