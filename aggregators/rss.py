"""
RSS Feed aggregator - fetches from any RSS feed.
"""

from datetime import datetime
from typing import List
import os
from aggregators.base import BaseAggregator, ContentItem


class RSSFeedAggregator(BaseAggregator):
    """Fetches content from RSS feeds."""
    
    FEEDS = [
        'https://feeds.feedburner.com/TechCrunch/',
        'https://www.theverge.com/rss/index.xml',
        'https://wired.com/feed/rss',
        'https://www.engadget.com/rss.xml',
        'https:// Ars Technica RSS',
    ]
    
    def __init__(self, feed_url: str = None):
        name = "Tech News RSS"
        super().__init__(name, "rss", feed_url or 'https://feeds.feedburner.com/TechCrunch/')
        self.feed_url = feed_url or 'https://feeds.feedburner.com/TechCrunch/'
        
    def fetch(self, limit: int = 10) -> List[ContentItem]:
        """Fetch from RSS feed."""
        try:
            response = self.client.get(self.feed_url)
            if response.status_code == 200:
                from xml.etree import ElementTree
                root = ElementTree.fromstring(response.text)
                
                items = []
                ns = {'atom': 'http://www.w3.org/2005/Atom'}
                
                for item in root.findall('.//item')[:limit]:
                    title = item.find('title')
                    link = item.find('link')
                    desc = item.find('description')
                    
                    if title is not None:
                        content_item = ContentItem(
                            title=title.text or '',
                            url=link.text if link is not None else '',
                            source='rss',
                            source_type='rss',
                            raw_data={
                                'title': title.text,
                                'url': link.text if link is not None else '',
                                'description': desc.text if desc is not None else ''
                            }
                        )
                        items.append(content_item)
                return items
        except Exception as e:
            self.logger.error(f"Failed to fetch RSS: {e}")
        
        return []


class WiredAggregator(RSSFeedAggregator):
    """Wired magazine tech news."""
    def __init__(self):
        super().__init__('https://www.wired.com/feed/rss')


class TechCrunchAggregator(RSSFeedAggregator):
    """TechCrunch news."""
    def __init__(self):
        super().__init__('https://feeds.feedburner.com/TechCrunch/')


# Register aggregators
AGGREGATORS = {
    'rss_wired': WiredAggregator,
    'rss_techcrunch': TechCrunchAggregator,
}