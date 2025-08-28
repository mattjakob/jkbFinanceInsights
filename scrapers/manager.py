"""
/**
 * 
 *  ┌─────────────────────────────────────┐
 *  │        SCRAPER MANAGER              │
 *  └─────────────────────────────────────┘
 *  Orchestrates scrapers and database operations
 * 
 *  Manages scraper instances, handles data fetching,
 *  and coordinates database writes through repositories.
 * 
 *  Parameters:
 *  - None
 * 
 *  Returns:
 *  - ScraperManager instance
 * 
 *  Notes:
 *  - Decouples scrapers from database operations
 *  - Provides unified interface for all scrapers
 */
"""

from typing import List, Dict, Any, Type, Optional
from datetime import datetime

from .base import BaseScraper
from .tradingview_news import TradingViewNewsScraper
from .tradingview_ideas_recent import TradingViewIdeasRecentScraper
from .tradingview_ideas_popular import TradingViewIdeasPopularScraper
from .tradingview_opinions import TradingViewOpinionsScraper
from core import FeedType, InsightModel, ScrapedItem
from data import InsightsRepository
from debugger import debug_info, debug_success, debug_error, debug_warning


class ScraperManager:
    """
     ┌─────────────────────────────────────┐
     │        SCRAPERMANAGER               │
     └─────────────────────────────────────┘
     Manages scraper instances and operations
     
     Provides a unified interface for fetching data from
     any configured scraper and storing it in the database.
    """
    
    def __init__(self, repository: Optional[InsightsRepository] = None):
        self.repository = repository or InsightsRepository()
        self._scrapers: Dict[FeedType, Type[BaseScraper]] = {
            FeedType.TD_NEWS: TradingViewNewsScraper,
            FeedType.TD_IDEAS_RECENT: TradingViewIdeasRecentScraper,
            FeedType.TD_IDEAS_POPULAR: TradingViewIdeasPopularScraper,
            FeedType.TD_OPINIONS: TradingViewOpinionsScraper
        }
        self._instances: Dict[FeedType, BaseScraper] = {}
    
    def get_scraper(self, feed_type: FeedType) -> BaseScraper:
        """
         ┌─────────────────────────────────────┐
         │         GET_SCRAPER                 │
         └─────────────────────────────────────┘
         Get or create scraper instance
         
         Returns a scraper instance for the specified feed type,
         creating it if necessary.
         
         Parameters:
         - feed_type: Type of feed to scrape
         
         Returns:
         - BaseScraper instance
         
         Notes:
         - Caches instances for reuse
         - Raises ValueError if feed type not supported
        """
        if feed_type not in self._scrapers:
            raise ValueError(f"No scraper configured for feed type: {feed_type.value}")
        
        if feed_type not in self._instances:
            scraper_class = self._scrapers[feed_type]
            self._instances[feed_type] = scraper_class()
        
        return self._instances[feed_type]
    
    def fetch_and_store(self, 
                       feed_type: FeedType,
                       symbol: str,
                       exchange: str,
                       limit: int = 50) -> Dict[str, Any]:
        """
         ┌─────────────────────────────────────┐
         │       FETCH_AND_STORE               │
         └─────────────────────────────────────┘
         Fetch data and store in database
         
         Fetches data from the specified scraper and stores
         it in the database, handling duplicates.
         
         Parameters:
         - feed_type: Type of feed to fetch
         - symbol: Trading symbol
         - exchange: Exchange name
         - limit: Maximum items to fetch
         
         Returns:
         - Dictionary with operation results
         
         Notes:
         - Returns statistics about created/duplicate items
         - Handles all database operations
        """
        try:
            # Get scraper
            scraper = self.get_scraper(feed_type)
            
            # Fetch items
            scraped_items = scraper.fetch(symbol, exchange, limit)
            
            if not scraped_items:
                return {
                    'success': True,
                    'message': f'No items found for {feed_type.value}',
                    'processed_items': 0,
                    'created_insights': 0,
                    'duplicate_insights': 0,
                    'failed_items': 0,
                    'results': []
                }
            
            # Process and store each item
            results = []
            created_count = 0
            duplicate_count = 0
            failed_count = 0
            
            for item in scraped_items:
                result = self._store_item(item, feed_type)
                results.append(result)
                
                if result['status'] == 'created':
                    created_count += 1
                elif result['status'] == 'duplicate':
                    duplicate_count += 1
                else:
                    failed_count += 1
            
            # Log summary
            if created_count > 0:
                debug_success(f"Created {created_count} new insights for {feed_type.value}")
            if duplicate_count > 0:
                debug_info(f"Found {duplicate_count} duplicate insights")
            if failed_count > 0:
                debug_warning(f"Failed to process {failed_count} items")
            
            return {
                'success': True,
                'message': f'Fetch completed for {feed_type.value}',
                'processed_items': len(scraped_items),
                'created_insights': created_count,
                'duplicate_insights': duplicate_count,
                'failed_items': failed_count,
                'results': results,
                'scraper_type': feed_type.value,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            debug_error(f"Fetch and store failed: {str(e)}")
            return {
                'success': False,
                'message': f'Fetch failed: {str(e)}',
                'processed_items': 0,
                'created_insights': 0,
                'duplicate_insights': 0,
                'failed_items': 0,
                'results': [],
                'timestamp': datetime.now().isoformat()
            }
    
    def fetch_all_feeds(self,
                       symbol: str,
                       exchange: str,
                       limit: int = 50) -> Dict[str, Any]:
        """
         ┌─────────────────────────────────────┐
         │        FETCH_ALL_FEEDS              │
         └─────────────────────────────────────┘
         Fetch from all available scrapers
         
         Runs all configured scrapers for the given symbol
         and aggregates results.
         
         Parameters:
         - symbol: Trading symbol
         - exchange: Exchange name
         - limit: Maximum items per scraper
         
         Returns:
         - Aggregated results from all scrapers
        """
        all_results = []
        total_processed = 0
        total_created = 0
        total_duplicates = 0
        total_failed = 0
        
        for feed_type in self._scrapers.keys():
            debug_info(f"Fetching from {feed_type.value}")
            result = self.fetch_and_store(feed_type, symbol, exchange, limit)
            
            if result['success']:
                all_results.extend(result['results'])
                total_processed += result['processed_items']
                total_created += result['created_insights']
                total_duplicates += result['duplicate_insights']
                total_failed += result['failed_items']
        
        return {
            'success': True,
            'message': 'Fetched from all feed types',
            'processed_items': total_processed,
            'created_insights': total_created,
            'duplicate_insights': total_duplicates,
            'failed_items': total_failed,
            'results': all_results,
            'timestamp': datetime.now().isoformat()
        }
    
    def _store_item(self, item: ScrapedItem, feed_type: FeedType) -> Dict[str, Any]:
        """
         ┌─────────────────────────────────────┐
         │         _STORE_ITEM                 │
         └─────────────────────────────────────┘
         Store individual scraped item
         
         Converts ScrapedItem to InsightModel and stores
         in database through repository.
         
         Parameters:
         - item: ScrapedItem to store
         - feed_type: Feed type for categorization
         
         Returns:
         - Dictionary with storage result
        """
        try:
            # Convert to InsightModel
            insight = item.to_insight_model(feed_type)
            
            # Store in database
            insight_id, is_new = self.repository.create(insight)
            
            return {
                'title': item.title,
                'symbol': item.symbol,
                'exchange': item.exchange,
                'insight_id': insight_id,
                'status': 'created' if is_new else 'duplicate',
                'timestamp': item.timestamp.isoformat()
            }
            
        except Exception as e:
            debug_error(f"Failed to store item: {str(e)}")
            return {
                'title': item.title,
                'status': 'failed',
                'error': str(e)
            }
