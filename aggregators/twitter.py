"""
Twitter/X aggregator - fetches trending tech tweets.
"""

from datetime import datetime
from typing import List
import os
from aggregators.base import BaseAggregator, ContentItem


class TwitterAggregator(BaseAggregator):
    """Fetches trending tech content from Twitter/X."""
    
    def __init__(self, api_key: str = None):
        name = "Twitter Tech Trends"
        super().__init__(name, "twitter", "https://twitter.com")
        self.api_key = api_key or os.environ.get('TWITTER_API_KEY')
        
    def fetch(self, limit: int = 10) -> List[ContentItem]:
        """Fetch trending tech tweets."""
        # Note: Twitter API requires authentication
        # For demo, return empty list
        self.logger.info("Twitter aggregator needs API key for full functionality")
        return []


class TwitterHashtagAggregator(BaseAggregator):
    """Fetches tech tweets by hashtag."""
    
    HASHTAGS = ['python', 'javascript', 'webdev', 'ai', 'machinelearning', 'coding', 'programming']
    
    def __init__(self, hashtag: str = 'tech'):
        name = f"Twitter #{hashtag}"
        super().__init__(name, "twitter", f"https://twitter.com/hashtag/{hashtag}")
        self.hashtag = hashtag
        self.api_key = os.environ.get('TWITTER_API_KEY')
        
    def fetch(self, limit: int = 10) -> List[ContentItem]:
        """Fetch tweets by hashtag."""
        self.logger.info(f"Twitter hashtag #{self.hashtag} - needs API key")
        return []


# Register aggregators
AGGREGATORS = {
    'twitter_trending': TwitterAggregator,
    'twitter_hashtag': TwitterHashtagAggregator,
}