"""
CSS-Tricks aggregator - web design tutorials.
"""

from typing import List
from aggregators.base import BaseAggregator, ContentItem


class CSSTricksAggregator(BaseAggregator):
    """Fetches articles from CSS-Tricks."""
    
    def __init__(self):
        name = "CSS-Tricks"
        super().__init__(name, "csstricks", "https://css-tricks.com/feed")
        
    def fetch(self, limit: int = 10) -> List[ContentItem]:
        url = "https://css-tricks.com/feed"
        
        try:
            response = self.client.get(url)
            if response.status_code == 200:
                from xml.etree import ElementTree
                root = ElementTree.fromstring(response.text)
                
                items = []
                for item in root.findall('.//item')[:limit]:
                    title = item.find('title')
                    link = item.find('link')
                    
                    if title is not None:
                        content_item = ContentItem(
                            title=title.text or '',
                            url=link.text if link is not None else '',
                            source='csstricks',
                            source_type='csstricks',
                            raw_data={'title': title.text}
                        )
                        items.append(content_item)
                return items
        except Exception as e:
            self.logger.error(f"Failed: {e}")
        
        return []


class SitePointAggregator(BaseAggregator):
    """SitePoint web development tutorials."""
    
    def __init__(self):
        name = "SitePoint"
        super().__init__(name, "sitepoint", "https://www.sitepoint.com/feed")
        
    def fetch(self, limit: int = 10) -> List[ContentItem]:
        url = "https://www.sitepoint.com/feed"
        
        try:
            response = self.client.get(url)
            if response.status_code == 200:
                from xml.etree import ElementTree
                root = ElementTree.fromstring(response.text)
                
                items = []
                for item in root.findall('.//item')[:limit]:
                    title = item.find('title')
                    link = item.find('link')
                    
                    if title is not None:
                        content_item = ContentItem(
                            title=title.text or '',
                            url=link.text if link is not None else '',
                            source='sitepoint',
                            source_type='sitepoint',
                            raw_data={'title': title.text}
                        )
                        items.append(content_item)
                return items
        except Exception as e:
            self.logger.error(f"Failed: {e}")
        
        return []


AGGREGATORS = {'csstricks': CSSTricksAggregator, 'sitepoint': SitePointAggregator}