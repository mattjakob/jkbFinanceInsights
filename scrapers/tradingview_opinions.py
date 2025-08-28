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
        # API has a maximum limit of ~20 items, so cap the request
        api_limit = min(limit, 20) if limit else 20
        url = f"https://www.tradingview.com/api/v1/minds/?symbol={symbol}&limit={api_limit}"
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
        
        # Fetch actual comment content if available
        comment_content = ""
        mind_uid = item.get('uid')
        if mind_uid and comments_count > 0:
            comment_content = self._fetch_comments(mind_uid)
        
        metadata = {
            'author': author,
            'post_type': 'opinion',
            'likes': likes_count,
            'comments': comments_count,
            'comment_content': comment_content
        }
        
        # Format content with new structure: LIKES -> CONTENT -> COMMENTS
        formatted_content = content
        
        # Add likes section if available
        if likes_count > 0:
            likes_section = f"------------------------------------------------------------\n{likes_count} PEOPLE LIKED THIS POST OR FOUND IT USEFUL\n------------------------------------------------------------"
            formatted_content = f"{likes_section}\n{formatted_content}"
        
        # Add comments section if available
        if comment_content and comments_count > 0:
            formatted_comments = self._format_comments_section(comment_content, comments_count)
            formatted_content = f"{formatted_content}\n{formatted_comments}"
        
        # Use the formatted content
        content = formatted_content
        
        # Extract image URL (check for snapshot data)
        image_url = self._extract_image_url(item)
        
        # Parse timestamp
        timestamp = self._parse_timestamp(item)
        if not timestamp:
            debug_warning(f"Skipping opinion with no timestamp: {title}")
            return None
        
        # Image URL already extracted above
        
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

    def _fetch_comments(self, mind_uid: str) -> str:
        """
        ┌─────────────────────────────────────┐
        │           FETCH COMMENTS            │
        └─────────────────────────────────────┘
        Fetches comment content for a specific mind/opinion.
        
        Parameters:
        - mind_uid: Unique identifier for the mind/opinion
        
        Returns:
        - Formatted comment content string
        
        Notes:
        - Makes separate API call to get comment content
        - Formats comments with author and timestamp
        - Limits to 5 comments for readability
        """
        if not mind_uid:
            return ""
        
        try:
            comment_url = f"https://www.tradingview.com/api/v1/minds/{mind_uid}/comments/"
            response = self.make_request(comment_url)
            comments = response.json()
            
            if not isinstance(comments, list) or not comments:
                return ""
            
            comment_texts = []
            
            # Process up to 5 comments
            for comment in comments[:5]:
                if not isinstance(comment, dict):
                    continue
                
                # Extract comment data
                text = comment.get('text', '').strip()
                if not text:
                    continue
                
                # Extract author
                author_info = comment.get('author', {})
                author = author_info.get('username', 'Anonymous') if isinstance(author_info, dict) else 'Anonymous'
                
                # Extract and format timestamp
                created = comment.get('created', '')
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
                    comment_texts.append(f"@{author} ({timestamp_str}): {text}")
                else:
                    comment_texts.append(f"@{author}: {text}")
            
            return "\n".join(comment_texts)
            
        except Exception as e:
            from debugger import debug_warning
            debug_warning(f"Failed to fetch comments for mind {mind_uid}: {str(e)}")
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

    def _extract_image_url(self, item: dict) -> str:
        """
        ┌─────────────────────────────────────┐
        │          EXTRACT IMAGE URL          │
        └─────────────────────────────────────┘
        Extracts image URL from opinion item data.
        
        Parameters:
        - item: Opinion item dictionary from API
        
        Returns:
        - Image URL string or empty string if none found
        
        Notes:
        - Checks for snapshot_url field (chart images)
        - Searches text content for embedded image URLs
        - Does not use avatar pictures per user preference
        """
        # First, check for snapshot_url (chart images)
        snapshot_url = item.get('snapshot_url', '')
        if snapshot_url and snapshot_url.startswith('http'):
            return snapshot_url
        
        # Second, look for image URLs in the text content
        text = item.get('text', '')
        if text:
            import re
            urls = re.findall(r'http[s]?://[^\s]+', text)
            for url in urls:
                # Look for image file extensions
                if any(ext in url.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp']):
                    return url
        
        # Third, if no snapshot_url in main item, fetch individual mind data
        mind_uid = item.get('uid', '')
        if mind_uid:
            try:
                mind_url = f"https://www.tradingview.com/api/v1/minds/{mind_uid}/"
                response = self.make_request(mind_url)
                mind_data = response.json()
                
                # Check for snapshot_url in individual mind data
                individual_snapshot_url = mind_data.get('snapshot_url', '')
                if individual_snapshot_url and individual_snapshot_url.startswith('http'):
                    return individual_snapshot_url
                    
            except Exception as e:
                # Don't log this as it's not critical - just return empty
                pass
        
        return ""




