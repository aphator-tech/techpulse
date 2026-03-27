"""
Dev.to aggregator - fetches trending articles from Dev.to.
"""

from datetime import datetime
from typing import List
import os
from aggregators.base import BaseAggregator, ContentItem


class DevToAggregator(BaseAggregator):
    """Fetches trending articles from Dev.to."""
    
    def __init__(self, tag: str = None):
        name = f"Dev.to {tag or 'Trending'}"
        super().__init__(name, "devto", "https://dev.to/api")
        self.tag = tag
        self.api_key = os.environ.get('DEVTO_API_KEY')
    
    def fetch(self, limit: int = 20) -> List[ContentItem]:
        """Fetch articles from Dev.to."""
        
        params = {'per_page': min(limit, 30)}
        
        if self.tag:
            url = f"{self.base_url}/articles"
            params['tag'] = self.tag
        else:
            url = f"{self.base_url}/articles"
            params['top'] = 7  # Top in last 7 days
        
        headers = {}
        if self.api_key:
            headers['api-key'] = self.api_key
        
        try:
            response = self.client.get(url, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            items = []
            for article in data:
                # Parse published date
                published = None
                if article.get('published_at'):
                    try:
                        published = datetime.fromisoformat(article['published_at'].replace('Z', '+00:00'))
                    except:
                        pass
                
                items.append(ContentItem(
                    title=article.get('title', ''),
                    url=article.get('url', ''),
                    content=article.get('description', ''),
                    author=article.get('user', {}).get('name', ''),
                    published_at=published,
                    external_id=str(article.get('id', '')),
                    metadata={
                        'reactions': article.get('public_reactions_count', 0),
                        'comments': article.get('comments_count', 0),
                        'views': article.get('page_views_count', 0),
                        'tags': article.get('tag_list', []),
                        'reading_time': article.get('reading_time_minutes', 0),
                    },
                    source_name="Dev.to"
                ))
            
            return items
            
        except Exception as e:
            self.logger.error(f"Failed to fetch from Dev.to: {e}")
            return []


class DevToLatestAggregator(BaseAggregator):
    """Fetches latest articles from Dev.to."""
    
    def __init__(self):
        super().__init__("Dev.to Latest", "devto", "https://dev.to/api")
    
    def fetch(self, limit: int = 20) -> List[ContentItem]:
        """Fetch latest articles."""
        
        params = {'per_page': min(limit, 30), 'state': 'fresh'}
        
        try:
            response = self.client.get(f"{self.base_url}/articles", params=params)
            response.raise_for_status()
            data = response.json()
            
            items = []
            for article in data:
                published = None
                if article.get('published_at'):
                    try:
                        published = datetime.fromisoformat(article['published_at'].replace('Z', '+00:00'))
                    except:
                        pass
                
                items.append(ContentItem(
                    title=article.get('title', ''),
                    url=article.get('url', ''),
                    content=article.get('description', ''),
                    author=article.get('user', {}).get('name', ''),
                    published_at=published,
                    external_id=str(article.get('id', '')),
                    metadata={
                        'reactions': article.get('public_reactions_count', 0),
                        'comments': article.get('comments_count', 0),
                    },
                    source_name="Dev.to Latest"
                ))
            
            return items
            
        except Exception as e:
            self.logger.error(f"Failed to fetch latest from Dev.to: {e}")
            return []