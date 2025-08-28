"""
┌─────────────────────────────────────┐
│  TRADINGVIEW IDEAS RECENT SCRAPER   │
└─────────────────────────────────────┘
Dedicated scraper for TradingView Ideas (recent) feed

This module fetches recent user ideas for a symbol from TradingView using JSON API.
"""

from typing import List, Optional
from datetime import datetime, timezone
from bs4 import BeautifulSoup

from .base import BaseScraper
from core import ScrapedItem, FeedType
from debugger import debug_info, debug_error, debug_success, debug_warning


class TradingViewIdeasRecentScraper(BaseScraper):
    """
    ┌─────────────────────────────────────┐
    │  TRADINGVIEW IDEAS RECENT SCRAPER   │
    └─────────────────────────────────────┘
    Scraper for TradingView recent ideas feed using JSON API.
    
    Parameters:
    - symbol: Trading symbol (e.g., BTCUSD)
    - exchange: Exchange name (e.g., BINANCE)
    - limit: Maximum items to fetch
    
    Returns:
    - List of ScrapedItem instances
    
    Notes:
    - Uses JSON API endpoint for recent ideas
    - Fetches ideas sorted by most recent first
    """
    
    def __init__(self):
        super().__init__(FeedType.TD_IDEAS_RECENT)
    
    def fetch_items(self, symbol: str, exchange: str, limit: int) -> List[ScrapedItem]:
        """Fetch recent ideas from TradingView using JSON API"""
        if not symbol:
            raise ValueError("Symbol required for fetching ideas")
        
        # Build URL for recent ideas - uses JSON endpoint
        url = f"https://www.tradingview.com/symbols/{symbol}/ideas/?component-data-only=1&sort=recent"
        
        # Fetch JSON response
        response = self.make_request(url)
        
        # Parse JSON response
        try:
            data = response.json()
        except Exception as e:
            debug_error(f"Failed to parse JSON response: {str(e)}")
            return []
        
        # Handle different response structures
        if isinstance(data, str):
            debug_error(f"Unexpected string response: {data}")
            return []
        
        # The JSON structure is data.ideas.data.items
        ideas_data = data.get('data', {}).get('ideas', {})
        items = ideas_data.get('data', {}).get('items', []) if isinstance(ideas_data, dict) else []
        if not items:
            debug_warning(f"No recent ideas found for {exchange}:{symbol}")
            return []
        
        debug_info(f"Found {len(items)} recent ideas")
        
        # Sort by date and limit
        items = sorted(items, key=lambda x: x.get('published', 0), reverse=True)
        items = items[:limit] if limit else items
        
        # Process each idea item
        scraped_items = []
        for idx, item in enumerate(items):
            try:
                scraped_item = self._process_idea_item(item, symbol, exchange)
                if scraped_item:
                    scraped_items.append(scraped_item)
            except Exception as e:
                debug_error(f"Error processing recent idea {idx}: {str(e)}")
                continue
        
        return scraped_items
    
    def _process_idea_item(self, item: dict, symbol: str, exchange: str) -> Optional[ScrapedItem]:
        """Process individual recent idea item"""
        # Ensure item is a dict
        if not isinstance(item, dict):
            debug_error(f"Recent idea item is not a dict: {type(item)}")
            return None
        
        # Extract basic fields - the API uses 'name' for title
        title = item.get('name', '')
        if not title:
            return None
        
        # Limit title length
        if len(title) > 200:
            title = title[:197] + "..."
        
        # Get content - the API uses 'description'
        content = item.get('description', '')
        if not content:
            content = title
        
        if len(content.strip()) < 10:
            debug_warning(f"Skipping recent idea with insufficient content: {title}")
            return None
        
        # Extract metadata for content enhancement
        user_info = item.get('user', {})
        author = user_info.get('username', '') if isinstance(user_info, dict) else str(user_info)
        
        metadata = {
            'author': author,
            'published': item.get('published', ''),
            'likes': item.get('likes_count', 0),
            'comments': item.get('comments_count', 0),
            'strategy': item.get('strategy', '')  # Add strategy if available
        }
        
        # Enhance content with engagement metrics
        engagement_summary = self._create_engagement_summary(metadata)
        if engagement_summary:
            content = f"{content}\n\n{engagement_summary}"
        
        # Parse timestamp - the API uses 'created_at' and 'date_timestamp'
        timestamp = self._parse_timestamp(item)
        if not timestamp:
            debug_warning(f"Skipping recent idea with no timestamp: {title}")
            return None
        
        # Extract other fields - handle image dict
        image_info = item.get('image', {})
        if isinstance(image_info, dict):
            image_url = image_info.get('middle', image_info.get('big', ''))
        else:
            image_url = str(image_info) if image_info else ''
        
        source_url = item.get('chart_url', item.get('link', item.get('url', '')))
        
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
        """Parse timestamp from recent idea item"""
        # Try multiple timestamp fields - the API uses 'created_at' and 'date_timestamp'
        timestamp_fields = ['created_at', 'date_timestamp', 'published', 'timestamp', 'created', 'date']
        
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
                        # Handle ISO format with Z or timezone
                        if 'T' in value and (value.endswith('Z') or '+' in value):
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
        
        # Add likes/boosts count if available
        if metadata.get('likes', 0) > 0:
            likes_text = f"{metadata['likes']} like{'s' if metadata['likes'] != 1 else ''}"
            summary_parts.append(likes_text)
        
        # Add strategy if available
        if metadata.get('strategy'):
            strategy_text = f"Strategy: {metadata['strategy']}"
            summary_parts.append(strategy_text)
        
        # Add author if available
        if metadata.get('author'):
            author_text = f"By: {metadata['author']}"
            summary_parts.append(author_text)
        
        if summary_parts:
            return " | ".join(summary_parts)
        
        return ""
