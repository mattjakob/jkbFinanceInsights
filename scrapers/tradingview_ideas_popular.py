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
            
            # Extract metadata for content enhancement
            metadata = self._extract_article_metadata(article)
            
            # Format content with new structure: LIKES -> CONTENT -> COMMENTS
            likes_count = metadata.get('likes', 0)
            formatted_content = content
            
            # Add likes section if available
            if likes_count > 0:
                likes_section = f"------------------------------------------------------------\n{likes_count} PEOPLE LIKED THIS POST OR FOUND IT USEFUL\n------------------------------------------------------------"
                formatted_content = f"{likes_section}\n{formatted_content}"
            
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

    def _create_engagement_summary(self, metadata: Dict[str, Any]) -> str:
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
        - Parses URLs like /chart/BTCUSD/wR44yoxw-Bitcoin-Analysis/
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
            
            debug_info(f"Fetched {len(all_comments)} comments across {page_count} pages for idea {idea_id}")
            
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
            debug_warning(f"Failed to fetch comments for idea {idea_id}: {str(e)}")
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
