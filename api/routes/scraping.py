"""
/**
 * 
 *  ┌─────────────────────────────────────┐
 *  │        SCRAPING ROUTES              │
 *  └─────────────────────────────────────┘
 *  API routes for data scraping operations
 * 
 *  Provides endpoints for fetching new data from external
 *  sources using the refactored scraper system.
 * 
 *  Parameters:
 *  - None
 * 
 *  Returns:
 *  - FastAPI router with scraping endpoints
 * 
 *  Notes:
 *  - Uses ScraperManager for orchestration
 *  - Supports individual and all-feeds scraping
 */
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any

from core import FeedType
from scrapers import ScraperManager
from symbol_validator import exchange_manager
from debugger import debug_info, debug_error

# Create router
router = APIRouter(prefix="/api/scraping", tags=["scraping"])

# Initialize scraper manager
scraper_manager = ScraperManager()


class FetchRequest(BaseModel):
    """Request model for fetching data"""
    symbol: str
    exchange: str
    feed_type: str
    max_items: int = 50


@router.post("/fetch")
async def fetch_insights(request: FetchRequest):
    """
     ┌─────────────────────────────────────┐
     │         FETCH_INSIGHTS              │
     └─────────────────────────────────────┘
     Fetch new insights from external sources
     
     Uses the specified scraper to fetch new data and
     store it in the database.
    """
    try:
        # Handle ALL feed type
        if request.feed_type == "ALL" or not request.feed_type:
            debug_info("Fetching from all feed types")
            result = scraper_manager.fetch_all_feeds(
                symbol=request.symbol,
                exchange=request.exchange,
                limit=request.max_items
            )
        else:
            # Single feed type
            try:
                feed_type = FeedType(request.feed_type)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid feed type: {request.feed_type}"
                )
            
            result = scraper_manager.fetch_and_store(
                feed_type=feed_type,
                symbol=request.symbol,
                exchange=request.exchange,
                limit=request.max_items
            )
        
        return result
        
    except HTTPException:
        raise
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


@router.get("/feeds")
async def get_available_feeds():
    """
     ┌─────────────────────────────────────┐
     │       GET_AVAILABLE_FEEDS           │
     └─────────────────────────────────────┘
     Get list of available feed types
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


@router.get("/symbols/search")
async def search_symbols(query: str):
    """
     ┌─────────────────────────────────────┐
     │         SEARCH_SYMBOLS              │
     └─────────────────────────────────────┘
     Search for trading symbols using TradingView API
     
     Returns list of matching symbols with exchange information
     and suggested exchange for each symbol.
    """
    try:
        if not query or len(query.strip()) < 1:
            return {"suggestions": []}
        
        # Search symbols using exchange manager
        results = exchange_manager.search_symbol(query.strip())
        
        # Process results to match frontend expectations
        suggestions = []
        seen_symbols = set()
        
        # Group results by symbol to show multiple exchange options
        symbol_groups = {}
        for result in results:
            symbol = result.symbol.upper()
            if symbol not in symbol_groups:
                symbol_groups[symbol] = []
            symbol_groups[symbol].append(result)
        
        # Show multiple exchange options for each symbol, respecting TradingView's ranking
        # No hardcoded preferences - let TradingView's API determine what's most relevant
        for symbol, group in list(symbol_groups.items())[:5]:  # Limit to 5 unique symbols
            # For symbols with multiple exchanges, show up to 6 options
            # For symbols with single exchange, show just that one
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



