"""
Product Hunt aggregator - fetches trending products from Product Hunt.
"""

from datetime import datetime
from typing import List
import os
from aggregators.base import BaseAggregator, ContentItem


class ProductHuntAggregator(BaseAggregator):
    """Fetches trending products from Product Hunt."""
    
    CATEGORIES = ['tech', 'games', 'books', 'podcasts', 'developer-tools']
    
    def __init__(self, category: str = 'tech'):
        name = f"Product Hunt {category.title()}"
        super().__init__(name, "producthunt", "https://api.producthunt.com/v2")
        self.category = category
        self.api_key = os.environ.get('PRODUCT_HUNT_API_KEY')
    
    def fetch(self, limit: int = 20) -> List[ContentItem]:
        """Fetch trending products."""
        
        if not self.api_key:
            return self._fetch_html(limit)
        
        # Use API
        return self._fetch_api(limit)
    
    def _fetch_api(self, limit: int = 20) -> List[ContentItem]:
        """Fetch using Product Hunt API."""
        url = f"{self.base_url}/graphql"
        
        query = """
        query {
            category(slug: "%s) {
                posts(first: %d) {
                    edges {
                        node {
                            name
                            tagline
                            url
                            votesCount
                            commentsCount
                            publishedAt
                        }
                    }
                }
            }
        }
        """ % (self.category, limit)
        
        try:
            response = self.client.post(
                url,
                json={'query': query},
                headers={
                    'Authorization': f'Bearer {self.api_key}',
                    'Content-Type': 'application/json'
                }
            )
            response.raise_for_status()
            data = response.json()
            
            items = []
            for edge in data.get('data', {}).get('category', {}).get('posts', {}).get('edges', []):
                node = edge.get('node', {})
                published = None
                if node.get('publishedAt'):
                    try:
                        published = datetime.fromisoformat(node['publishedAt'].replace('Z', '+00:00'))
                    except:
                        pass
                
                items.append(ContentItem(
                    title=node.get('name', ''),
                    url=node.get('url', ''),
                    content=node.get('tagline', ''),
                    published_at=published,
                    external_id=node.get('id', ''),
                    metadata={
                        'votes': node.get('votesCount', 0),
                        'comments': node.get('commentsCount', 0),
                        'category': self.category,
                    },
                    source_name=f"Product Hunt {self.category.title()}"
                ))
            
            return items
            
        except Exception as e:
            self.logger.error(f"Failed to fetch from Product Hunt API: {e}")
            return []
    
    def _fetch_html(self, limit: int = 20) -> List[ContentItem]:
        """Fallback: scrape from HTML."""
        url = f"https://www.producthunt.com/categories/{self.category}"
        
        soup = self.fetch_html(url)
        if not soup:
            return []
        
        items = []
        
        # Parse product cards
        for card in soup.select('div[data-test="product-card"]')[:limit]:
            try:
                title_elem = card.select_one('a[href*="/products/"]')
                if not title_elem:
                    continue
                    
                title = title_elem.get_text(strip=True)
                url = f"https://www.producthunt.com{title_elem.get('href', '')}"
                
                tagline = ''
                tagline_elem = card.select_one('p')
                if tagline_elem:
                    tagline = tagline_elem.get_text(strip=True)
                
                items.append(ContentItem(
                    title=title,
                    url=url,
                    content=tagline,
                    metadata={'category': self.category},
                    source_name=f"Product Hunt {self.category.title()}"
                ))
                
            except Exception as e:
                self.logger.warning(f"Failed to parse product card: {e}")
                continue
        
        return items


class ProductHuntTodayAggregator(BaseAggregator):
    """Fetches today's top products from Product Hunt."""
    
    def __init__(self):
        super().__init__("Product Hunt Today", "producthunt", "https://www.producthunt.com")
    
    def fetch(self, limit: int = 20) -> List[ContentItem]:
        """Fetch today's top products."""
        url = "https://www.producthunt.com"
        
        soup = self.fetch_html(url)
        if not soup:
            return []
        
        items = []
        
        for card in soup.select('a[href*="/products/"]')[:limit]:
            try:
                title = card.get_text(strip=True)
                href = card.get('href', '')
                
                if not title or not href:
                    continue
                
                items.append(ContentItem(
                    title=title,
                    url=f"https://www.producthunt.com{href}",
                    source_name="Product Hunt Today"
                ))
                
            except Exception as e:
                self.logger.warning(f"Failed to parse product: {e}")
                continue
        
        return items