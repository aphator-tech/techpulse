"""
Reddit aggregator - fetches trending posts from Reddit.
"""

from datetime import datetime
from typing import List
import os
from aggregators.base import BaseAggregator, ContentItem


class RedditAggregator(BaseAggregator):
    """Fetches trending content from Reddit subreddits."""
    
    SUBREDDITS = [
        'programming', 'technology', 'artificial', 'MachineLearning',
        'developers', 'Startups', 'gadgets', 'sysadmin', 'coding',
        'webdev', 'python', 'javascript', 'LearnProgramming'
    ]
    
    def __init__(self, subreddit: str = 'programming', api_key: str = None):
        name = f"Reddit r/{subreddit}"
        super().__init__(name, "reddit", f"https://www.reddit.com/r/{subreddit}")
        self.subreddit = subreddit
        self.api_key = api_key or os.environ.get('REDDIT_API_KEY')
        
        # Update headers for Reddit
        self.client.headers['User-Agent'] = 'TechContentBot/1.0'
        if self.api_key:
            self.client.headers['Authorization'] = f'Bearer {self.api_key}'
    
    def fetch(self, limit: int = 20) -> List[ContentItem]:
        """Fetch hot posts from subreddit."""
        
        # Use Reddit's JSON API
        url = f"https://www.reddit.com/r/{self.subreddit}/hot.json?limit={limit}"
        
        try:
            response = self.client.get(url)
            response.raise_for_status()
            data = response.json()
            
            items = []
            for post in data['data']['children']:
                post_data = post['data']
                
                # Parse published time
                published = datetime.fromtimestamp(post_data['created_utc'])
                
                items.append(ContentItem(
                    title=post_data.get('title', ''),
                    url=f"https://reddit.com{post_data.get('permalink', '')}",
                    content=post_data.get('selftext', ''),
                    author=post_data.get('author', ''),
                    published_at=published,
                    external_id=post_data.get('name', ''),
                    metadata={
                        'score': post_data.get('score', 0),
                        'num_comments': post_data.get('num_comments', 0),
                        'subreddit': self.subreddit,
                        'is_self': post_data.get('is_self', False),
                        'url_overridden': post_data.get('url_overridden', False)
                    },
                    source_name=f"r/{self.subreddit}"
                ))
            
            return items
            
        except Exception as e:
            self.logger.error(f"Failed to fetch from Reddit r/{self.subreddit}: {e}")
            return []


class RedditMultipleAggregator(BaseAggregator):
    """Fetches from multiple Reddit subreddits."""
    
    def __init__(self, subreddits: List[str] = None, api_key: str = None):
        name = "Reddit Multi-Subreddit"
        super().__init__(name, "reddit", "https://www.reddit.com")
        self.subreddits = subreddits or RedditAggregator.SUBREDDITS
        self.api_key = api_key
    
    def fetch(self, limit: int = 20) -> List[ContentItem]:
        """Fetch from multiple subreddits."""
        all_items = []
        
        # Fetch from each subreddit
        for subreddit in self.subreddits[:5]:  # Limit to 5 to avoid rate limits
            agg = RedditAggregator(subreddit, self.api_key)
            try:
                items = agg.fetch(limit=limit // 5)
                all_items.extend(items)
            except Exception as e:
                self.logger.warning(f"Failed to fetch r/{subreddit}: {e}")
            finally:
                agg.close()
        
        # Sort by engagement (score + comments)
        all_items.sort(
            key=lambda x: (x.metadata.get('score', 0) + x.metadata.get('num_comments', 0)),
            reverse=True
        )
        
        return all_items[:limit]