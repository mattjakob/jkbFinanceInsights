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
        
        # Extract metadata for content enhancement
        author_info = item.get('author', {})
        author = author_info.get('username', '') if isinstance(author_info, dict) else ''
        likes_count = item.get('total_likes', 0)
        comments_count = item.get('total_comments', 0)
        
        metadata = {
            'author': author,
            'post_type': 'opinion',
            'likes': likes_count,
            'comments': comments_count
        }
        
        # Enhance content with engagement metrics
        engagement_summary = self._create_engagement_summary(metadata)
        if engagement_summary:
            content = f"{content}\n\n{engagement_summary}"
        
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
            metadata=metadata
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

    def _create_engagement_summary(self, metadata: dict) -> str:
        """
        ┌─────────────────────────────────────┐
        │        CREATE ENGAGEMENT SUMMARY    │
        └─────────────────────────────────────┘
        Creates a summary of engagement metrics for content enhancement.
        
        Parameters:
        - metadata: Dictionary containing engagement data
        
        Returns:
        - Formatted engagement summary string
        
        Notes:
        - Summarizes comments count and popularity (likes)
        - Only includes metrics that have meaningful values
        """
        summary_parts = []
        
        # Add comments count if available
        if metadata.get('comments', 0) > 0:
            comments_text = f"{metadata['comments']} comment{'s' if metadata['comments'] != 1 else ''}"
            summary_parts.append(comments_text)
        
        # Add likes count if available
        if metadata.get('likes', 0) > 0:
            likes_text = f"{metadata['likes']} like{'s' if metadata['likes'] != 1 else ''}"
            summary_parts.append(likes_text)
        
        # Add author if available
        if metadata.get('author'):
            author_text = f"By: {metadata['author']}"
            summary_parts.append(author_text)
        
        if summary_parts:
            return " | ".join(summary_parts)
        
        return ""


