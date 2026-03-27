"""
Smashing Magazine aggregator - fetches web dev tutorials.
"""

from datetime import datetime
from typing import List
from aggregators.base import BaseAggregator, ContentItem


class SmashingMagazineAggregator(BaseAggregator):
    """Fetches articles from Smashing Magazine."""
    
    def __init__(self):
        name = "Smashing Magazine"
        super().__init__(name, "smashing", "https://www.smashingmagazine.com/feed")
        
    def fetch(self, limit: int = 10) -> List[ContentItem]:
        """Fetch articles from Smashing Magazine."""
        url = "https://www.smashingmagazine.com/feed"
        
        try:
            response = self.client.get(url)
            if response.status_code == 200:
                from xml.etree import ElementTree
                root = ElementTree.fromstring(response.text)
                
                items = []
                for item in root.findall('.//item')[:limit]:
                    title = item.find('title')
                    link = item.find('link')
                    desc = item.find('description')
                    
                    if title is not None:
                        content_item = ContentItem(
                            title=title.text or '',
                            url=link.text if link is not None else '',
                            source='smashing',
                            source_type='smashing',
                            raw_data={'title': title.text, 'url': link.text if link is not None else ''}
                        )
                        items.append(content_item)
                return items
        except Exception as e:
            self.logger.error(f"Failed to fetch from Smashing: {e}")
        
        return []


# Register
AGGREGATORS = {'smashing': SmashingMagazineAggregator}