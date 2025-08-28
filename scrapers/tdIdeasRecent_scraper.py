"""
┌─────────────────────────────────────┐
│   TRADINGVIEW IDEAS RECENT SCRAPER  │
└─────────────────────────────────────┘
Dedicated scraper for TradingView Ideas (recent) feed

This module fetches recent user ideas for a symbol from TradingView.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
import requests
from bs4 import BeautifulSoup
import time

from .feed_scraper import FeedScraper
import items_management
from debugger import debug_info, debug_error, debug_success, debug_warning
from config import SCRAPER_TIMEOUT, SCRAPER_MAX_RETRIES, SCRAPER_RETRY_DELAY

class TradingViewIdeasRecentScraper(FeedScraper):
    """
    ┌─────────────────────────────────────┐
    │   TRADINGVIEW IDEAS RECENT SCRAPER  │
    └─────────────────────────────────────┘
    Scraper for TradingView recent ideas feed.
    """
    def __init__(self):
        super().__init__("TD IDEAS RECENT")
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Referer': 'https://www.tradingview.com/',
        }
        debug_info("TradingView Ideas Recent scraper initialized")

    def fetch(self, symbol: str, exchange: str, maxItems: int, sinceLast: Optional[str] = None) -> List[Dict[str, Any]]:
        try:
            debug_info(f"Starting TradingView Ideas Recent fetch for {exchange}:{symbol} (max: {maxItems})")
            
            # Build URL - for recent ideas, we need a different URL pattern
            if symbol:
                symbol_payload = f"/{symbol}/"
            else:
                raise ValueError("Symbol required for recent ideas")
            
            # Page 1 has a different URL structure than subsequent pages
            url = f"https://www.tradingview.com/symbols{symbol_payload}ideas/?component-data-only=1&sort=recent"
            debug_info(f"Fetching recent ideas from: {url}")
            
            response = requests.get(url, headers=self.headers, timeout=SCRAPER_TIMEOUT)
            response.raise_for_status()
            
            # Parse the JSON response
            data = response.json()
            items = data.get("data", {}).get("ideas", {}).get("data", {}).get("items", [])
            
            if not items:
                debug_warning(f"No recent ideas found for {exchange}:{symbol}")
                return []
            
            # Filter items that have symbol data and limit to maxItems
            valid_items = []
            for item in items:
                # According to the reference code, we need to check if the item has a symbol
                if item.get("symbol") is not None:
                    valid_items.append(item)
                if maxItems and len(valid_items) >= maxItems:
                    break
            
            debug_info(f"Retrieved {len(valid_items)} recent ideas")
            
            processed_items = []
            successful_inserts = 0
            
            for idea in valid_items:
                try:
                    # Extract the fields correctly based on the actual data structure
                    title = idea.get('name', '')  # 'name' not 'title'
                    if not title:
                        continue
                    
                    if len(title) > 200:
                        title = title[:197] + "..."
                    
                    content = idea.get('description', '')  # 'description' not 'paragraph'
                    if not content:
                        debug_warning(f"Skipping idea with no content: {title}")
                        continue
                    
                    # Extract comments and boost information
                    comments_count = idea.get('comments_count', 0)
                    likes_count = idea.get('likes_count', 0)
                    
                    # Create comments_content string
                    comments_content = f"COMMENTS: {comments_count}"
                    # Note: Individual comment messages are not accessible via public API
                    # Only the count is available
                    
                    # Create likes_content string  
                    likes_content = ""
                    if likes_count > 0:
                        likes_content = f"{likes_count} PEOPLE FOUND THIS USEFUL"
                    
                    # Append comments and likes info to content
                    if comments_content or likes_content:
                        content += "\n\n"
                        if likes_content:
                            content += likes_content + "\n"
                        if comments_content:
                            content += comments_content
                    
                    # Handle timestamp - the API returns date_timestamp as Unix timestamp
                    date_timestamp = idea.get('date_timestamp')
                    if date_timestamp:
                        # Unix timestamps from TradingView are in UTC
                        utc_dt = datetime.fromtimestamp(date_timestamp, tz=timezone.utc)
                        # Convert to local time for storage
                        local_dt = utc_dt.astimezone()
                        timePosted = local_dt.isoformat()
                    else:
                        # Fallback to created_at string if available
                        created_at = idea.get('created_at')
                        if created_at:
                            try:
                                # Parse and convert to local time
                                dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                                local_dt = dt.astimezone()
                                timePosted = local_dt.isoformat()
                            except:
                                timePosted = created_at
                        else:
                            debug_warning(f"Skipping idea with no timestamp: {title}")
                            continue
                    
                    # Get image URL from the image field
                    image_data = idea.get('image', {})
                    if image_data and isinstance(image_data, dict):
                        # Use the middle size image and remove "_mid" if present
                        imageURL = image_data.get('middle', '')
                        if imageURL and "_mid" in imageURL:
                            imageURL = imageURL.replace("_mid", "")
                    else:
                        imageURL = ''
                    
                    insight_data = {
                        "title": title,
                        "content": content,
                        "timePosted": timePosted,
                        "symbol": symbol.upper(),
                        "exchange": exchange.upper(),
                        "imageURL": imageURL
                    }
                    
                    if not content or len(content.strip()) < 20:
                        debug_warning(f"Skipping idea due to insufficient data: {title}")
                        continue
                    
                    insight_id, is_new = items_management.add_insight(
                        type=self.type,
                        title=insight_data["title"],
                        content=insight_data["content"],
                        timePosted=insight_data["timePosted"],
                        symbol=insight_data["symbol"],
                        exchange=insight_data["exchange"],
                        imageURL=insight_data.get("imageURL")
                    )
                    
                    processed_item = {
                        **insight_data,
                        "insight_id": insight_id,
                        "status": "created" if is_new else "duplicate"
                    }
                    processed_items.append(processed_item)
                    if is_new:
                        successful_inserts += 1
                    
                except Exception as e:
                    debug_error(f"Failed to process idea: {str(e)}")
                    processed_items.append({
                        "title": idea.get("name", "Unknown"),
                        "status": "failed",
                        "error": str(e)
                    })
                    continue
            
            self.update_fetch_time()
            debug_success(f"TradingView Ideas Recent fetch completed: {successful_inserts}/{len(valid_items)} items processed successfully")
            return processed_items
            
        except Exception as e:
            debug_error(f"TradingView Ideas Recent fetch failed: {str(e)}")
            return []
