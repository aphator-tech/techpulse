"""
Content generator - transforms raw content into polished blog posts.
"""

import logging
import random
from datetime import datetime
from typing import List, Dict, Optional
from .llm import LLMGenerator, get_template, GenerationResult


logger = logging.getLogger(__name__)


class ContentGenerator:
    """Generates high-quality blog posts from raw content."""
    
    CONTENT_TYPES = ['news', 'tutorial', 'tool_review', 'howto', 'deep_dive', 'quick_tips']
    
    # Keywords for content type classification
    CONTENT_TYPE_KEYWORDS = {
        'tutorial': ['tutorial', 'how to', 'guide', 'step by step', 'walkthrough', 'learn', 'build'],
        'tool_review': ['review', 'comparison', 'vs', 'best', 'alternative', 'tool', 'library', 'framework'],
        'howto': ['howto', 'how-to', 'tips', 'tricks', 'optimize', 'improve'],
        'deep_dive': ['analysis', 'deep dive', 'explained', 'understanding', 'internals', 'architecture'],
        'quick_tips': ['tip', 'trick', 'short', 'quick', 'fast'],
        'news': ['news', 'announce', 'release', 'update', 'launch', 'new'],
    }
    
    def __init__(self, provider: str = "openai"):
        """Initialize content generator.
        
        Args:
            provider: LLM provider to use
        """
        self.llm = LLMGenerator(provider)
        self.logger = logging.getLogger(__name__)
        
        # Track content type performance
        self.type_weights = {
            'news': 1.0,
            'tutorial': 1.0,
            'tool_review': 1.0,
            'howto': 1.0,
            'deep_dive': 1.0,
            'quick_tips': 1.0,
        }
    
    def classify_content_type(self, raw_content: Dict) -> str:
        """Classify content type based on title and metadata.
        
        Args:
            raw_content: Raw content dict
            
        Returns:
            Content type string
        """
        title = raw_content.get('title', '').lower()
        content = raw_content.get('content', '').lower()
        
        # Check source-specific patterns
        source = raw_content.get('source_name', '')
        
        if 'github' in source.lower() or 'huggingface' in source.lower():
            return 'tool_review'
        
        if 'hackaday' in source.lower():
            return 'tutorial'
        
        if 'producthunt' in source.lower():
            return 'tool_review'
        
        # Keyword-based classification
        scores = {}
        for content_type, keywords in self.CONTENT_TYPE_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in title or kw in content)
            scores[content_type] = score
        
        # Return highest scoring type, default to news
        if max(scores.values()) > 0:
            return max(scores, key=scores.get)
        
        return 'news'
    
    def generate_content(self, raw_content: Dict, 
                        content_type: str = None) -> GenerationResult:
        """Generate blog post from raw content.
        
        Args:
            raw_content: Raw content from aggregator
            content_type: Type of content (optional, auto-detected if not provided)
            
        Returns:
            GenerationResult with generated content
        """
        # Auto-detect content type if not provided
        if not content_type:
            content_type = self.classify_content_type(raw_content)
        
        # Get template
        template_fn = get_template(content_type)
        prompt = template_fn(raw_content)
        
        # Generate
        max_tokens = self._get_token_limit(content_type)
        generated = self.llm.generate(prompt, max_tokens=max_tokens)
        
        if not generated:
            return GenerationResult(
                success=False,
                content="",
                title=raw_content.get('title', 'Untitled'),
                summary="",
                error="LLM generation failed"
            )
        
        # Extract title and summary
        title = self._extract_title(generated, raw_content)
        summary = self._extract_summary(generated)
        
        return GenerationResult(
            success=True,
            content=generated,
            title=title,
            summary=summary
        )
    
    def generate_batch(self, raw_contents: List[Dict], 
                       content_types: List[str] = None) -> List[GenerationResult]:
        """Generate multiple content items.
        
        Args:
            raw_contents: List of raw content dicts
            content_types: Optional list of content types
            
        Returns:
            List of GenerationResults
        """
        results = []
        
        for i, raw in enumerate(raw_contents):
            content_type = content_types[i] if content_types and i < len(content_types) else None
            
            try:
                result = self.generate_content(raw, content_type)
                results.append(result)
                
                # Add small delay to avoid rate limits
                import time
                time.sleep(0.5)
                
            except Exception as e:
                self.logger.error(f"Failed to generate content: {e}")
                results.append(GenerationResult(
                    success=False,
                    content="",
                    title=raw.get('title', 'Untitled'),
                    summary="",
                    error=str(e)
                ))
        
        return results
    
    def _get_token_limit(self, content_type: str) -> int:
        """Get appropriate token limit for content type."""
        limits = {
            'quick_tips': 1000,
            'howto': 1500,
            'news': 1500,
            'tool_review': 2000,
            'tutorial': 2500,
            'deep_dive': 3000,
        }
        return limits.get(content_type, 1500)
    
    def _extract_title(self, generated: str, raw: Dict) -> str:
        """Extract title from generated content."""
        lines = generated.strip().split('\n')
        for line in lines[:3]:
            line = line.strip()
            if line and len(line) > 10 and not line.startswith('#'):
                # Clean up title
                return line[:200]
        return raw.get('title', 'Untitled')[:200]
    
    def _extract_summary(self, generated: str) -> str:
        """Extract summary from generated content."""
        # Use first paragraph as summary
        paragraphs = generated.split('\n\n')
        for p in paragraphs:
            p = p.strip()
            if p and len(p) > 50:
                return p[:300]
        return generated[:300]
    
    def update_type_weights(self, content_type: str, engagement: float):
        """Update content type weights based on engagement.
        
        Args:
            content_type: Type of content
            engagement: Engagement metric (views, etc.)
        """
        if content_type in self.type_weights:
            # Simple exponential moving average
            self.type_weights[content_type] = (
                0.7 * self.type_weights[content_type] + 
                0.3 * min(engagement / 100, 5.0)  # Cap at 5x
            )
            self.logger.info(f"Updated weight for {content_type}: {self.type_weights[content_type]:.2f}")
    
    def select_content_type(self) -> str:
        """Select content type based on weights.
        
        Returns:
            Selected content type
        """
        # Normalize weights
        total = sum(self.type_weights.values())
        weights = {k: v/total for k, v in self.type_weights.items()}
        
        # Weighted random selection
        r = random.random()
        cumulative = 0
        for ct, w in weights.items():
            cumulative += w
            if r <= cumulative:
                return ct
        
        return 'news'


# Singleton instance
_generator = None


def get_generator(provider: str = "openai") -> ContentGenerator:
    """Get content generator instance."""
    global _generator
    if _generator is None:
        _generator = ContentGenerator(provider)
    return _generator