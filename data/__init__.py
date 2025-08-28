"""
Data access layer for JKB Finance Insights

This module provides repository pattern implementations
for clean data access without exposing SQL to business logic.
"""

from .repositories.insights import InsightsRepository

__all__ = [
    'InsightsRepository'
]



