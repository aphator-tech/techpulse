"""
Aggregator package for the tech content automation system.
Provides unified interface for fetching from multiple sources.
"""

from .base import BaseAggregator, ContentItem, RSSAggregator
from .reddit import RedditAggregator, RedditMultipleAggregator
from .github import GitHubTrendingAggregator, GitHubSearchAggregator, GitHubDeveloperAggregator
from .huggingface import HuggingFaceTrendingAggregator, HuggingFacePapersAggregator, HuggingFaceSpacesAggregator
from .hackernews import HackerNewsAggregator, HackerNewsNewAggregator, HackerNewsBestAggregator
from .devto import DevToAggregator, DevToLatestAggregator
from .hackaday import HackadayAggregator, HackadayBlogAggregator
from .producthunt import ProductHuntAggregator, ProductHuntTodayAggregator
from .stackoverflow import StackOverflowAggregator
from .medium import MediumAggregator


# Registry of all available aggregators
AGGREGATORS = {
    # Reddit
    'reddit_programming': lambda: RedditAggregator('programming'),
    'reddit_technology': lambda: RedditAggregator('technology'),
    'reddit_ai': lambda: RedditAggregator('artificial'),
    'reddit_machinelearning': lambda: RedditAggregator('MachineLearning'),
    'reddit_multi': lambda: RedditMultipleAggregator(),
    
    # GitHub
    'github_trending': lambda: GitHubTrendingAggregator(),
    'github_trending_python': lambda: GitHubTrendingAggregator('Python'),
    'github_trending_javascript': lambda: GitHubTrendingAggregator('JavaScript'),
    'github_search': lambda: GitHubSearchAggregator(),
    'github_developers': lambda: GitHubDeveloperAggregator(),
    
    # Hugging Face
    'huggingface_models': lambda: HuggingFaceTrendingAggregator('models'),
    'huggingface_papers': lambda: HuggingFacePapersAggregator(),
    'huggingface_spaces': lambda: HuggingFaceSpacesAggregator(),
    
    # Hacker News
    'hackernews_top': lambda: HackerNewsAggregator('topstories'),
    'hackernews_new': lambda: HackerNewsNewAggregator(),
    'hackernews_best': lambda: HackerNewsBestAggregator(),
    
    # Dev.to
    'devto_trending': lambda: DevToAggregator(),
    'devto_latest': lambda: DevToLatestAggregator(),
    
    # Hackaday
    'hackaday_projects': lambda: HackadayAggregator('projects'),
    'hackaday_blog': lambda: HackadayBlogAggregator(),
    
    # Product Hunt
    'producthunt_tech': lambda: ProductHuntAggregator('tech'),
    'producthunt_developer': lambda: ProductHuntAggregator('developer-tools'),
    'producthunt_today': lambda: ProductHuntTodayAggregator(),
    
    # Stack Overflow
    'stackoverflow': lambda: StackOverflowAggregator('python'),
    
    # Medium
    'medium': lambda: MediumAggregator('technology'),
}


def get_aggregator(name: str) -> BaseAggregator:
    """Get an aggregator by name.
    
    Args:
        name: Name of the aggregator
        
    Returns:
        Aggregator instance
        
    Raises:
        KeyError: If aggregator not found
    """
    if name not in AGGREGATORS:
        raise KeyError(f"Unknown aggregator: {name}. Available: {list(AGGREGATORS.keys())}")
    return AGGREGATORS[name]()


def get_all_aggregators() -> dict:
    """Get all available aggregators.
    
    Returns:
        Dict of aggregator name -> lambda
    """
    return AGREGATORS.copy()


def get_default_aggregators() -> list:
    """Get list of default aggregator names to use.
    
    Returns:
        List of aggregator names
    """
    return [
        'reddit_multi',
        'github_trending',
        'hackernews_top',
        'devto_trending',
        'huggingface_models',
        'hackaday_projects',
        'stackoverflow',
        'medium',
    ]