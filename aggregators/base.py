"""
Base aggregator class for content sources.
Provides common functionality and interface for all content fetchers.
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import httpx
from bs4 import BeautifulSoup


logger = logging.getLogger(__name__)


@dataclass
class ContentItem:
    """Represents a single content item from a source."""
    title: str
    url: str
    content: Optional[str] = None
    author: Optional[str] = None
    published_at: Optional[datetime] = None
    external_id: Optional[str] = None
    metadata: Dict[str, Any] = None
    source_name: str = ""
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class BaseAggregator(ABC):
    """Base class for all content aggregators."""
    
    def __init__(self, name: str, source_type: str, base_url: str = None):
        """Initialize aggregator.
        
        Args:
            name: Display name for this source
            source_type: Type of content source
            base_url: Base URL for the source
        """
        self.name = name
        self.source_type = source_type
        self.base_url = base_url
        self.logger = logging.getLogger(f"{__name__}.{name}")
        self.client = httpx.Client(
            timeout=30.0,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        )
    
    @abstractmethod
    def fetch(self, limit: int = 20) -> List[ContentItem]:
        """Fetch content from the source.
        
        Args:
            limit: Maximum number of items to fetch
            
        Returns:
            List of ContentItem objects
        """
        pass
    
    def fetch_html(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch and parse HTML content.
        
        Args:
            url: URL to fetch
            
        Returns:
            BeautifulSoup object or None on failure
        """
        try:
            response = self.client.get(url)
            response.raise_for_status()
            return BeautifulSoup(response.text, 'lxml')
        except Exception as e:
            self.logger.error(f"Failed to fetch {url}: {e}")
            return None
    
    def fetch_json(self, url: str, headers: Dict = None) -> Optional[Dict]:
        """Fetch and parse JSON content.
        
        Args:
            url: URL to fetch
            headers: Additional headers
            
        Returns:
            JSON dict or None on failure
        """
        try:
            req_headers = {'Accept': 'application/json'}
            if headers:
                req_headers.update(headers)
            response = self.client.get(url, headers=req_headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self.logger.error(f"Failed to fetch JSON from {url}: {e}")
            return None
    
    def close(self):
        """Close HTTP client."""
        self.client.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class RSSAggregator(BaseAggregator):
    """Aggregator for RSS/Atom feeds."""
    
    def __init__(self, name: str, feed_url: str):
        super().__init__(name, "rss", feed_url)
        self.feed_url = feed_url
    
    def fetch(self, limit: int = 20) -> List[ContentItem]:
        """Fetch from RSS feed."""
        import feedparser
        
        try:
            feed = feedparser.parse(self.feed_url)
            items = []
            
            for entry in feed.entries[:limit]:
                published = None
                if hasattr(entry, 'published'):
                    try:
                        published = datetime(*entry.published_parsed[:6])
                    except:
                        pass
                elif hasattr(entry, 'updated'):
                    try:
                        published = datetime(*entry.updated_parsed[:6])
                    except:
                        pass
                
                items.append(ContentItem(
                    title=entry.get('title', ''),
                    url=entry.get('link', ''),
                    content=entry.get('summary', entry.get('description', '')),
                    author=entry.get('author', entry.get('dc_creator', '')),
                    published_at=published,
                    external_id=entry.get('id', entry.get('link', '')),
                    source_name=self.name
                ))
            
            return items
            
        except Exception as e:
            self.logger.error(f"Failed to parse RSS feed {self.feed_url}: {e}")
            return []


class APIAggregator(BaseAggregator):
    """Base class for API-based aggregators."""
    
    def __init__(self, name: str, source_type: str, base_url: str, api_key: str = None):
        super().__init__(name, source_type, base_url)
        self.api_key = api_key
    
    def get_auth_headers(self) -> Dict:
        """Get authentication headers for API requests."""
        return {}