"""
/**
 * 
 *  ┌─────────────────────────────────────┐
 *  │     TRADINGVIEW NEWS SCRAPER        │
 *  └─────────────────────────────────────┘
 *  Scraper for TradingView news feed
 * 
 *  Fetches real-time news from TradingView's news API
 *  and parses article content when available.
 * 
 *  Parameters:
 *  - None
 * 
 *  Returns:
 *  - TradingViewNewsScraper instance
 * 
 *  Notes:
 *  - Extends BaseScraper for common functionality
 *  - Returns standardized ScrapedItem objects
 */
"""

from typing import List, Optional
from datetime import datetime, timezone
from bs4 import BeautifulSoup

from .base import BaseScraper
from core import ScrapedItem, FeedType
from config import SCRAPER_MIN_CONTENT_LENGTH
from debugger import debug_info, debug_error, debug_warning


class TradingViewNewsScraper(BaseScraper):
    """
     ┌─────────────────────────────────────┐
     │   TRADINGVIEWNEWSSCRAPER            │
     └─────────────────────────────────────┘
     Scraper implementation for TradingView news
     
     Fetches news headlines and full articles from
     TradingView's news API.
    """
    
    def __init__(self):
        super().__init__(FeedType.TD_NEWS)
    
    def fetch_items(self, symbol: str, exchange: str, limit: int) -> List[ScrapedItem]:
        """
         ┌─────────────────────────────────────┐
         │         FETCH_ITEMS                 │
         └─────────────────────────────────────┘
         Fetch news items from TradingView
         
         Implements the abstract method to fetch news data.
         
         Parameters:
         - symbol: Trading symbol
         - exchange: Exchange name
         - limit: Maximum items to fetch
         
         Returns:
         - List of ScrapedItem instances
        """
        # Store for later use
        self._current_symbol = symbol
        self._current_exchange = exchange
        
        # Build API URL - parameters need to be in the URL, not as params
        url = f"https://news-headlines.tradingview.com/v2/view/headlines/symbol?client=web&lang=en&area=&provider=&section=&streaming=&symbol={exchange}:{symbol}"
        params = {}
        
        # Fetch headlines
        response = self.make_request(url, params=params)
        
        # Debug response to see what we're getting
        debug_info(f"News API response status: {response.status_code}")
        
        try:
            data = response.json()
        except Exception as e:
            debug_error(f"Failed to parse JSON: {e}")
            debug_info(f"Response text: {response.text[:500]}...")
            return []
        
        # Handle different response structures
        if isinstance(data, str):
            debug_error(f"Unexpected string response: {data}")
            return []
        
        items = data.get('items', []) if isinstance(data, dict) else []
        if not items:
            debug_warning(f"No news headlines found for {exchange}:{symbol}")
            return []
        
        debug_info(f"Found {len(items)} news items")
        
        # Sort by date and limit
        items = sorted(items, key=lambda x: x.get('published', 0), reverse=True)
        items = items[:limit] if limit else items
        
        # Process each news item
        scraped_items = []
        filtered_count = 0
        error_count = 0
        
        for idx, item in enumerate(items):
            try:
                scraped_item = self._process_news_item(item)
                if scraped_item:
                    scraped_items.append(scraped_item)
                else:
                    filtered_count += 1
            except Exception as e:
                debug_error(f"Error processing news item {idx}: {str(e)}")
                debug_info(f"Item type: {type(item)}, Item: {str(item)[:200]}")
                error_count += 1
                continue
        
        # Log filtering statistics
        if filtered_count > 0:
            debug_warning(f"Filtered out {filtered_count} news items due to insufficient content/invalid data")
        if error_count > 0:
            debug_warning(f"Failed to process {error_count} news items due to errors")
        
        debug_info(f"News processing: {len(scraped_items)} valid items from {len(items)} raw items")
        return scraped_items
    
    def _process_news_item(self, item: dict) -> Optional[ScrapedItem]:
        """
         ┌─────────────────────────────────────┐
         │      _PROCESS_NEWS_ITEM             │
         └─────────────────────────────────────┘
         Process individual news item
         
         Converts raw API data to ScrapedItem format,
         fetching full article content when available.
         
         Parameters:
         - item: Raw news item from API
         
         Returns:
         - ScrapedItem or None if invalid
        """
        # Ensure item is a dict
        if not isinstance(item, dict):
            debug_error(f"News item is not a dict: {type(item)}")
            return None
        
        # Extract basic fields
        title = item.get('title', '')
        if not title:
            title = "Untitled News Item"  # Provide fallback instead of filtering
        
        # Limit title length
        if len(title) > 200:
            title = title[:197] + "..."
        
        # Get timestamp - use current time if not available
        timestamp = self._parse_timestamp(item)
        if not timestamp:
            timestamp = datetime.now()
        
        # Get content - try to fetch full article first
        content = self._fetch_article_content(item)
        
        # If no full article, use description
        if not content:
            content = item.get('description', '')
        
        # If no description, use summary
        if not content:
            content = item.get('summary', '')
        
        # If still no content, use title as fallback
        if not content:
            content = title
        
        # Extract other fields
        image_url = item.get('image', item.get('thumbnail', ''))
        
        # Use link field if available, otherwise construct from storyPath
        source_url = item.get('link')
        if not source_url and item.get('storyPath'):
            source_url = f"https://tradingview.com{item['storyPath']}"
        
        # Use the symbol/exchange we're searching for
        symbol = self._current_symbol
        exchange = self._current_exchange
        
        return ScrapedItem(
            title=title,
            content=content,
            timestamp=timestamp,
            symbol=symbol,
            exchange=exchange,
            source_url=source_url,
            image_url=image_url,
            metadata={
                'provider': item.get('provider', ''),
                'source': item.get('source', ''),
                'story_id': item.get('id', ''),
                'urgency': item.get('urgency', 0)
            }
        )
    
    def _parse_timestamp(self, item: dict) -> Optional[datetime]:
        """Parse timestamp from news item"""
        if 'published' in item:
            try:
                # Unix timestamp in UTC
                dt = datetime.fromtimestamp(item['published'], tz=timezone.utc)
                return dt.astimezone()  # Convert to local time
            except:
                pass
        
        return None
    
    def _fetch_article_content(self, item: dict) -> Optional[str]:
        """
         ┌─────────────────────────────────────┐
         │     _FETCH_ARTICLE_CONTENT          │
         └─────────────────────────────────────┘
         Fetch full article content
         
         Attempts to fetch and parse the full article
         content from TradingView using the proven
         selectors from the working implementation.
         
         Parameters:
         - item: News item with storyPath or link
         
         Returns:
         - Article content or None
        """
        # Try different URL sources
        url = None
        if item.get('storyPath'):
            url = f"https://tradingview.com{item['storyPath']}"
        elif item.get('link'):
            url = item['link']
        
        if not url:
            return None
        
        try:
            debug_info(f"Fetching full article from: {url}")
            response = self.make_request(url)
            
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Use the proven selectors from the working implementation
            article_tag = soup.find('article')
            if not article_tag:
                debug_warning(f"No article tag found for URL: {url}")
                return None
            
            # Extract content using the working implementation's approach
            full_content = {
                "title": None,
                "published_datetime": None,
                "body": [],
                "tags": []
            }
            
            # Title
            title = article_tag.find('h1', class_='title-KX2tCBZq')
            if title:
                full_content['title'] = title.get_text(strip=True)
            
            # Published date
            published_time = article_tag.find('time')
            if published_time:
                full_content['published_datetime'] = published_time.get('datetime')
            
            # Body - this is the key part for content extraction
            body_content = article_tag.find('div', class_='body-KX2tCBZq')
            if body_content:
                for element in body_content.find_all(['p', 'img'], recursive=True):
                    if element.name == 'p':
                        text = element.get_text(strip=True)
                        if text:
                            full_content['body'].append({
                                "type": "text",
                                "content": text
                            })
                    elif element.name == 'img':
                        full_content['body'].append({
                            "type": "image",
                            "src": element.get('src', ''),
                            "alt": element.get('alt', '')
                        })
            
            # Tags
            row_tags = soup.find('div', class_=lambda x: x and x.startswith('rowTags-'))
            if row_tags:
                for span in row_tags.find_all('span'):
                    tag_text = span.get_text(strip=True)
                    if tag_text:
                        full_content['tags'].append(tag_text)
            
            # Extract text content from body
            if full_content.get('body'):
                text_parts = [item['content'] for item in full_content['body'] if item.get('type') == 'text' and item.get('content')]
                if text_parts:
                    content = ' '.join(text_parts)
                    debug_info(f"Successfully fetched article content ({len(content)} chars)")
                    return content
            
            # Fallback: try alternative selectors if the main ones don't work
            content_selectors = [
                'article div.body-KX2tCBZq',  # TradingView article body
                'article div[class*="body"]',  # Generic body div in article
                'article .content',           # Generic content class
                'article',                    # Fallback to whole article
                '.article-content',           # Common article content class
                '.story-body',                # Story body class
                'div[class*="content"]',      # Any div with content in class name
            ]
            
            content_element = None
            for selector in content_selectors:
                content_element = soup.select_one(selector)
                if content_element:
                    debug_info(f"Found content using fallback selector: {selector}")
                    break
            
            if content_element:
                # Extract text from paragraphs, spans, and divs
                paragraphs = []
                
                # Try paragraphs first
                for p in content_element.find_all(['p', 'div', 'span']):
                    text = p.get_text(strip=True)
                    if text and len(text) > 20:  # Filter out very short texts
                        paragraphs.append(text)
                
                # If no paragraphs found, get all text
                if not paragraphs:
                    text = content_element.get_text(strip=True)
                    if text and len(text) > 50:
                        paragraphs = [text]
                
                if paragraphs:
                    content = ' '.join(paragraphs)
                    debug_info(f"Successfully fetched article content using fallback ({len(content)} chars)")
                    return content
            
            debug_warning(f"No content element found for URL: {url}")
            return None
            
        except Exception as e:
            debug_error(f"Failed to fetch article content from {url}: {e}")
            return None
