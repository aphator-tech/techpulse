"""
GitHub aggregator - fetches trending repositories.
"""

from datetime import datetime
from typing import List
import os
from aggregators.base import BaseAggregator, ContentItem


class GitHubTrendingAggregator(BaseAggregator):
    """Fetches trending repositories from GitHub."""
    
    LANGUAGES = ['Python', 'JavaScript', 'TypeScript', 'Go', 'Rust', 'Java']
    
    def __init__(self, language: str = None, time_range: str = 'daily'):
        """Initialize GitHub trending aggregator.
        
        Args:
            language: Programming language filter (optional)
            time_range: 'daily' or 'weekly'
        """
        lang_part = f"?language={language}" if language else ""
        name = f"GitHub Trending {language or 'All'}"
        super().__init__(name, "github", f"https://github.com/trending{lang_part}")
        self.language = language
        self.time_range = time_range
    
    def fetch(self, limit: int = 20) -> List[ContentItem]:
        """Fetch trending repositories."""
        url = f"https://github.com/trending/{self.time_range}"
        if self.language:
            url += f"?spoken_language_code="
        
        soup = self.fetch_html(url)
        if not soup:
            return []
        
        items = []
        
        # Parse repository cards
        for article in soup.select('article.box-row')[:limit]:
            try:
                title_elem = article.select_one('h2 a')
                if not title_elem:
                    continue
                    
                repo_path = title_elem.get('href', '').strip('/')
                title = f"{repo_path} - {title_elem.get_text(strip=True)}"
                url = f"https://github.com/{repo_path}"
                
                # Description
                desc_elem = article.select_one('p')
                description = desc_elem.get_text(strip=True) if desc_elem else ""
                
                # Stars and forks
                stars = 0
                forks = 0
                for span in article.select('span.d-inline-block'):
                    text = span.get_text(strip=True)
                    if 'stars' in text.lower():
                        stars = self._parse_number(text)
                    elif 'forks' in text.lower():
                        forks = self._parse_number(text)
                
                # Language
                lang_elem = article.select_one('span.language-text')
                language = lang_elem.get_text(strip=True) if lang_elem else ""
                
                items.append(ContentItem(
                    title=title,
                    url=url,
                    content=description,
                    metadata={
                        'stars': stars,
                        'forks': forks,
                        'language': language,
                        'time_range': self.time_range
                    },
                    source_name="GitHub Trending"
                ))
                
            except Exception as e:
                self.logger.warning(f"Failed to parse repo: {e}")
                continue
        
        return items
    
    def _parse_number(self, text: str) -> int:
        """Parse star/fork count."""
        text = text.strip().lower().replace(',', '')
        multipliers = {'k': 1000, 'm': 1000000}
        for k, v in multipliers.items():
            if k in text:
                return int(float(text.replace(k, '')) * v)
        try:
            return int(text)
        except:
            return 0


class GitHubSearchAggregator(BaseAggregator):
    """Fetches repositories based on search query."""
    
    def __init__(self, query: str = "stars:>1000 created:>2023-01-01", 
                 sort: str = "stars", api_key: str = None):
        name = f"GitHub Search: {query}"
        super().__init__(name, "github", "https://api.github.com/search/repositories")
        self.query = query
        self.sort = sort
        self.api_key = api_key or os.environ.get('GITHUB_TOKEN')
        
        if self.api_key:
            self.client.headers['Authorization'] = f'token {self.api_key}'
    
    def fetch(self, limit: int = 20) -> List[ContentItem]:
        """Search GitHub repositories."""
        url = f"https://api.github.com/search/repositories"
        params = {
            'q': self.query,
            'sort': self.sort,
            'order': 'desc',
            'per_page': min(limit, 100)
        }
        
        try:
            response = self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            items = []
            for repo in data.get('items', []):
                items.append(ContentItem(
                    title=f"{repo['full_name']} - ⭐ {repo['stargazers_count']}",
                    url=repo['html_url'],
                    content=repo.get('description', ''),
                    author=repo['owner']['login'],
                    published_at=datetime.fromisoformat(repo['created_at'].replace('Z', '+00:00')),
                    external_id=str(repo['id']),
                    metadata={
                        'stars': repo['stargazers_count'],
                        'forks': repo['forks_count'],
                        'language': repo.get('language', ''),
                        'topics': repo.get('topics', []),
                    },
                    source_name="GitHub Search"
                ))
            
            return items
            
        except Exception as e:
            self.logger.error(f"Failed to search GitHub: {e}")
            return []


class GitHubDeveloperAggregator(BaseAggregator):
    """Fetches trending developers from GitHub."""
    
    def __init__(self, language: str = None):
        name = f"GitHub Developers {language or ''}"
        super().__init__(name, "github", "https://github.com/trending/developers")
        self.language = language
    
    def fetch(self, limit: int = 20) -> List[ContentItem]:
        """Fetch trending developers."""
        url = "https://github.com/trending/developers"
        if self.language:
            url += f"?spoken_language_code="
        
        soup = self.fetch_html(url)
        if not soup:
            return []
        
        items = []
        
        for article in soup.select('article')[:limit]:
            try:
                link = article.select_one('h2 a')
                if not link:
                    continue
                    
                username = link.get('href', '').strip('/')
                name = link.get_text(strip=True)
                
                items.append(ContentItem(
                    title=f"Developer: {name} (@{username})",
                    url=f"https://github.com/{username}",
                    content=f"Trending GitHub developer: {name}",
                    author=username,
                    metadata={'username': username},
                    source_name="GitHub Developers"
                ))
                
            except Exception as e:
                self.logger.warning(f"Failed to parse developer: {e}")
                continue
        
        return items