"""
Hacker News aggregator - fetches top stories from Hacker News.
"""

from datetime import datetime
from typing import List
from aggregators.base import BaseAggregator, ContentItem


class HackerNewsAggregator(BaseAggregator):
    """Fetches top stories from Hacker News."""
    
    def __init__(self, story_type: str = "topstories"):
        """Initialize HN aggregator.
        
        Args:
            story_type: 'topstories', 'newstories', 'beststories'
        """
        name = f"Hacker News {story_type.title()}"
        super().__init__(name, "hackernews", "https://hacker-news.firebaseio.com/v0")
        self.story_type = story_type
    
    def fetch(self, limit: int = 20) -> List[ContentItem]:
        """Fetch stories from Hacker News."""
        
        # First get story IDs
        ids_url = f"{self.base_url}/{self.story_type}.json"
        ids_data = self.fetch_json(ids_url)
        
        if not ids_data:
            return []
        
        story_ids = ids_data[:limit]
        items = []
        
        # Fetch individual stories
        for story_id in story_ids:
            story_url = f"{self.base_url}/item/{story_id}.json"
            story = self.fetch_json(story_url)
            
            if not story:
                continue
            
            # Parse time
            published = None
            if story.get('time'):
                published = datetime.fromtimestamp(story['time'])
            
            items.append(ContentItem(
                title=story.get('title', ''),
                url=story.get('url', f"https://news.ycombinator.com/item?id={story_id}"),
                content=story.get('text', ''),
                author=story.get('by', ''),
                published_at=published,
                external_id=str(story_id),
                metadata={
                    'score': story.get('score', 0),
                    'descendants': story.get('descendants', 0),
                    'type': story.get('type', ''),
                },
                source_name="Hacker News"
            ))
        
        return items


class HackerNewsNewAggregator(BaseAggregator):
    """Fetches newest stories from Hacker News."""
    
    def __init__(self):
        super().__init__("Hacker News New", "hackernews", "https://hacker-news.firebaseio.com/v0")
    
    def fetch(self, limit: int = 20) -> List[ContentItem]:
        """Fetch newest stories."""
        return HackerNewsAggregator("newstories").fetch(limit)


class HackerNewsBestAggregator(BaseAggregator):
    """Fetches best stories from Hacker News."""
    
    def __init__(self):
        super().__init__("Hacker News Best", "hackernews", "https://hacker-news.firebaseio.com/v0")
    
    def fetch(self, limit: int = 20) -> List[ContentItem]:
        """Fetch best stories."""
        return HackerNewsAggregator("beststories").fetch(limit)