"""
/**
 * 
 *  ┌─────────────────────────────────────┐
 *  │   TRADINGVIEW OPINIONS SCRAPER      │
 *  └─────────────────────────────────────┘
 *  Scraper for TradingView opinions feed
 * 
 *  Fetches user opinions and analysis from TradingView's
 *  community-generated content.
 * 
 *  Parameters:
 *  - None
 * 
 *  Returns:
 *  - TradingViewOpinionsScraper instance
 * 
 *  Notes:
 *  - Similar structure to ideas scraper
 *  - Focuses on opinion/analysis content
 */
"""

from typing import List, Optional
from datetime import datetime, timezone

from .base import BaseScraper
from core import ScrapedItem, FeedType
from debugger import debug_info, debug_warning


class TradingViewOpinionsScraper(BaseScraper):
    """
     ┌─────────────────────────────────────┐
     │  TRADINGVIEWOPINIONSSCRAPER         │
     └─────────────────────────────────────┘
     Scraper for TradingView opinions
     
     Fetches opinion posts and analysis from the
     TradingView community.
    """
    
    def __init__(self):
        super().__init__(FeedType.TD_OPINIONS)
    
    def fetch_items(self, symbol: str, exchange: str, limit: int) -> List[ScrapedItem]:
        """Fetch opinions from TradingView"""
        if not symbol:
            raise ValueError("Symbol required for fetching opinions")
        
        # TradingView opinions use the minds API
        url = f"https://www.tradingview.com/api/v1/minds/?symbol={symbol}"
        if limit:
            url += f"&limit={limit}"
        params = {}
        
        # Fetch data
        response = self.make_request(url, params=params)
        data = response.json()
        
        # Extract items from the minds API response
        # The API returns {"results": [...]}
        items = []
        if isinstance(data, dict) and 'results' in data:
            items = data['results']
        elif isinstance(data, list):
            items = data
        
        if not items:
            debug_warning(f"No opinions found for {symbol}")
            return []
        
        # Process items
        scraped_items = []
        for item in items[:limit]:
            scraped_item = self._process_opinion_item(item, symbol, exchange)
            if scraped_item:
                scraped_items.append(scraped_item)
        
        return scraped_items
    
    def _process_opinion_item(self, item: dict, symbol: str, exchange: str) -> Optional[ScrapedItem]:
        """Process individual opinion item"""
        # Extract content from text field (minds API structure)
        content = item.get('text', '')
        if not content:
            return None
        
        # Create title from first line or truncate content
        lines = content.split('\n')
        title = lines[0] if lines else content[:100]
        if len(title) > 100:
            title = title[:97] + "..."
        
        # Add metadata if available
        author = item.get('user', {}).get('username', '')
        if author:
            content += f"\n\nAuthor: {author}"
        
        # Add engagement info
        likes_count = item.get('likes_count', 0)
        comments = item.get('comments', [])
        comments_count = len(comments) if isinstance(comments, list) else 0
        
        if likes_count or comments_count:
            content += "\n\n"
            if likes_count > 0:
                content += f"{likes_count} PEOPLE FOUND THIS USEFUL\n"
            content += f"COMMENTS: {comments_count}"
        
        # Parse timestamp
        timestamp = self._parse_timestamp(item)
        if not timestamp:
            debug_warning(f"Skipping opinion with no timestamp: {title}")
            return None
        
        # Extract image URL if available
        image_url = ''
        image_data = item.get('image', {})
        if isinstance(image_data, dict):
            image_url = image_data.get('large', image_data.get('middle', ''))
        elif isinstance(image_data, str):
            image_url = image_data
        
        # Build source URL if available
        short_name = item.get('short_name', '')
        post_id = item.get('id', '')
        source_url = None
        if short_name:
            source_url = f"https://www.tradingview.com/chart/{short_name}/"
        elif post_id:
            source_url = f"https://www.tradingview.com/x/{post_id}/"
        
        return ScrapedItem(
            title=title,
            content=content,
            timestamp=timestamp,
            symbol=symbol.upper(),
            exchange=exchange.upper(),
            source_url=source_url,
            image_url=image_url,
            metadata={
                'author': author,
                'post_type': 'opinion',
                'likes': item.get('likes_count', 0),
                'comments': item.get('comments_count', 0)
            }
        )
    
    def _parse_timestamp(self, item: dict) -> Optional[datetime]:
        """Parse timestamp from opinion item"""
        # Try multiple timestamp fields - minds API uses 'created'
        timestamp_fields = ['created', 'date_timestamp', 'timestamp', 'published', 'created_at']
        
        for field in timestamp_fields:
            if field in item:
                value = item[field]
                
                # Unix timestamp
                if isinstance(value, (int, float)):
                    try:
                        dt = datetime.fromtimestamp(value, tz=timezone.utc)
                        return dt.astimezone()
                    except:
                        continue
                
                # ISO string
                elif isinstance(value, str):
                    try:
                        if 'T' in value:
                            dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
                        else:
                            dt = datetime.fromisoformat(value).replace(tzinfo=timezone.utc)
                        return dt.astimezone()
                    except:
                        continue
        
        return None
