"""
┌─────────────────────────────────────┐
│           SCRAPERS                  │
└─────────────────────────────────────┘

Scrapers package for financial data collection.

This package contains all scraper modules for collecting financial insights
from various sources while maintaining consistent data structures.
"""

from .feed_scraper import FeedScraper, create_scraper

__all__ = ['FeedScraper', 'create_scraper']
