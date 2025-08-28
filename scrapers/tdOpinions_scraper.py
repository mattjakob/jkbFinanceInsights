"""
/**
*
*  ┌─────────────────────────────────────┐
*  │      TDOPINIONS_SCRAPER             │
*  └─────────────────────────────────────┘
*  TradingView Opinions (Minds) Scraper
*
*  Scrapes opinions and discussions from TradingView's minds/discussions section
*  for a specific symbol and exchange, extracting user-generated content, comments,
*  and engagement metrics.
*
*  Parameters:
*  - symbol: The trading symbol (e.g., 'BTCUSD')
*  - exchange: The exchange (e.g., 'BINANCE')
*  - maxItems: Maximum number of opinions to fetch
*
*  Returns:
*  - List of processed insight items with opinion data
*
*  Notes:
*  - Uses TradingView's minds API endpoints
*  - Extracts likes, comments count, and full opinion text
*  - Includes author information and timestamps
*/
"""

import requests
import json
import time
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from debugger import debug_info, debug_warning, debug_error, debug_success
from scrapers.feed_scraper import FeedScraper
import items_management
from config import SCRAPER_TIMEOUT, SCRAPER_MAX_RETRIES, SCRAPER_RETRY_DELAY


class TradingViewOpinionsScraper(FeedScraper):
    """
    /**
    *
    *  ┌─────────────────────────────────────┐
    *  │   TRADINGVIEWOPINIONSSCRAPER        │
    *  └─────────────────────────────────────┘
    *  Scraper for TradingView minds/discussions section
    *
    *  Extracts user opinions, discussions, and market sentiment from
    *  TradingView's community-driven content for specific trading symbols.
    *
    *  Parameters:
    *  - Inherits from FeedScraper base class
    *
    *  Returns:
    *  - Processed opinion data as insight items
    *
    *  Notes:
    *  - Handles pagination and API rate limiting
    *  - Extracts likes, comments, and engagement metrics
    */
    """
    
    def __init__(self):
        """Initialize the TradingView Opinions scraper."""
        super().__init__("TD OPINIONS")
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Referer': 'https://www.tradingview.com/',
        }
        debug_info("TradingView Opinions scraper initialized")
    
    def fetch(self, symbol: str, exchange: str, maxItems: int, sinceLast: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        /**
        *
        *  ┌─────────────────────────────────────┐
        *  │             FETCH                   │
        *  └─────────────────────────────────────┘
        *  Fetch opinions from TradingView minds API
        *
        *  Retrieves user-generated opinions and discussions for a specific
        *  trading symbol from TradingView's community section.
        *
        *  Parameters:
        *  - symbol: Trading symbol (e.g., 'BTCUSD')
        *  - exchange: Exchange name (e.g., 'BINANCE')
        *  - maxItems: Maximum number of opinions to fetch
        *
        *  Returns:
        *  - List of processed insight items
        *
        *  Notes:
        *  - Uses TradingView minds API
        *  - Includes comment fetching for engagement data
        */
        """
        debug_info(f"Starting TradingView Opinions fetch for {exchange}:{symbol} (max: {maxItems})")
        
        try:
            # Build API URL
            minds_url = f"https://www.tradingview.com/api/v1/minds/?symbol={symbol}"
            if maxItems and maxItems > 0:
                minds_url += f"&limit={maxItems}"
            
            debug_info(f"Fetching opinions from: {minds_url}")
            
            # Make API request
            response = requests.get(minds_url, headers=self.headers, timeout=SCRAPER_TIMEOUT)
            response.raise_for_status()
            
            data = response.json()
            opinions = data.get('results', [])
            
            debug_info(f"Retrieved {len(opinions)} opinions")
            
            if not opinions:
                debug_warning("No opinions found")
                return []
            
            # Process opinions
            processed_items = []
            successful_inserts = 0
            
            for opinion in opinions[:maxItems] if maxItems else opinions:
                try:
                    # Extract basic opinion data
                    title = self._extract_title(opinion)
                    content = opinion.get('text', '')
                    if not content:
                        debug_warning(f"Skipping opinion with no content: {title}")
                        continue
                    
                    # Extract author information
                    author = opinion.get('author', {})
                    author_name = author.get('username', 'Unknown')
                    
                    # Extract engagement metrics
                    likes_count = opinion.get('total_likes', 0)
                    comments_count = opinion.get('total_comments', 0)
                    
                    # Extract timestamp
                    timePosted = opinion.get('created')
                    if not timePosted:
                        debug_warning(f"Skipping opinion with no timestamp: {title}")
                        continue
                    
                    # Parse timestamp to ISO format
                    try:
                        # The API returns ISO format like "2025-08-27T20:08:56.834327+00:00"
                        # Parse as UTC timestamp
                        if isinstance(timePosted, str):
                            # Parse the timestamp
                            if timePosted.endswith('+00:00'):
                                # Replace +00:00 with Z for standard ISO format
                                dt = datetime.fromisoformat(timePosted.replace('+00:00', '+00:00'))
                            elif 'Z' in timePosted:
                                dt = datetime.fromisoformat(timePosted.replace('Z', '+00:00'))
                            else:
                                # Assume UTC if no timezone info
                                dt = datetime.fromisoformat(timePosted).replace(tzinfo=timezone.utc)
                            
                            # Convert to local time for storage
                            local_dt = dt.astimezone()
                            timePosted = local_dt.isoformat()
                        else:
                            debug_warning(f"Unexpected timestamp format: {timePosted}")
                            continue
                    except Exception as e:
                        debug_warning(f"Failed to parse timestamp {timePosted}: {str(e)}")
                        continue
                    
                    # Extract image URL from chart snapshots (not avatars)
                    imageURL = ""
                    if 'snapshot_url' in opinion:
                        imageURL = opinion['snapshot_url']
                    
                    # Add engagement information to content
                    engagement_content = self._build_engagement_content(likes_count, comments_count, opinion)
                    if engagement_content:
                        content += "\n\n" + engagement_content
                    
                    # Add author information to content
                    content += f"\n\n--- Posted by: {author_name}"
                    if author.get('badges'):
                        badges = [badge.get('verbose_name', '') for badge in author.get('badges', [])]
                        if badges:
                            content += f" ({', '.join(badges)})"
                    
                    # Create insight item
                    insight_id, is_new = items_management.add_insight(
                        type=self.type,
                        title=title,
                        content=content,
                        timePosted=timePosted,
                        symbol=symbol.upper(),
                        exchange=exchange.upper(),
                        imageURL=imageURL
                    )
                    
                    processed_item = {
                        "title": title,
                        "content": content,
                        "timePosted": timePosted,
                        "symbol": symbol.upper(),
                        "exchange": exchange.upper(),
                        "imageURL": imageURL,
                        "insight_id": insight_id,
                        "status": "created" if is_new else "duplicate"
                    }
                    processed_items.append(processed_item)
                    if is_new:
                        successful_inserts += 1
                    
                except Exception as e:
                    debug_error(f"Failed to process opinion: {str(e)}")
                    processed_items.append({
                        "title": opinion.get("text", "Unknown")[:50] + "...",
                        "status": "failed",
                        "error": str(e)
                    })
                    continue
            
            self.update_fetch_time()
            debug_success(f"TradingView Opinions fetch completed: {successful_inserts}/{len(opinions)} items processed successfully")
            return processed_items
            
        except Exception as e:
            debug_error(f"TradingView Opinions fetch failed: {str(e)}")
            return []
    
    def _extract_title(self, opinion: Dict[str, Any]) -> str:
        """
        /**
        *
        *  ┌─────────────────────────────────────┐
        *  │          EXTRACT_TITLE              │
        *  └─────────────────────────────────────┘
        *  Extract a meaningful title from opinion text
        *
        *  Creates a title from the first line or sentence of the opinion
        *  content, with fallback to a generic title.
        *
        *  Parameters:
        *  - opinion: Opinion data dictionary
        *
        *  Returns:
        *  - Extracted title string
        *
        *  Notes:
        *  - Uses first line or first 100 characters as title
        */
        """
        text = opinion.get('text', '')
        if not text:
            return "TradingView Opinion"
        
        # Try to get first line as title
        first_line = text.split('\n')[0].strip()
        if first_line and len(first_line) <= 100:
            return first_line
        
        # If first line is too long, truncate it
        if len(first_line) > 100:
            return first_line[:97] + "..."
        
        # Fallback to first 100 characters
        if len(text) > 100:
            return text[:97] + "..."
        
        return text
    
    def _build_engagement_content(self, likes_count: int, comments_count: int, opinion: Dict[str, Any]) -> str:
        """
        /**
        *
        *  ┌─────────────────────────────────────┐
        *  │       BUILD_ENGAGEMENT_CONTENT      │
        *  └─────────────────────────────────────┘
        *  Build engagement metrics content string
        *
        *  Creates formatted content showing likes and comments information
        *  for the opinion, including actual comment messages when available.
        *
        *  Parameters:
        *  - likes_count: Number of likes
        *  - comments_count: Number of comments
        *  - opinion: Opinion data dictionary
        *
        *  Returns:
        *  - Formatted engagement content string
        *
        *  Notes:
        *  - Follows same format as Ideas scrapers
        *  - Fetches and includes actual comment messages
        */
        """
        engagement_parts = []
        
        # Add likes information if any
        if likes_count > 0:
            engagement_parts.append(f"{likes_count} PEOPLE FOUND THIS USEFUL")
        
        # Add comments information
        comments_content = f"COMMENTS: {comments_count}"
        
        # Fetch actual comment messages if comments exist
        if comments_count > 0:
            try:
                post_id = opinion.get('uid')
                if post_id:
                    comments_url = f"https://www.tradingview.com/api/v1/minds/{post_id}/comments/"
                    comments_response = requests.get(comments_url, headers=self.headers, timeout=SCRAPER_TIMEOUT)
                    
                    if comments_response.status_code == 200:
                        comments_data = comments_response.json()
                        if isinstance(comments_data, list) and comments_data:
                            # Add comment messages
                            for comment in comments_data:
                                comment_text = comment.get('text', '').strip()
                                if comment_text:
                                    author_name = comment.get('author', {}).get('username', 'Anonymous')
                                    comments_content += f"\n- {author_name}: {comment_text}"
            except Exception as e:
                debug_warning(f"Failed to fetch comments for opinion {opinion.get('uid', 'unknown')}: {str(e)}")
        
        engagement_parts.append(comments_content)
        
        return "\n".join(engagement_parts)
