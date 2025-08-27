"""
┌─────────────────────────────────────┐
│       TRADINGVIEW NEWS SCRAPER      │
└─────────────────────────────────────┘
Dedicated scraper for TradingView News feed

This module handles scraping and processing of TradingView News feed,
providing real news data from TradingView's news API.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import requests
from bs4 import BeautifulSoup

from .feed_scraper import FeedScraper
import items_management
from debugger import debug_info, debug_error, debug_success, debug_warning


class TradingViewNewsScraper(FeedScraper):
    """
    
     ┌─────────────────────────────────────┐
     │     TRADINGVIEW NEWS SCRAPER        │
     └─────────────────────────────────────┘
     Scraper for TradingView News feed
     
     This class handles scraping of TradingView News feed by accessing
     TradingView's news headlines API and extracting real news data.
     
     Parameters:
     - None (inherits from FeedScraper)
     
     Returns:
     - TradingViewNewsScraper instance ready for scraping operations
     
     Notes:
     - Inherits shared functionality from FeedScraper
     - Implements direct TradingView news API access
     - Fetches real news headlines and content
    """

    def __init__(self):
        super().__init__("TD NEWS")
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Referer': 'https://www.tradingview.com/',
        }
        debug_info("TradingView News scraper initialized")

    def fetch(self, symbol: str, exchange: str, maxItems: int, sinceLast: Optional[str] = None) -> List[Dict[str, Any]]:
        """
         ┌─────────────────────────────────────┐
         │             FETCH                   │
         └─────────────────────────────────────┘
         Fetch TradingView news data and create insights
         
         Retrieves real news data from TradingView for the specified symbol/exchange,
         processes each item, and creates database insights using items_management.
         
         Parameters:
         - symbol: Trading symbol (e.g., "BTCUSD", "AAPL")
         - exchange: Exchange name (e.g., "BINANCE", "NASDAQ")
         - maxItems: Maximum number of items to retrieve
         - sinceLast: Optional timestamp to fetch only items since this time (not used currently)
         
         Returns:
         - List of processed news items with insight IDs
         
         Notes:
         - Creates database insights for each news item
         - Updates timeFetched after successful completion
         - Returns empty list on failure with error logging
        """
        try:
            debug_info(f"Starting TradingView News fetch for {exchange}:{symbol} (max: {maxItems})")
            
            # Fetch news headlines from TradingView API
            headlines = self._scrape_headlines(symbol, exchange, maxItems)
            
            if not headlines:
                debug_warning(f"No news headlines retrieved for {exchange}:{symbol}")
                return []
            
            processed_items = []
            successful_inserts = 0
            
            # Process each headline and create insights
            for headline in headlines:
                try:
                    # Extract news content if story path is available
                    full_content = None
                    if headline.get('storyPath'):
                        try:
                            full_content = self._scrape_news_content(headline['storyPath'])
                        except Exception as e:
                            debug_error(f"Failed to fetch full content: {e}")
                    
                    # Prepare insight data
                    insight_data = self._prepare_insight_data(headline, full_content, symbol, exchange)
                    
                    if not insight_data:
                        debug_warning(f"Skipping news item due to insufficient data: {headline.get('title', 'Unknown')}")
                        continue
                    
                    # Create insight in database
                    insight_id = items_management.add_insight(
                        type=self.type,
                        title=insight_data["title"],
                        content=insight_data["content"],
                        timePosted=insight_data["timePosted"],
                        symbol=insight_data["symbol"],
                        exchange=insight_data["exchange"],
                        imageURL=insight_data.get("imageURL")
                    )
                    
                    # Add to processed items
                    processed_item = {
                        **insight_data,
                        "insight_id": insight_id,
                        "status": "created"
                    }
                    processed_items.append(processed_item)
                    successful_inserts += 1
                    
                except Exception as e:
                    debug_error(f"Failed to process news item: {str(e)}")
                    processed_items.append({
                        "title": headline.get("title", "Unknown"),
                        "status": "failed",
                        "error": str(e)
                    })
                    continue
            
            # Update fetch timestamp on successful completion
            self.update_fetch_time()
            
            debug_success(f"TradingView News fetch completed: {successful_inserts}/{len(headlines)} items processed successfully")
            
            return processed_items
            
        except Exception as e:
            debug_error(f"TradingView News fetch failed: {str(e)}")
            return []

    def _scrape_headlines(self, symbol: str, exchange: str, max_items: int) -> List[Dict[str, Any]]:
        """
         ┌─────────────────────────────────────┐
         │        SCRAPE HEADLINES             │
         └─────────────────────────────────────┘
         Scrape news headlines from TradingView API
         
         Parameters:
         - symbol: Trading symbol
         - exchange: Exchange name
         - max_items: Maximum number of headlines to fetch
         
         Returns:
         - List of headline dictionaries
        """
        try:
            # Construct the TradingView news API URL
            url = f"https://news-headlines.tradingview.com/v2/view/headlines/symbol?client=web&lang=en&area=&provider=&section=&streaming=&symbol={exchange}:{symbol}"
            
            debug_info(f"Fetching headlines from: {url}")
            
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            response_json = response.json()
            items = response_json.get('items', [])
            
            if not items:
                debug_info("No news items found in API response")
                return []
            
            # Sort by latest published date
            items = sorted(items, key=lambda x: x.get('published', 0), reverse=True)
            
            # Limit to requested number of items
            if max_items and len(items) > max_items:
                items = items[:max_items]
            
            debug_info(f"Retrieved {len(items)} news headlines")
            return items
            
        except requests.exceptions.HTTPError as http_err:
            if response.status_code == 400:
                debug_error(f"Bad request: The server could not understand the request. {http_err}")
            else:
                debug_error(f"HTTP error occurred: {http_err}")
            return []
        except Exception as err:
            debug_error(f"Error scraping headlines: {err}")
            return []

    def _scrape_news_content(self, story_path: str) -> Dict[str, Any]:
        """
         ┌─────────────────────────────────────┐
         │      SCRAPE NEWS CONTENT            │
         └─────────────────────────────────────┘
         Scrape full article content from TradingView
         
         Parameters:
         - story_path: Path to the news article
         
         Returns:
         - Dictionary containing article content
        """
        try:
            # Construct the full URL
            url = f"https://tradingview.com{story_path}"
            
            debug_info(f"Fetching article content from: {url}")
            
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            # Parse the HTML
            soup = BeautifulSoup(response.text, "html.parser")
            
            article_tag = soup.find('article')
            if not article_tag:
                debug_warning("No article tag found in response")
                return {}
            
            article_json = {
                "title": None,
                "published_datetime": None,
                "body": [],
                "tags": []
            }
            
            # Extract title
            title = article_tag.find('h1', class_='title-KX2tCBZq')
            if title:
                article_json['title'] = title.get_text(strip=True)
            
            # Extract published date
            published_time = article_tag.find('time')
            if published_time:
                article_json['published_datetime'] = published_time.get('datetime')
            
            # Extract body content
            body_content = article_tag.find('div', class_='body-KX2tCBZq')
            if body_content:
                for element in body_content.find_all(['p', 'img'], recursive=True):
                    if element.name == 'p':
                        text = element.get_text(strip=True)
                        if text:
                            article_json['body'].append({
                                "type": "text",
                                "content": text
                            })
                    elif element.name == 'img':
                        article_json['body'].append({
                            "type": "image",
                            "src": element.get('src', ''),
                            "alt": element.get('alt', '')
                        })
            
            # Extract tags
            row_tags = soup.find('div', class_=lambda x: x and x.startswith('rowTags-'))
            if row_tags:
                for span in row_tags.find_all('span'):
                    tag_text = span.get_text(strip=True)
                    if tag_text:
                        article_json['tags'].append(tag_text)
            
            return article_json
            
        except Exception as e:
            debug_error(f"Failed to scrape article content: {e}")
            return {}

    def _prepare_insight_data(self, headline: Dict[str, Any], full_content: Optional[Dict[str, Any]], symbol: str, exchange: str) -> Optional[Dict[str, Any]]:
        """
         ┌─────────────────────────────────────┐
         │      PREPARE INSIGHT DATA           │
         └─────────────────────────────────────┘
         Prepare data for insight creation
         
         Parameters:
         - headline: News headline data from API
         - full_content: Full article content if available
         - symbol: Trading symbol
         - exchange: Exchange name
         
         Returns:
         - Dictionary ready for insight creation or None if insufficient data
        """
        # Extract title
        title = headline.get('title', '')
        if not title:
            return None
        
        # Truncate long titles
        if len(title) > 200:
            title = title[:197] + "..."
        
        # Extract content
        content = ""
        
        # First, try to get content from full article
        if full_content and full_content.get('body'):
            text_parts = []
            for item in full_content['body']:
                if item.get('type') == 'text' and item.get('content'):
                    text_parts.append(item['content'])
            content = ' '.join(text_parts)
        
        # Fallback to headline description
        if not content:
            content = headline.get('description', '')
        
        # If still no content, use provider and title
        if not content:
            provider = headline.get('provider', 'TradingView')
            content = f"News from {provider}: {title}"
        
        # Extract timestamp
        timePosted = None
        
        # Try published timestamp (Unix timestamp)
        if 'published' in headline:
            try:
                dt = datetime.fromtimestamp(headline['published'])
                timePosted = dt.isoformat()
            except:
                pass
        
        # Fallback to full content published datetime
        if not timePosted and full_content and full_content.get('published_datetime'):
            timePosted = full_content['published_datetime']
        
        # Default to current time
        if not timePosted:
            timePosted = datetime.now().isoformat()
        
        # Extract image URL
        imageURL = headline.get('image', headline.get('thumbnail', ''))
        
        return {
            "title": title,
            "content": content,
            "timePosted": timePosted,
            "symbol": symbol.upper(),
            "exchange": exchange.upper(),
            "imageURL": imageURL
        }