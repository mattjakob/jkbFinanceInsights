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

from services import InsightScrapingService, SymbolService
from debugger import debug_info, debug_error

# Create router
router = APIRouter(prefix="/api/scraping", tags=["scraping"])

# Service instances
scraping_service = InsightScrapingService()
symbol_service = SymbolService()


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
        return await scraping_service.create_scraping_task(
            symbol=request.symbol,
            exchange=request.exchange,
            feed_type=request.feed_type,
            max_items=request.max_items
        )
        
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
    return scraping_service.get_available_feeds()


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
        return symbol_service.search_symbols(query)
        
    except Exception as e:
        debug_error(f"Symbol search failed: {e}")
        return {"suggestions": [], "error": str(e)}



