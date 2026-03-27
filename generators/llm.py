"""
LLM wrapper for AI content generation.
Supports multiple free LLM providers with fallback.
"""

import os
import logging
from typing import Optional, Dict, List
from dataclasses import dataclass
import httpx


logger = logging.getLogger(__name__)


@dataclass
class GenerationResult:
    """Result of content generation."""
    success: bool
    content: str
    title: str
    summary: str
    error: str = None


class FreeLLMProvider:
    """Base class for free LLM providers."""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key
        self.client = httpx.Client(timeout=60.0)
    
    def generate(self, prompt: str, max_tokens: int = 2000) -> Optional[str]:
        raise NotImplementedError
    
    def close(self):
        self.client.close()


class GroqProvider(FreeLLMProvider):
    """Groq - Free LLM API with fast inference."""
    
    BASE_URL = "https://api.groq.com/openai/v1"
    
    MODELS = ["llama-3.3-70b-versatile", "llama-3.1-70b-versatile", "mixtral-8x7b-32768"]
    
    def generate(self, prompt: str, max_tokens: int = 2000) -> Optional[str]:
        if not self.api_key:
            return None
        
        try:
            response = self.client.post(
                f"{self.BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.MODELS[0],
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": max_tokens,
                    "temperature": 0.7
                }
            )
            response.raise_for_status()
            data = response.json()
            return data['choices'][0]['message']['content']
        except Exception as e:
            logger.error(f"Groq generation failed: {e}")
            return None


class OpenRouterProvider(FreeLLMProvider):
    """OpenRouter - Aggregates multiple free LLM APIs."""
    
    BASE_URL = "https://openrouter.ai/api/v1"
    
    MODELS = ["meta-llama/llama-3.3-70b-instruct", "mistralai/mistral-7b-instruct", "google/gemini-2.0-flash-exp"]
    
    def generate(self, prompt: str, max_tokens: int = 2000) -> Optional[str]:
        if not self.api_key:
            return None
        
        try:
            response = self.client.post(
                f"{self.BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://techpulse.local",
                    "X-Title": "TechPulse"
                },
                json={
                    "model": self.MODELS[0],
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": max_tokens,
                    "temperature": 0.7
                }
            )
            response.raise_for_status()
            data = response.json()
            return data['choices'][0]['message']['content']
        except Exception as e:
            logger.error(f"OpenRouter generation failed: {e}")
            return None


class HuggingFaceProvider(FreeLLMProvider):
    """HuggingFace Inference API - Free tier available."""
    
    BASE_URL = "https://api-inference.huggingface.co"
    
    MODELS = ["meta-llama/Llama-3.3-70B-Instruct", "mistralai/Mistral-7B-Instruct-v0.2", "Qwen/Qwen2.5-72B-Instruct"]
    
    def generate(self, prompt: str, max_tokens: int = 2000) -> Optional[str]:
        if not self.api_key:
            return None
        
        try:
            response = self.client.post(
                f"{self.BASE_URL}/models/{self.MODELS[0]}",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "inputs": prompt,
                    "parameters": {
                        "max_new_tokens": max_tokens,
                        "temperature": 0.7,
                        "return_full_text": False
                    }
                }
            )
            response.raise_for_status()
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                return data[0].get('generated_text', '')
            return None
        except Exception as e:
            logger.error(f"HuggingFace generation failed: {e}")
            return None


class OpenAICompatProvider(FreeLLMProvider):
    """OpenAI-compatible free endpoint (like LiteLLM proxy)."""
    
    def __init__(self, api_key: str = None, base_url: str = None):
        super().__init__(api_key)
        self.base_url = base_url or os.environ.get('OPENAI_API_BASE', 'https://api.openai.com/v1')
        self.model = os.environ.get('OPENAI_MODEL', 'gpt-3.5-turbo')
    
    def generate(self, prompt: str, max_tokens: int = 2000) -> Optional[str]:
        if not self.api_key:
            return None
        
        try:
            response = self.client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": max_tokens,
                    "temperature": 0.7
                }
            )
            response.raise_for_status()
            data = response.json()
            return data['choices'][0]['message']['content']
        except Exception as e:
            logger.error(f"OpenAI-compatible generation failed: {e}")
            return None


class GeminiProvider(FreeLLMProvider):
    """Google Gemini API."""
    
    BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
    
    def __init__(self, api_key: str = None):
        super().__init__(api_key)
        self.model = "gemini-2.0-flash-exp"
    
    def generate(self, prompt: str, max_tokens: int = 2000) -> Optional[str]:
        if not self.api_key:
            return None
        
        try:
            response = self.client.post(
                f"{self.BASE_URL}/models/{self.model}:generateContent",
                params={"key": self.api_key},
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {
                        "maxOutputTokens": max_tokens,
                        "temperature": 0.7
                    }
                }
            )
            response.raise_for_status()
            data = response.json()
            if 'candidates' in data and len(data['candidates']) > 0:
                return data['candidates'][0]['content']['parts'][0]['text']
            return None
        except Exception as e:
            logger.error(f"Gemini generation failed: {e}")
            return None


# Try to load free keys from environment
def get_free_keys() -> Dict[str, str]:
    """Get all available free API keys."""
    return {
        'groq': os.environ.get('GROQ_API_KEY'),
        'openrouter': os.environ.get('OPENROUTER_API_KEY'),
        'huggingface': os.environ.get('HUGGINGFACE_API_KEY'),
        'gemini': os.environ.get('GEMINI_API_KEY'),
        'apifreellm': os.environ.get('APIFREELLM_API_KEY'),
    }


class FallbackLLMGenerator:
    """Multi-provider LLM with automatic fallback."""
    
    PROVIDERS = [
        ('groq', GroqProvider),
        ('openrouter', OpenRouterProvider),
        ('huggingface', HuggingFaceProvider),
        ('gemini', GeminiProvider),
    ]
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.providers = {}
        
        # Initialize all available providers
        keys = get_free_keys()
        for name, provider_class in self.PROVIDERS:
            api_key = keys.get(name)
            if api_key:
                self.providers[name] = provider_class(api_key)
                self.logger.info(f"Initialized {name} provider")
        
        if not self.providers:
            self.logger.warning("No free LLM providers available!")
    
    def generate(self, prompt: str, max_tokens: int = 2000) -> Optional[str]:
        """Try each provider in sequence until one works."""
        
        for name, provider in self.providers.items():
            try:
                self.logger.info(f"Trying {name} provider...")
                result = provider.generate(prompt, max_tokens)
                if result:
                    self.logger.info(f"Successfully generated with {name}")
                    return result
            except Exception as e:
                self.logger.warning(f"{name} failed: {e}")
                continue
        
        self.logger.error("All LLM providers failed")
        return None
    
    def close(self):
        for provider in self.providers.values():
            provider.close()


# Backward compatibility
class LLMGenerator:
    """Unified LLM interface - tries free providers first, then mock."""
    
    def __init__(self, provider: str = "fallback"):
        self.provider = provider
        self.logger = logging.getLogger(f"{__name__}.{provider}")
        
        # Try to use free providers
        self.free_llm = FallbackLLMGenerator()
        
        if not self.free_llm.providers:
            self.logger.warning("No free providers available - using mock")
    
    def generate(self, prompt: str, max_tokens: int = 2000, 
                 temperature: float = 0.7) -> Optional[str]:
        """Generate content - tries free LLM APIs first."""
        
        # Try free providers
        result = self.free_llm.generate(prompt, max_tokens)
        if result:
            return result
        
        # Return mock content if no providers available
        return self._generate_mock(prompt)
    
    def _generate_mock(self, prompt: str) -> str:
        """Generate mock content as fallback."""
        title = "Generated Article"
        if "Title:" in prompt:
            try:
                title_part = prompt.split("Title:")[1].split("\n")[0].strip()
                if title_part:
                    title = title_part
            except:
                pass
        
        return f"""# {title}

This article was automatically generated from trending tech content.

## Introduction

The tech industry is constantly evolving, with new developments and innovations emerging every day.

## Key Insights

Based on the trending content from various sources, here are the key highlights:

1. **Innovation continues**: New tools and frameworks are being released
2. **Community-driven growth**: Open source projects are seeing increased adoption
3. **Focus on productivity**: New tools help developers work more efficiently

## What This Means for Developers

Staying up-to-date with trends is crucial for developers.

## Conclusion

The tech landscape continues to evolve rapidly.

---
*This content was automatically generated.*
"""
    
    def generate_with_fallback(self, prompt: str, max_tokens: int = 2000) -> Optional[str]:
        """Generate with fallback - same as generate for free providers."""
        return self.generate(prompt, max_tokens)
    
    def close(self):
        if hasattr(self.free_llm, 'close'):
            self.free_llm.close()


class ContentTemplates:
    """Content templates for different content types."""
    
    @staticmethod
    def news_article(raw_content: Dict) -> str:
        return f"""Write a news article based on the following trending tech content:

Title: {raw_content.get('title', '')}
Source: {raw_content.get('source_name', '')}
URL: {raw_content.get('url', '')}

Content/Summary: {raw_content.get('content', '')[:1000] if raw_content.get('content') else 'No additional content available.'}

Requirements:
- Write in a professional news style
- Include context and background
- Make it engaging for tech enthusiasts
- Add relevant subheadings
- Keep it concise but informative (800-1200 words)
- Include the source URL at the end
"""

    @staticmethod
    def tutorial_walkthrough(raw_content: Dict) -> str:
        return f"""Create a detailed tutorial/walkthrough based on this content:

Title: {raw_content.get('title', '')}
Source: {raw_content.get('source_name', '')}
URL: {raw_content.get('url', '')}

Content: {raw_content.get('content', '')[:1500] if raw_content.get('content') else 'No content available.'}

Requirements:
- Write step-by-step instructions
- Include code examples where applicable
- Add prerequisites
- Explain concepts clearly for intermediate developers
- Include troubleshooting tips if relevant
- Make it practical and actionable (1500-2500 words)
- Add source attribution at the end
"""

    @staticmethod
    def tool_review(raw_content: Dict) -> str:
        return f"""Write a tool review/comparison based on this content:

Title: {raw_content.get('title', '')}
Source: {raw_content.get('source_name', '')}
URL: {raw_content.get('url', '')}

Details: {raw_content.get('content', '')[:1000] if raw_content.get('content') else 'No details available.'}

Requirements:
- Overview of the tool and its purpose
- Key features and capabilities
- Pros and cons
- Use cases and target audience
- Comparison with similar tools if applicable
- Conclusion with verdict (1000-1500 words)
"""

    @staticmethod
    def howto_guide(raw_content: Dict) -> str:
        return f"""Create a practical how-to guide:

Title: {raw_content.get('title', '')}
Source: {raw_content.get('source_name', '')}
URL: {raw_content.get('url', '')}

Content: {raw_content.get('content', '')[:1000] if raw_content.get('content') else 'No content available.'}

Requirements:
- Clear, action-oriented title
- Problem statement
- Step-by-step solution
- Include code snippets or commands
- Add tips and best practices
- Keep it focused and practical (800-1200 words)
"""

    @staticmethod
    def deep_dive(raw_content: Dict) -> str:
        return f"""Create an in-depth technical analysis:

Title: {raw_content.get('title', '')}
Source: {raw_content.get('source_name', '')}
URL: {raw_content.get('url', '')}

Content: {raw_content.get('content', '')[:2000] if raw_content.get('content') else 'No content available.'}

Requirements:
- Comprehensive technical exploration
- Historical context if relevant
- Technical details and architecture
- Real-world implications
- Future outlook
- Expert insights
- Detailed examples (2000-3000 words)
"""

    @staticmethod
    def quick_tips(raw_content: Dict) -> str:
        return f"""Create a quick tips article:

Title: {raw_content.get('title', '')}
Source: {raw_content.get('source_name', '')}
URL: {raw_content.get('url', '')}

Content: {raw_content.get('content', '')[:500] if raw_content.get('content') else 'No content available.'}

Requirements:
- Bite-sized, actionable tips
- Numbered list format
- Brief explanations for each tip
- Include examples where helpful
- Keep it scannable and concise (400-600 words)
"""


CONTENT_TYPE_TEMPLATES = {
    'news': ContentTemplates.news_article,
    'tutorial': ContentTemplates.tutorial_walkthrough,
    'tool_review': ContentTemplates.tool_review,
    'howto': ContentTemplates.howto_guide,
    'deep_dive': ContentTemplates.deep_dive,
    'quick_tips': ContentTemplates.quick_tips,
}


def get_template(content_type: str):
    return CONTENT_TYPE_TEMPLATES.get(content_type, ContentTemplates.news_article)