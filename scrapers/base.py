"""
/**
 * 
 *  ┌─────────────────────────────────────┐
 *  │          BASE SCRAPER               │
 *  └─────────────────────────────────────┘
 *  Abstract base class for all scrapers
 * 
 *  Defines the interface and common functionality for all
 *  scraper implementations, ensuring consistency.
 * 
 *  Parameters:
 *  - None
 * 
 *  Returns:
 *  - Base scraper class for inheritance
 * 
 *  Notes:
 *  - All scrapers must implement fetch_items method
 *  - Provides common utilities for HTTP requests
 */
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from core import ScrapedItem, FeedType
from config import SCRAPER_TIMEOUT, SCRAPER_MAX_RETRIES, SCRAPER_RETRY_DELAY
from debugger import debug_info, debug_error, debug_warning


class BaseScraper(ABC):
    """
     ┌─────────────────────────────────────┐
     │          BASESCRAPER                │
     └─────────────────────────────────────┘
     Abstract base class for all scrapers
     
     Provides common functionality and enforces interface
     for scraper implementations.
     
     Parameters:
     - feed_type: Type of feed this scraper handles
     
     Returns:
     - BaseScraper instance
     
     Notes:
     - Subclasses must implement fetch_items()
     - Provides HTTP session with retry logic
    """
    
    def __init__(self, feed_type: FeedType):
        self.feed_type = feed_type
        self.session = self._create_session()
        self.last_fetch_time = None
        
    def _create_session(self) -> requests.Session:
        """
         ┌─────────────────────────────────────┐
         │        _CREATE_SESSION              │
         └─────────────────────────────────────┘
         Create HTTP session with retry logic
         
         Sets up a requests session with automatic retries
         and timeout configuration.
         
         Returns:
         - Configured requests.Session
        """
        session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=SCRAPER_MAX_RETRIES,
            backoff_factor=SCRAPER_RETRY_DELAY,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Set default headers
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Referer': 'https://www.tradingview.com/',
        })
        
        return session
    
    def fetch(self, symbol: str, exchange: str, limit: int = 50) -> List[ScrapedItem]:
        """
         ┌─────────────────────────────────────┐
         │             FETCH                   │
         └─────────────────────────────────────┘
         Public interface for fetching data
         
         Wraps the abstract fetch_items method with error
         handling and timing.
         
         Parameters:
         - symbol: Trading symbol
         - exchange: Exchange name
         - limit: Maximum items to fetch
         
         Returns:
         - List of ScrapedItem instances
         
         Notes:
         - Updates last_fetch_time on success
         - Returns empty list on error
        """
        try:
            debug_info(f"Starting {self.feed_type.value} fetch for {exchange}:{symbol} (max: {limit})")
            
            items = self.fetch_items(symbol, exchange, limit)
            
            self.last_fetch_time = datetime.now()
            
            debug_info(f"{self.feed_type.value} fetch completed: {len(items)} items retrieved (requested: {limit})")
            if len(items) < limit:
                debug_warning(f"{self.feed_type.value}: Retrieved {len(items)} items, {limit - len(items)} fewer than requested")
            return items
            
        except Exception as e:
            debug_error(f"{self.feed_type.value} fetch failed: {str(e)}")
            return []
    
    @abstractmethod
    def fetch_items(self, symbol: str, exchange: str, limit: int) -> List[ScrapedItem]:
        """
         ┌─────────────────────────────────────┐
         │          FETCH_ITEMS                │
         └─────────────────────────────────────┘
         Abstract method to fetch items
         
         Must be implemented by subclasses to fetch data
         from the specific source.
         
         Parameters:
         - symbol: Trading symbol
         - exchange: Exchange name
         - limit: Maximum items to fetch
         
         Returns:
         - List of ScrapedItem instances
         
         Notes:
         - Implementation should handle source-specific logic
         - Should convert to ScrapedItem format
        """
        pass
    
    def make_request(self, url: str, **kwargs) -> requests.Response:
        """
         ┌─────────────────────────────────────┐
         │         MAKE_REQUEST                │
         └─────────────────────────────────────┘
         Make HTTP request with configured session
         
         Utility method for subclasses to make HTTP requests
         with automatic retry and timeout handling.
         
         Parameters:
         - url: URL to request
         - **kwargs: Additional arguments for requests.get()
         
         Returns:
         - requests.Response object
         
         Notes:
         - Uses configured timeout if not specified
         - Raises on HTTP errors
        """
        if 'timeout' not in kwargs:
            kwargs['timeout'] = SCRAPER_TIMEOUT
            
        response = self.session.get(url, **kwargs)
        response.raise_for_status()
        return response



