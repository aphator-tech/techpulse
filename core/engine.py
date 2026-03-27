"""
Core automation engine - orchestrates content fetching, generation, and deployment.
"""

import logging
import os
from datetime import datetime
from typing import List, Dict, Optional

# Import from local packages
import db
from aggregators import get_aggregator, get_default_aggregators
from generators import get_generator


logger = logging.getLogger(__name__)


class ContentEngine:
    """Main automation engine for content operations."""
    
    def __init__(self, db_path: str = "content_data/content.db"):
        """Initialize the content engine.
        
        Args:
            db_path: Path to SQLite database
        """
        self.db = db.Database(db_path)
        self.logger = logging.getLogger(__name__)
        
        # Ensure sources are in database
        self._init_sources()
    
    def _init_sources(self):
        """Initialize default sources in database."""
        default_sources = [
            ('Reddit Multi', 'reddit', 'https://reddit.com', 'REDDIT_API_KEY', 30),
            ('GitHub Trending', 'github', 'https://github.com/trending', 'GITHUB_TOKEN', 60),
            ('Hugging Face Models', 'huggingface', 'https://huggingface.co/models', 'HUGGING_FACE_API_KEY', 120),
            ('Hacker News Top', 'hackernews', 'https://news.ycombinator.com', None, 15),
            ('Dev.to', 'devto', 'https://dev.to', 'DEVTO_API_KEY', 30),
            ('Hackaday', 'hackaday', 'https://hackaday.com', None, 60),
            ('Product Hunt', 'producthunt', 'https://producthunt.com', 'PRODUCT_HUNT_API_KEY', 60),
        ]
        
        for name, stype, url, api_key, interval in default_sources:
            existing = self.db.get_source_by_name(name)
            if not existing:
                self.db.add_source(name, stype, url, api_key, interval)
                self.logger.info(f"Added source: {name}")
    
    def fetch_from_source(self, source_name: str, limit: int = 20) -> int:
        """Fetch content from a specific source.
        
        Args:
            source_name: Name of the aggregator
            limit: Max items to fetch
            
        Returns:
            Number of items fetched
        """
        try:
            aggregator = get_aggregator(source_name)
            items = aggregator.fetch(limit)
            aggregator.close()
            
            # Get source ID from database
            source_info = self._get_source_info(source_name)
            if not source_info:
                self.logger.error(f"Source not found: {source_name}")
                return 0
            
            source_id = source_info['id']
            fetched = 0
            
            for item in items:
                # Check for duplicates
                if self.db.check_content_exists(item.url):
                    continue
                
                # Store in database
                self.db.add_raw_content(
                    source_id=source_id,
                    title=item.title,
                    url=item.url,
                    content_text=item.content,
                    author=item.author,
                    published_at=item.published_at.isoformat() if item.published_at else None,
                    metadata=item.metadata,
                    external_id=item.external_id
                )
                fetched += 1
            
            self.db.update_source_stats(source_id, success=True)
            self.logger.info(f"Fetched {fetched} items from {source_name}")
            return fetched
            
        except Exception as e:
            self.logger.error(f"Failed to fetch from {source_name}: {e}")
            return 0
    
    def fetch_from_all_sources(self, limit: int = 10) -> Dict[str, int]:
        """Fetch from all enabled sources.
        
        Args:
            limit: Items per source
            
        Returns:
            Dict of source_name -> count
        """
        results = {}
        aggregators = get_default_aggregators()
        
        for agg_name in aggregators:
            try:
                count = self.fetch_from_source(agg_name, limit)
                results[agg_name] = count
            except Exception as e:
                self.logger.error(f"Failed {agg_name}: {e}")
                results[agg_name] = 0
        
        return results
    
    def _get_source_info(self, source_name: str) -> Optional[Dict]:
        """Get source info from aggregator name."""
        # Map aggregator names to source names
        name_map = {
            'reddit_multi': 'Reddit Multi',
            'github_trending': 'GitHub Trending',
            'huggingface_models': 'Hugging Face Models',
            'hackernews_top': 'Hacker News Top',
            'devto_trending': 'Dev.to',
            'hackaday_projects': 'Hackaday',
            'producthunt_tech': 'Product Hunt',
        }
        
        db_name = name_map.get(source_name, source_name)
        sources = self.db.get_enabled_sources()
        
        for s in sources:
            if s['name'] == db_name:
                return s
        return None
    
    def process_unprocessed(self, max_items: int = 5) -> int:
        """Process unprocessed content into blog posts.
        
        Args:
            max_items: Max items to process
            
        Returns:
            Number of items processed
        """
        generator = get_generator()
        
        raw_items = self.db.get_unprocessed_content(limit=max_items)
        processed = 0
        
        for raw in raw_items:
            try:
                # Generate content
                result = generator.generate_content(raw)
                
                if result.success:
                    # Store generated content
                    tags = self._extract_tags(raw, result.content)
                    
                    self.db.add_generated_content(
                        raw_content_id=raw['id'],
                        source_id=raw['source_id'],
                        title=result.title,
                        content=result.content,
                        content_type='news',  # Could be auto-detected
                        summary=result.summary,
                        tags=','.join(tags),
                        word_count=len(result.content.split())
                    )
                    
                    # Mark as processed
                    self.db.mark_content_processed(raw['id'])
                    processed += 1
                    
                    self.logger.info(f"Generated: {result.title}")
                else:
                    self.logger.warning(f"Failed to generate: {result.error}")
                    
            except Exception as e:
                self.logger.error(f"Error processing {raw['id']}: {e}")
        
        return processed
    
    def _extract_tags(self, raw: Dict, content: str) -> List[str]:
        """Extract tags from content."""
        tags = []
        
        # From metadata
        if raw.get('metadata'):
            meta = raw['metadata']
            if isinstance(meta, dict):
                if meta.get('tags'):
                    tags.extend(meta['tags'][:3])
                if meta.get('language'):
                    tags.append(meta['language'])
        
        # From source
        source = raw.get('source_name', '')
        if source:
            tags.append(source.split()[0].lower())
        
        return list(set(tags))[:5]
    
    def get_latest_published(self, limit: int = 10) -> List[Dict]:
        """Get latest published content."""
        return self.db.get_published_content(limit=limit)
    
    def get_stats(self) -> Dict:
        """Get system statistics."""
        sources = self.db.get_enabled_sources()
        raw_content = self.db.get_unprocessed_content(limit=1000)
        generated = self.db.get_latest_generated_content(limit=100)
        published = self.db.get_published_content(limit=100)
        type_stats = self.db.get_content_type_stats()
        
        return {
            'sources': len(sources),
            'raw_pending': len(raw_content),
            'generated_count': len(generated),
            'published_count': len(published),
            'type_stats': type_stats,
        }


# Global engine instance
_engine: Optional[ContentEngine] = None


def get_engine(db_path: str = None) -> ContentEngine:
    """Get the global engine instance."""
    global _engine
    if _engine is None:
        _engine = ContentEngine(db_path or "content_data/content.db")
    return _engine