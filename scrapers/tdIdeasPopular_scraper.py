"""
┌─────────────────────────────────────┐
│  TRADINGVIEW IDEAS POPULAR SCRAPER  │
└─────────────────────────────────────┘
Dedicated scraper for TradingView Ideas (popular) feed

This module fetches popular user ideas for a symbol from TradingView.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import requests
from bs4 import BeautifulSoup

from .feed_scraper import FeedScraper
import items_management
from debugger import debug_info, debug_error, debug_success, debug_warning

class TradingViewIdeasPopularScraper(FeedScraper):
    """
    ┌─────────────────────────────────────┐
    │  TRADINGVIEW IDEAS POPULAR SCRAPER  │
    └─────────────────────────────────────┘
    Scraper for TradingView popular ideas feed.
    """
    def __init__(self):
        super().__init__("TD IDEAS POPULAR")
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Referer': 'https://www.tradingview.com/',
        }
        debug_info("TradingView Ideas Popular scraper initialized")

    def fetch(self, symbol: str, exchange: str, maxItems: int, sinceLast: Optional[str] = None) -> List[Dict[str, Any]]:
        try:
            debug_info(f"Starting TradingView Ideas Popular fetch for {exchange}:{symbol} (max: {maxItems})")
            
            # Build URL - for popular ideas
            if not symbol:
                raise ValueError("Symbol is required for fetching ideas")
            symbol_payload = f"/{symbol}/"
            
            # The correct URL according to the reference code - note "sort=recent" not "sort=popular"
            url = f"https://www.tradingview.com/symbols{symbol_payload}ideas/page-1/?component-data-only=1&sort=recent"
            debug_info(f"Fetching popular ideas from: {url}")
            
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            # Parse HTML response
            soup = BeautifulSoup(response.text, "html.parser")
            content = soup.find("div", class_="listContainer-rqOoE_3Q")
            
            if content is None:
                debug_warning(f"No popular ideas found for {exchange}:{symbol}")
                return []
            
            articles_tag = content.find_all("article")
            if not articles_tag:
                debug_warning(f"No popular ideas found for {exchange}:{symbol}")
                return []
            
            # Parse articles and limit to maxItems
            items = []
            for tag in articles_tag:
                if maxItems and len(items) >= maxItems:
                    break
                items.append(self._parse_article(tag))
            
            debug_info(f"Retrieved {len(items)} popular ideas")
            
            processed_items = []
            successful_inserts = 0
            
            for idea in items:
                try:
                    title = idea.get('title', '')
                    if not title:
                        continue
                    
                    if len(title) > 200:
                        title = title[:197] + "..."
                    
                    content = idea.get('paragraph', '')
                    if not content:
                        debug_warning(f"Skipping idea with no content: {title}")
                        continue
                    
                    # Handle publication datetime
                    timePosted = idea.get('publication_datetime')
                    if not timePosted:
                        debug_warning(f"Skipping idea with no timestamp: {title}")
                        continue
                    
                    # Handle image URL
                    imageURL = idea.get('preview_image', '')
                    if imageURL and "_mid" in imageURL:
                        # Remove "_mid" from the URL if present
                        imageURL = imageURL.replace("_mid", "")
                    
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
                    
                    insight_id = items_management.add_insight(
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
                        "status": "created"
                    }
                    processed_items.append(processed_item)
                    successful_inserts += 1
                    
                except Exception as e:
                    debug_error(f"Failed to process idea: {str(e)}")
                    processed_items.append({
                        "title": idea.get("title", "Unknown"),
                        "status": "failed",
                        "error": str(e)
                    })
                    continue
            
            self.update_fetch_time()
            debug_success(f"TradingView Ideas Popular fetch completed: {successful_inserts}/{len(items)} items processed successfully")
            return processed_items
            
        except Exception as e:
            debug_error(f"TradingView Ideas Popular fetch failed: {str(e)}")
            return []

    def _parse_article(self, article_tag) -> Dict[str, Any]:
        article_json = {
            "title": None,
            "paragraph": None,
            "preview_image": None,
            "author": None,
            "comments_count": None,
            "boosts_count": None,
            "publication_datetime": None,
            "is_updated": False,
            "idea_strategy": None,
        }
        # Title
        title_tag = article_tag.find('a', class_=lambda x: x and x.startswith('title-'))
        if title_tag:
            article_json["title"] = title_tag.text
        # Paragraph
        para_tag = article_tag.find('a', class_=lambda x: x and x.startswith('paragraph-'))
        if para_tag:
            article_json["paragraph"] = para_tag.text
        # Preview image
        picture_tag = article_tag.find('picture')
        if picture_tag:
            img_tag = picture_tag.find('img')
            if img_tag:
                article_json["preview_image"] = img_tag['src']
        # Author
        author_tag = article_tag.find('span', class_=lambda x: x and x.startswith('card-author-'))
        if author_tag:
            article_json["author"] = author_tag.text.replace("by", "").strip()
        # Comments count
        comments_count_tag = article_tag.find('span', class_=lambda x: x and x.startswith('ellipsisContainer'))
        if comments_count_tag:
            article_json["comments_count"] = comments_count_tag.text.strip()
        # Boosts count
        boosts_count_tag = article_tag.find('button', class_=lambda x: x and x.startswith('boostButton-'))
        if boosts_count_tag:
            aria_label = boosts_count_tag.get('aria-label')
            if aria_label:
                article_json["boosts_count"] = aria_label.split()[0]
            else:
                article_json["boosts_count"] = 0
        else:
            article_json["boosts_count"] = 0
        # Publication info
        publication_datetime_tag = article_tag.find('time', class_=lambda x: x and x.startswith('publication-date-'))
        if publication_datetime_tag:
            article_json["publication_datetime"] = publication_datetime_tag.get('datetime','')
            if publication_datetime_tag.text.strip():
                article_json["is_updated"] = True
        # Idea strategy
        ideas_strategy_tag = article_tag.find('span', class_=lambda x: x and x.startswith('idea-strategy-icon-'))
        if ideas_strategy_tag:
            article_json["idea_strategy"] = ideas_strategy_tag.get('title', '').strip()
        return article_json
