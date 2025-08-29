"""
Repository implementations for data access
"""

from .insights import InsightsRepository
from .reports import ReportsRepository, get_reports_repository

__all__ = [
    'InsightsRepository',
    'ReportsRepository',
    'get_reports_repository'
]



