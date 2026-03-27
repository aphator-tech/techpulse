"""
Hackaday aggregator - fetches latest projects and posts from Hackaday.
"""

from datetime import datetime
from typing import List
from aggregators.base import BaseAggregator, ContentItem


class HackadayAggregator(BaseAggregator):
    """Fetches latest projects from Hackaday."""
    
    def __init__(self, feed: str = "projects"):
        """Initialize Hackaday aggregator.
        
        Args:
            feed: 'projects', 'blog', or 'tags'
        """
        name = f"Hackaday {feed.title()}"
        super().__init__(name, "hackaday", f"https://hackaday.com/{feed}/feed")
        self.feed = feed
    
    def fetch(self, limit: int = 20) -> List[ContentItem]:
        """Fetch from Hackaday RSS feed."""
        
        # Use RSS feed
        return self._fetch_rss(limit)
    
    def _fetch_rss(self, limit: int = 20) -> List[ContentItem]:
        """Fetch via RSS feed."""
        import feedparser
        
        try:
            feed = feedparser.parse(self.base_url)
            items = []
            
            for entry in feed.entries[:limit]:
                published = None
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    try:
                        published = datetime(*entry.published_parsed[:6])
                    except:
                        pass
                
                # Extract content
                content = entry.get('summary', entry.get('description', ''))
                
                items.append(ContentItem(
                    title=entry.get('title', ''),
                    url=entry.get('link', ''),
                    content=content,
                    author=entry.get('author', ''),
                    published_at=published,
                    external_id=entry.get('id', entry.get('link', '')),
                    metadata={
                        'feed': self.feed,
                    },
                    source_name="Hackaday"
                ))
            
            return items
            
        except Exception as e:
            self.logger.error(f"Failed to fetch from Hackaday: {e}")
            return []


class HackadayBlogAggregator(BaseAggregator):
    """Fetches blog posts from Hackaday."""
    
    def __init__(self):
        super().__init__("Hackaday Blog", "hackaday", "https://hackaday.com/blog/feed")
    
    def fetch(self, limit: int = 20) -> List[ContentItem]:
        """Fetch blog posts."""
        import feedparser
        
        try:
            feed = feedparser.parse(self.base_url)
            items = []
            
            for entry in feed.entries[:limit]:
                published = None
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    try:
                        published = datetime(*entry.published_parsed[:6])
                    except:
                        pass
                
                items.append(ContentItem(
                    title=entry.get('title', ''),
                    url=entry.get('link', ''),
                    content=entry.get('summary', ''),
                    author=entry.get('author', ''),
                    published_at=published,
                    external_id=entry.get('id', ''),
                    source_name="Hackaday Blog"
                ))
            
            return items
            
        except Exception as e:
            self.logger.error(f"Failed to fetch Hackaday blog: {e}")
            return []