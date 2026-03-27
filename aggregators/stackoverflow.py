"""
Stack Overflow aggregator - fetches trending questions.
"""

from datetime import datetime
from typing import List
import os
from aggregators.base import BaseAggregator, ContentItem


class StackOverflowAggregator(BaseAggregator):
    """Fetches trending questions from Stack Overflow."""
    
    TAGS = ['python', 'javascript', 'java', 'c#', 'php', 'android', 'html', 'jquery', 'c++', 'css']
    
    def __init__(self, tag: str = 'python'):
        name = f"Stack Overflow {tag}"
        super().__init__(name, "stackoverflow", f"https://stackoverflow.com/questions/tagged/{tag}")
        self.tag = tag
        
    def fetch(self, limit: int = 10) -> List[ContentItem]:
        """Fetch trending questions."""
        url = f"https://api.stackexchange.com/2.3/questions?order=desc&sort=activity&tagged={self.tag}&site=stackoverflow&pagesize={limit}"
        
        try:
            response = self.client.get(url)
            if response.status_code == 200:
                data = response.json()
                items = []
                for item in data.get('items', []):
                    content_item = ContentItem(
                        title=item.get('title', ''),
                        url=item.get('link', ''),
                        source='stackoverflow',
                        source_type='stackoverflow',
                        raw_data=item
                    )
                    items.append(content_item)
                return items
        except Exception as e:
            self.logger.error(f"Failed to fetch from Stack Overflow: {e}")
        
        return []


# Register aggregators
AGGREGATORS = {
    'stackoverflow': StackOverflowAggregator,
}