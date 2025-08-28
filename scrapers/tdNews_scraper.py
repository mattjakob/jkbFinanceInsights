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
from datetime import datetime, timezone
import requests
from bs4 import BeautifulSoup
import time

from .feed_scraper import FeedScraper
import items_management
from debugger import debug_info, debug_error, debug_success, debug_warning
from config import SCRAPER_TIMEOUT, SCRAPER_MAX_RETRIES, SCRAPER_RETRY_DELAY

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
            
            # --- Scrape headlines ---
            url = f"https://news-headlines.tradingview.com/v2/view/headlines/symbol?client=web&lang=en&area=&provider=&section=&streaming=&symbol={exchange}:{symbol}"
            debug_info(f"Fetching headlines from: {url}")
            response = requests.get(url, headers=self.headers, timeout=SCRAPER_TIMEOUT)
            response.raise_for_status()
            response_json = response.json()
            items = response_json.get('items', [])
            if not items:
                debug_warning(f"No news headlines retrieved for {exchange}:{symbol}")
                return []
            # Sort and limit
            items = sorted(items, key=lambda x: x.get('published', 0), reverse=True)
            if maxItems and len(items) > maxItems:
                items = items[:maxItems]
            debug_info(f"Retrieved {len(items)} news headlines")

            processed_items = []
            successful_inserts = 0
            for headline in items:
                try:
                    # --- Scrape full content if available ---
                    full_content = None
                    if headline.get('storyPath'):
                        try:
                            url = f"https://tradingview.com{headline['storyPath']}"
                            debug_info(f"Fetching article content from: {url}")
                            article_resp = requests.get(url, headers=self.headers, timeout=SCRAPER_TIMEOUT)
                            article_resp.raise_for_status()
                            soup = BeautifulSoup(article_resp.text, "html.parser")
                            article_tag = soup.find('article')
                            full_content = {
                                "title": None,
                                "published_datetime": None,
                                "body": [],
                                "tags": []
                            }
                            if article_tag:
                                # Title
                                title = article_tag.find('h1', class_='title-KX2tCBZq')
                                if title:
                                    full_content['title'] = title.get_text(strip=True)
                                # Published date
                                published_time = article_tag.find('time')
                                if published_time:
                                    full_content['published_datetime'] = published_time.get('datetime')
                                # Body
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
                        except Exception as e:
                            debug_error(f"Failed to fetch full content: {e}")
                    # --- Prepare insight data ---
                    title = headline.get('title', '')
                    if not title:
                        continue
                    if len(title) > 200:
                        title = title[:197] + "..."
                    content = ""
                    if full_content and full_content.get('body'):
                        text_parts = [item['content'] for item in full_content['body'] if item.get('type') == 'text' and item.get('content')]
                        content = ' '.join(text_parts)
                    if not content:
                        content = headline.get('description', '')
                    if not content:
                        debug_warning(f"Skipping news item with no content: {title}")
                        continue
                    timePosted = None
                    if 'published' in headline:
                        try:
                            # Unix timestamps from TradingView are in UTC
                            dt = datetime.fromtimestamp(headline['published'], tz=timezone.utc)
                            # Convert to local time
                            local_dt = dt.astimezone()
                            timePosted = local_dt.isoformat()
                        except:
                            pass
                    if not timePosted and full_content and full_content.get('published_datetime'):
                        try:
                            # Parse and convert to local time
                            pub_dt = full_content['published_datetime']
                            if 'T' in pub_dt and (pub_dt.endswith('Z') or '+' in pub_dt):
                                dt = datetime.fromisoformat(pub_dt.replace('Z', '+00:00'))
                            else:
                                # Assume UTC if no timezone
                                dt = datetime.fromisoformat(pub_dt).replace(tzinfo=timezone.utc)
                            local_dt = dt.astimezone()
                            timePosted = local_dt.isoformat()
                        except:
                            timePosted = full_content['published_datetime']
                    if not timePosted:
                        debug_warning(f"Skipping news item with no timestamp: {title}")
                        continue
                    imageURL = headline.get('image', headline.get('thumbnail', ''))
                    insight_data = {
                        "title": title,
                        "content": content,
                        "timePosted": timePosted,
                        "symbol": symbol.upper(),
                        "exchange": exchange.upper(),
                        "imageURL": imageURL
                    }
                    if not content or len(content.strip()) < 20:
                        debug_warning(f"Skipping news item due to insufficient data: {title}")
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
                    debug_error(f"Failed to process news item: {str(e)}")
                    processed_items.append({
                        "title": headline.get("title", "Unknown"),
                        "status": "failed",
                        "error": str(e)
                    })
                    continue
            self.update_fetch_time()
            debug_success(f"TradingView News fetch completed: {successful_inserts}/{len(items)} items processed successfully")
            return processed_items
        except Exception as e:
            debug_error(f"TradingView News fetch failed: {str(e)}")
            return []   