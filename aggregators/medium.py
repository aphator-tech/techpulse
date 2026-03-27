"""
Medium aggregator - fetches trending tech articles from Medium.
"""

from datetime import datetime
from typing import List
import os
from aggregators.base import BaseAggregator, ContentItem


class MediumAggregator(BaseAggregator):
    """Fetches trending articles from Medium."""
    
    TOPICS = ['technology', 'programming', 'artificial-intelligence', 'web-development', 'data-science']
    
    def __init__(self, topic: str = 'technology'):
        name = f"Medium {topic}"
        super().__init__(name, "medium", f"https://medium.com/topic/{topic}")
        self.topic = topic
        
    def fetch(self, limit: int = 10) -> List[ContentItem]:
        """Fetch trending Medium articles."""
        url = f"https://medium.com/feed/topic/{self.topic}"
        
        try:
            response = self.client.get(url)
            if response.status_code == 200:
                # Parse RSS feed
                from xml.etree import ElementTree
                root = ElementTree.fromstring(response.text)
                
                items = []
                ns = {'atom': 'http://www.w3.org/2005/Atom'}
                
                for item in root.findall('.//atom:entry', ns)[:limit]:
                    title = item.find('atom:title', ns)
                    link = item.find('atom:link', ns)
                    content = item.find('atom:content', ns)
                    
                    if title is not None:
                        content_item = ContentItem(
                            title=title.text or '',
                            url=link.attrib.get('href', '') if link is not None else '',
                            source='medium',
                            source_type='medium',
                            raw_data={
                                'title': title.text,
                                'url': link.attrib.get('href', '') if link is not None else '',
                                'content': content.text if content is not None else ''
                            }
                        )
                        items.append(content_item)
                return items
        except Exception as e:
            self.logger.error(f"Failed to fetch from Medium: {e}")
        
        return []


# Register aggregators
AGGREGATORS = {
    'medium': MediumAggregator,
}