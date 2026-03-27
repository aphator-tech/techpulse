"""
YouTube API aggregator - fetches tech video RSS.
"""

from typing import List
from aggregators.base import BaseAggregator, ContentItem


class YouTubeTechAggregator(BaseAggregator):
    """Fetches tech videos from YouTube via RSS."""
    
    CHANNELS = [
        'https://www.youtube.com/feeds/videos.xml?channel_id=UCwX6rVkOq0IC4X1mS6wX0XQ',  # Fireship
        'https://www.youtube.com/feeds/videos.xml?channel_id=UCuXw5HJ1et5KP4-6LEfsihg',  # TechLead
        'https://www.youtube.com/feeds/videos.xml?channel_id=UC80PWE9NpiA_tC3C7L7F5fA',  # Code with Chris
    ]
    
    def __init__(self, channel_id: str = None):
        channel = channel_id or 'fireship'
        name = f"YouTube {channel}"
        super().__init__(name, "youtube", f"https://youtube.com/{channel}")
        self.channel_id = channel_id
        
    def fetch(self, limit: int = 10) -> List[ContentItem]:
        # YouTube RSS requires channel ID
        # For now, return empty - would need to fetch from web
        self.logger.info("YouTube aggregator - using RSS fallback")
        return []


class DailyTechVideosAggregator(BaseAggregator):
    """Aggregates tech news videos."""
    
    def __init__(self):
        name = "Tech Daily Videos"
        super().__init__(name, "youtube", "https://youtube.com")
        
    def fetch(self, limit: int = 10) -> List[ContentItem]:
        # Could scrape YouTube search results
        return []


AGGREGATORS = {'youtube_fireship': YouTubeTechAggregator}