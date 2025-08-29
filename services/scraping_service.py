"""
/**
 * 
 *  ┌─────────────────────────────────────┐
 *  │       SCRAPING SERVICE              │
 *  └─────────────────────────────────────┘
 *  Business logic for scraping operations
 * 
 *  Coordinates data scraping operations and provides
 *  business logic layer for external data fetching.
 * 
 *  Parameters:
 *  - scraper_manager: ScraperManager instance
 * 
 *  Returns:
 *  - ScrapingService instance
 * 
 *  Notes:
 *  - Handles scraping coordination and validation
 *  - Manages symbol validation and feed selection
 */
"""

from typing import Dict, Any, List
from scrapers import ScraperManager
from symbol_validator import exchange_manager
from core import FeedType
from debugger import debug_info, debug_error


class ScrapingService:
    """
     ┌─────────────────────────────────────┐
     │       SCRAPINGSERVICE               │
     └─────────────────────────────────────┘
     Business logic service for scraping
     
     Provides high-level operations for data scraping,
     implementing business rules and validation.
    """
    
    def __init__(self, scraper_manager: ScraperManager = None):
        self.scraper_manager = scraper_manager or ScraperManager()
    
    def fetch_insights(self, 
                      symbol: str, 
                      exchange: str, 
                      feed_type: str, 
                      max_items: int = 50) -> Dict[str, Any]:
        """
         ┌─────────────────────────────────────┐
         │       FETCH_INSIGHTS                │
         └─────────────────────────────────────┘
         Fetch insights from external sources
         
         Parameters:
         - symbol: Trading symbol
         - exchange: Exchange name
         - feed_type: Feed type or "ALL"
         - max_items: Maximum items to fetch
         
         Returns:
         - Dictionary with fetch results
        """
        try:
            # Handle ALL feed type
            if feed_type == "ALL" or not feed_type:
                debug_info("Fetching from all feed types")
                result = self.scraper_manager.fetch_all_feeds(
                    symbol=symbol,
                    exchange=exchange,
                    limit=max_items
                )
            else:
                # Single feed type
                try:
                    ft = FeedType(feed_type)
                except ValueError:
                    return {
                        "success": False,
                        "message": f"Invalid feed type: {feed_type}",
                        "processed_items": 0,
                        "created_insights": 0,
                        "duplicate_insights": 0,
                        "failed_items": 0,
                        "results": []
                    }
                
                result = self.scraper_manager.fetch_and_store(
                    feed_type=ft,
                    symbol=symbol,
                    exchange=exchange,
                    limit=max_items
                )
            
            return result
            
        except Exception as e:
            debug_error(f"Fetch failed: {e}")
            return {
                "success": False,
                "message": f"Fetch failed: {str(e)}",
                "processed_items": 0,
                "created_insights": 0,
                "duplicate_insights": 0,
                "failed_items": 0,
                "results": []
            }
    
    def get_available_feeds(self) -> List[Dict[str, str]]:
        """
         ┌─────────────────────────────────────┐
         │      GET_AVAILABLE_FEEDS            │
         └─────────────────────────────────────┘
         Get list of available feed types
         
         Returns:
         - List of feed type dictionaries
        """
        feeds = [
            {
                "name": feed_type.value,
                "value": feed_type.value,
                "description": f"{feed_type.value} feed"
            }
            for feed_type in FeedType
        ]
        
        # Add "ALL" option
        feeds.insert(0, {
            "name": "ALL",
            "value": "ALL",
            "description": "Fetch from all available feeds"
        })
        
        return feeds
    
    def search_symbols(self, query: str) -> Dict[str, Any]:
        """
         ┌─────────────────────────────────────┐
         │       SEARCH_SYMBOLS                │
         └─────────────────────────────────────┘
         Search for trading symbols
         
         Parameters:
         - query: Search query string
         
         Returns:
         - Dictionary with symbol suggestions
        """
        try:
            if not query or len(query.strip()) < 1:
                return {"suggestions": []}
            
            # Search symbols using exchange manager
            results = exchange_manager.search_symbol(query.strip())
            
            # Process results to match frontend expectations
            suggestions = []
            
            # Group results by symbol to show multiple exchange options
            symbol_groups = {}
            for result in results:
                symbol = result.symbol.upper()
                if symbol not in symbol_groups:
                    symbol_groups[symbol] = []
                symbol_groups[symbol].append(result)
            
            # Show multiple exchange options for each symbol, respecting TradingView's ranking
            for symbol, group in list(symbol_groups.items())[:5]:  # Limit to 5 unique symbols
                # For symbols with multiple exchanges, show up to 6 options
                if len(group) > 1:
                    # Show multiple exchange options, respecting TradingView's order
                    # Filter for spot trading first (most relevant for users)
                    spot_results = [r for r in group if r.type == 'spot']
                    other_results = [r for r in group if r.type != 'spot']
                    
                    # Combine spot results first, then others, respecting TradingView's ranking
                    all_results = spot_results + other_results
                    top_exchanges = all_results[:6]
                    
                    for result in top_exchanges:
                        suggestions.append({
                            "symbol": result.symbol,
                            "description": result.description,
                            "exchange": result.exchange,
                            "type": result.type,
                            "provider_id": result.provider_id
                        })
                else:
                    # Single exchange result
                    best_result = group[0]
                    suggestions.append({
                        "symbol": best_result.symbol,
                        "description": best_result.description,
                        "exchange": best_result.exchange,
                        "type": best_result.type,
                        "provider_id": best_result.provider_id
                    })
            
            return {"suggestions": suggestions}
            
        except Exception as e:
            debug_error(f"Symbol search failed: {e}")
            return {"suggestions": [], "error": str(e)}
