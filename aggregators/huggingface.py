"""
Hugging Face aggregator - fetches trending models, papers, and spaces.
"""

from datetime import datetime
from typing import List
import os
from aggregators.base import BaseAggregator, ContentItem


class HuggingFaceTrendingAggregator(BaseAggregator):
    """Fetches trending items from Hugging Face."""
    
    def __init__(self, category: str = "models"):
        """Initialize Hugging Face aggregator.
        
        Args:
            category: 'models', 'papers', or 'spaces'
        """
        name = f"Hugging Face {category.title()}"
        super().__init__(name, "huggingface", f"https://huggingface.co/{category}")
        self.category = category
        self.api_key = os.environ.get('HUGGING_FACE_API_KEY')
    
    def fetch(self, limit: int = 20) -> List[ContentItem]:
        """Fetch trending items from Hugging Face."""
        
        # Use the trending API endpoint
        url = f"https://huggingface.co/api/{self.category}"
        
        params = {
            'sort': 'likes',
            'direction': -1,
            'limit': limit,
            'full': 'true'
        }
        
        headers = {}
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'
        
        try:
            response = self.client.get(url, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            items = []
            for item in data:
                # Parse last modified date
                updated = None
                if item.get('lastModified'):
                    try:
                        updated = datetime.fromisoformat(item['lastModified'].replace('Z', '+00:00'))
                    except:
                        pass
                
                item_type = self.category.rstrip('s')
                items.append(ContentItem(
                    title=f"[{item_type.upper()}] {item.get('id', '')}",
                    url=f"https://huggingface.co/{item.get('id', '')}",
                    content=item.get('card_data', {}).get('summary', '') or 
                           item.get('pipeline_tag', ''),
                    author=item.get('author', ''),
                    published_at=updated,
                    external_id=item.get('id', ''),
                    metadata={
                        'likes': item.get('likes', 0),
                        'downloads': item.get('downloads', 0),
                        'tags': item.get('tags', []),
                        'pipeline_tag': item.get('pipeline_tag', ''),
                    },
                    source_name=f"Hugging Face {self.category.title()}"
                ))
            
            return items
            
        except Exception as e:
            self.logger.error(f"Failed to fetch from Hugging Face: {e}")
            return []


class HuggingFacePapersAggregator(BaseAggregator):
    """Fetches trending papers from Hugging Face."""
    
    def __init__(self):
        super().__init__("Hugging Face Papers", "huggingface", "https://huggingface.co/papers")
    
    def fetch(self, limit: int = 20) -> List[ContentItem]:
        """Fetch trending papers."""
        
        # Fetch from papers section
        url = "https://huggingface.co/api/papers"
        params = {'limit': limit}
        
        try:
            response = self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            items = []
            for paper in data:
                published = None
                if paper.get('published'):
                    try:
                        published = datetime.fromisoformat(paper['published'].replace('Z', '+00:00'))
                    except:
                        pass
                
                items.append(ContentItem(
                    title=paper.get('title', ''),
                    url=paper.get('paper_link', ''),
                    content=paper.get('abstract', ''),
                    author=paper.get('authors', ''),
                    published_at=published,
                    external_id=paper.get('id', ''),
                    metadata={
                        'likes': paper.get('likes', 0),
                        'citations': paper.get('citations', 0),
                    },
                    source_name="Hugging Face Papers"
                ))
            
            return items
            
        except Exception as e:
            self.logger.error(f"Failed to fetch papers: {e}")
            return []


class HuggingFaceSpacesAggregator(BaseAggregator):
    """Fetches trending spaces from Hugging Face."""
    
    def __init__(self, sort: str = "trending"):
        name = "Hugging Face Spaces"
        super().__init__(name, "huggingface", "https://huggingface.co/spaces")
        self.sort = sort
    
    def fetch(self, limit: int = 20) -> List[ContentItem]:
        """Fetch trending spaces."""
        url = "https://huggingface.co/api/spaces"
        params = {
            'sort': 'likes',
            'direction': -1,
            'limit': limit,
            'full': 'true'
        }
        
        try:
            response = self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            items = []
            for space in data:
                items.append(ContentItem(
                    title=f"Space: {space.get('id', '')}",
                    url=f"https://huggingface.co/spaces/{space.get('id', '')}",
                    content=space.get('emoji', '') + ' ' + (space.get('title', '')),
                    author=space.get('author', ''),
                    external_id=space.get('id', ''),
                    metadata={
                        'likes': space.get('likes', 0),
                        'sdk': space.get('sdk', ''),
                    },
                    source_name="Hugging Face Spaces"
                ))
            
            return items
            
        except Exception as e:
            self.logger.error(f"Failed to fetch spaces: {e}")
            return []