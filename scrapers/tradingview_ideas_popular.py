"""
┌─────────────────────────────────────┐
│  TRADINGVIEW IDEAS POPULAR SCRAPER  │
└─────────────────────────────────────┘
Dedicated scraper for TradingView Ideas (popular) feed

This module fetches popular user ideas for a symbol from TradingView using HTML parsing.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from bs4 import BeautifulSoup

from .base import BaseScraper
from core import ScrapedItem, FeedType
from debugger import debug_info, debug_error, debug_success, debug_warning


class TradingViewIdeasPopularScraper(BaseScraper):
    """
    ┌─────────────────────────────────────┐
    │  TRADINGVIEW IDEAS POPULAR SCRAPER  │
    └─────────────────────────────────────┘
    Scraper for TradingView popular ideas feed using HTML parsing.
    
    Parameters:
    - symbol: Trading symbol (e.g., BTCUSD)
    - exchange: Exchange name (e.g., BINANCE)
    - limit: Maximum items to fetch
    
    Returns:
    - List of ScrapedItem instances
    
    Notes:
    - Uses HTML parsing for popular ideas
    - Fetches ideas sorted by popularity
    - Based on original working implementation
    """
    
    def __init__(self):
        super().__init__(FeedType.TD_IDEAS_POPULAR)
        # Set headers for HTML requests
        self.session.headers.update({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Referer': 'https://www.tradingview.com/',
        })
    
    def fetch_items(self, symbol: str, exchange: str, limit: int) -> List[ScrapedItem]:
        """Fetch popular ideas from TradingView using HTML parsing"""
        if not symbol:
            raise ValueError("Symbol required for fetching ideas")
        
        # Build URL for popular ideas - uses HTML endpoint
        url = f"https://www.tradingview.com/symbols/{symbol}/ideas/"
        
        # Fetch HTML page
        response = self.make_request(url)
        
        # Parse HTML response
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Debug logging
        debug_info(f"Response length: {len(response.text)} chars")
        
        # Find articles directly - the structure has changed
        articles = soup.find_all("article")
        
        if not articles:
            debug_warning(f"No popular ideas found for {symbol}")
            return []
        
        debug_info(f"Found {len(articles)} articles")
        
        # Process articles and limit
        scraped_items = []
        for idx, article in enumerate(articles):
            if limit and len(scraped_items) >= limit:
                break
            
            try:
                scraped_item = self._parse_article_to_item(article, symbol, exchange)
                if scraped_item:
                    scraped_items.append(scraped_item)
            except Exception as e:
                debug_error(f"Error processing popular idea {idx}: {str(e)}")
                continue
        
        return scraped_items
    
    def _parse_article_to_item(self, article, symbol: str, exchange: str) -> Optional[ScrapedItem]:
        """Parse HTML article tag to ScrapedItem"""
        try:
            # Extract title
            title_tag = article.find('a', class_=lambda x: x and x.startswith('title-'))
            if not title_tag:
                return None
            
            title = title_tag.text.strip()
            if not title:
                return None
            
            # Limit title length
            if len(title) > 200:
                title = title[:197] + "..."
            
            # Extract content/paragraph
            para_tag = article.find('a', class_=lambda x: x and x.startswith('paragraph-'))
            content = para_tag.text.strip() if para_tag else title
            
            if len(content.strip()) < 10:
                debug_warning(f"Skipping popular idea with insufficient content: {title}")
                return None
            
            # Extract timestamp
            timestamp = self._parse_article_timestamp(article)
            if not timestamp:
                debug_warning(f"Skipping popular idea with no timestamp: {title}")
                return None
            
            # Extract image URL
            image_url = ""
            picture_tag = article.find('picture')
            if picture_tag:
                img_tag = picture_tag.find('img')
                if img_tag and img_tag.get('src'):
                    image_url = img_tag['src']
                    # Remove "_mid" from URL if present
                    if "_mid" in image_url:
                        image_url = image_url.replace("_mid", "")
            
            # Extract source URL
            source_url = title_tag.get('href') if title_tag else None
            if source_url and not source_url.startswith('http'):
                source_url = f"https://www.tradingview.com{source_url}"
            
            # Extract metadata
            metadata = self._extract_article_metadata(article)
            
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
            
        except Exception as e:
            debug_error(f"Failed to parse article: {str(e)}")
            return None
    
    def _parse_article_timestamp(self, article) -> Optional[datetime]:
        """Parse timestamp from article HTML"""
        # Look for time tag with publication date
        time_tag = article.find('time', class_=lambda x: x and x.startswith('publication-date-'))
        if time_tag and time_tag.get('datetime'):
            try:
                datetime_str = time_tag['datetime']
                if 'T' in datetime_str and (datetime_str.endswith('Z') or '+' in datetime_str):
                    dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
                else:
                    dt = datetime.fromisoformat(datetime_str).replace(tzinfo=timezone.utc)
                return dt.astimezone()
            except Exception as e:
                debug_warning(f"Failed to parse timestamp {time_tag['datetime']}: {str(e)}")
        
        return None
    
    def _extract_article_metadata(self, article) -> Dict[str, Any]:
        """Extract metadata from article HTML"""
        metadata = {}
        
        # Extract author
        author_tag = article.find('span', class_=lambda x: x and x.startswith('card-author-'))
        if author_tag:
            metadata['author'] = author_tag.text.replace("by", "").strip()
        
        # Extract comments count
        comments_count = 0
        comments_tag = article.find('span', class_=lambda x: x and x.startswith('ellipsisContainer'))
        if comments_tag:
            try:
                comments_count = int(comments_tag.text.strip())
            except (ValueError, TypeError):
                comments_count = 0
        metadata['comments'] = comments_count
        
        # Extract boosts/likes count
        boosts_count = 0
        boosts_tag = article.find('button', class_=lambda x: x and x.startswith('boostButton-'))
        if boosts_tag:
            button_text = boosts_tag.get_text().strip()
            if button_text and button_text.isdigit():
                boosts_count = int(button_text)
        metadata['likes'] = boosts_count
        
        # Extract idea strategy
        strategy_tag = article.find('span', class_=lambda x: x and x.startswith('idea-strategy-icon-'))
        if strategy_tag:
            metadata['strategy'] = strategy_tag.get('title', '').strip()
        
        return metadata
