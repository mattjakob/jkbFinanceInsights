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



