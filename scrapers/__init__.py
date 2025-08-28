"""
Scraper modules for JKB Finance Insights

This package contains all data scraping functionality,
with a base class for consistency and specific implementations
for each data source.
"""

from .base import BaseScraper
from .manager import ScraperManager
from .tradingview_news import TradingViewNewsScraper
from .tradingview_ideas_recent import TradingViewIdeasRecentScraper
from .tradingview_ideas_popular import TradingViewIdeasPopularScraper
from .tradingview_opinions import TradingViewOpinionsScraper

__all__ = [
    'BaseScraper',
    'ScraperManager',
    'TradingViewNewsScraper',
    'TradingViewIdeasRecentScraper',
    'TradingViewIdeasPopularScraper',
    'TradingViewOpinionsScraper'
]