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
        """Fetch recent ideas from TradingView using JSON API with pagination"""
        if not symbol:
            raise ValueError("Symbol required for fetching ideas")
        
        all_items = []
        page = 1
        max_pages = max(10, (limit // 20) + 2) if limit else 10  # Scale pages with requested limit
        
        while len(all_items) < limit and page <= max_pages:
            # Build URL for recent ideas with pagination
            url = f"https://www.tradingview.com/symbols/{symbol}/ideas/?component-data-only=1&sort=recent&page={page}"
            
            try:
                # Fetch JSON response
                response = self.make_request(url)
                
                # Parse JSON response
                try:
                    data = response.json()
                except Exception as e:
                    debug_error(f"Failed to parse JSON response for page {page}: {str(e)}")
                    break
                
                # Handle different response structures
                if isinstance(data, str):
                    debug_error(f"Unexpected string response on page {page}: {data}")
                    break
                
                # The JSON structure is data.ideas.data.items
                ideas_data = data.get('data', {}).get('ideas', {})
                items = ideas_data.get('data', {}).get('items', []) if isinstance(ideas_data, dict) else []
                
                if not items:
                    debug_info(f"No more items found on page {page}")
                    break
                
                debug_info(f"Found {len(items)} recent ideas on page {page}")
                
                # Add items to collection
                all_items.extend(items)
                page += 1
                
            except Exception as e:
                debug_error(f"Error fetching page {page}: {str(e)}")
                break
        
        if not all_items:
            debug_warning(f"No recent ideas found for {exchange}:{symbol}")
            return []
        
        debug_info(f"Total collected: {len(all_items)} recent ideas across {page-1} pages")
        
        # Sort by date and limit to requested amount
        all_items = sorted(all_items, key=lambda x: x.get('published', 0), reverse=True)
        items_to_process = all_items[:limit] if limit else all_items
        
        # Process each idea item
        scraped_items = []
        for idx, item in enumerate(items_to_process):
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
        
        # Format content with new structure: LIKES -> CONTENT -> COMMENTS
        likes_count = metadata.get('likes', 0)
        formatted_content = content
        
        # Add likes section if available
        if likes_count > 0:
            likes_section = f"------------------------------------------------------------\n{likes_count} PEOPLE LIKED THIS POST OR FOUND IT USEFUL\n------------------------------------------------------------"
            formatted_content = f"{likes_section}\n{formatted_content}"
        
        # Parse timestamp - use current time if not available
        timestamp = self._parse_timestamp(item)
        if not timestamp:
            timestamp = datetime.now()
        
        # Extract other fields - handle image dict
        image_info = item.get('image', {})
        if isinstance(image_info, dict):
            image_url = image_info.get('middle', image_info.get('big', ''))
        else:
            image_url = str(image_info) if image_info else ''
        
        source_url = item.get('chart_url', item.get('link', item.get('url', '')))
        
        # Extract idea ID and fetch comments
        idea_id = self._extract_idea_id(source_url)
        comment_content = ""
        if idea_id and metadata.get('comments', 0) > 0:
            comment_content = self._fetch_idea_comments(idea_id)
        
        # Add comment content to metadata and formatted content
        if comment_content:
            metadata['comment_content'] = comment_content
            comments_count = metadata.get('comments', 0)
            if comments_count > 0:
                formatted_comments = self._format_comments_section(comment_content, comments_count)
                formatted_content = f"{formatted_content}\n{formatted_comments}"
        
        # Use the formatted content
        content = formatted_content
        
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

    def _extract_idea_id(self, url: str) -> str:
        """
        ┌─────────────────────────────────────┐
        │           EXTRACT IDEA ID           │
        └─────────────────────────────────────┘
        Extracts idea ID from TradingView idea URL.
        
        Parameters:
        - url: TradingView idea URL
        
        Returns:
        - Idea ID string or empty string if not found
        
        Notes:
        - Parses URLs like /chart/BTCUSD/i1eMvd0M-BTC-Analysis/
        - Extracts the ID part before the first dash
        """
        if not url:
            return ""
        
        import re
        # Pattern to match /chart/SYMBOL/ID-TITLE/ or /chart/SYMBOL/ID/
        match = re.search(r'/chart/[^/]+/([^-/]+)', url)
        if match:
            return match.group(1)
        return ""

    def _fetch_idea_comments(self, idea_id: str) -> str:
        """
        ┌─────────────────────────────────────┐
        │         FETCH IDEA COMMENTS         │
        └─────────────────────────────────────┘
        Fetches comment content for a specific idea with pagination.
        
        Parameters:
        - idea_id: TradingView idea ID
        
        Returns:
        - Formatted comment content string
        
        Notes:
        - Makes paginated API calls to get all comments
        - Formats comments with author and timestamp
        - Limits to 10 comments for readability
        - Handles cursor-based pagination
        """
        if not idea_id:
            return ""
        
        try:
            all_comments = []
            next_url = f"https://www.tradingview.com/api/v1/ideas/{idea_id}/comments/"
            max_pages = 5  # Limit to 5 pages to avoid excessive API calls
            page_count = 0
            
            while next_url and page_count < max_pages:
                response = self.make_request(next_url)
                data = response.json()
                
                if not isinstance(data, dict) or 'results' not in data:
                    break
                
                page_comments = data['results']
                if not isinstance(page_comments, list):
                    break
                
                all_comments.extend(page_comments)
                
                # Get next page URL
                next_url = data.get('next')
                page_count += 1
                
                # Stop if we have enough comments
                if len(all_comments) >= 50:  # Limit total comments to prevent excessive content
                    break
            
            if not all_comments:
                return ""
            
            from debugger import debug_info
            debug_info(f"Fetched {len(all_comments)} comments across {page_count} pages for recent idea {idea_id}")
            
            comment_texts = []
            
            # Process ALL comments (no limit)
            for comment in all_comments:
                if not isinstance(comment, dict):
                    continue
                
                # Extract comment data
                text = comment.get('comment', '').strip()
                if not text:
                    continue
                
                # Extract author
                user_info = comment.get('user', {})
                username = user_info.get('username', 'Anonymous') if isinstance(user_info, dict) else 'Anonymous'
                
                # Extract and format timestamp
                created = comment.get('created_at', '')
                timestamp_str = ""
                if created:
                    try:
                        from datetime import datetime
                        dt = datetime.fromisoformat(created.replace('Z', '+00:00'))
                        timestamp_str = dt.strftime('%m/%d %H:%M')
                    except:
                        timestamp_str = created[:10]  # Just the date part
                
                # Limit comment length but keep it reasonable
                if len(text) > 500:
                    text = text[:497] + "..."
                
                # Format comment
                if timestamp_str:
                    comment_texts.append(f"@{username} ({timestamp_str}): {text}")
                else:
                    comment_texts.append(f"@{username}: {text}")
            
            return "\n".join(comment_texts)
            
        except Exception as e:
            from debugger import debug_warning
            debug_warning(f"Failed to fetch comments for recent idea {idea_id}: {str(e)}")
            return ""

    def _format_comments_section(self, comment_content: str, comments_count: int) -> str:
        """
        ┌─────────────────────────────────────┐
        │       FORMAT COMMENTS SECTION       │
        └─────────────────────────────────────┘
        Formats comments into numbered section with separators.
        
        Parameters:
        - comment_content: Raw comment content string
        - comments_count: Total number of comments
        
        Returns:
        - Formatted comments section string
        
        Notes:
        - Numbers each comment (01:, 02:, etc.)
        - Adds separators between comments
        - Wraps entire section with header and footer lines
        """
        if not comment_content:
            return ""
        
        comment_lines = comment_content.split('\n')
        formatted_comments = []
        
        for i, comment_line in enumerate(comment_lines):
            if comment_line.strip():
                comment_number = f"{i+1:02d}"
                formatted_comments.append(f"{comment_number}: {comment_line}")
                if i < len(comment_lines) - 1 and comment_lines[i+1].strip():
                    formatted_comments.append("------------------------------")
        
        comments_header = f"------------------------------------------------------------\n{comments_count} AVAILABLE COMMENTS:"
        comments_footer = "------------------------------------------------------------"
        
        return f"{comments_header}\n" + "\n".join(formatted_comments) + f"\n{comments_footer}"
