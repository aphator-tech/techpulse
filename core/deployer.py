"""
Auto-deployment pipeline for pushing content to GitHub.
"""

import os
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, List
import git
from slugify import slugify


logger = logging.getLogger(__name__)


class ContentDeployer:
    """Handles deployment of generated content to GitHub."""
    
    def __init__(self, repo_path: str = "content_data/output", 
                 repo_url: str = None):
        """Initialize the deployer.
        
        Args:
            repo_path: Local path to the git repository
            repo_url: Git remote URL (for cloning)
        """
        self.repo_path = Path(repo_path)
        self.repo_url = repo_url or os.environ.get('GITHUB_REPO_URL')
        self.repo: Optional[git.Repo] = None
        
    def init_or_clone(self):
        """Initialize or clone the repository."""
        self.repo_path.mkdir(parents=True, exist_ok=True)
        
        try:
            if (self.repo_path / '.git').exists():
                self.repo = git.Repo(self.repo_path)
                self.logger.info(f"Opened existing repo at {self.repo_path}")
            elif self.repo_url:
                self.repo = git.Repo.clone_from(
                    self.repo_url,
                    self.repo_path,
                    depth=1
                )
                self.logger.info(f"Cloned repo from {self.repo_url}")
            else:
                self.repo = git.Repo.init(self.repo_path)
                self.logger.info(f"Initialized new repo at {self.repo_path}")
        except Exception as e:
            self.logger.error(f"Failed to init/clone repo: {e}")
            # Create fresh repo
            self.repo = git.Repo.init(self.repo_path)
    
    @property
    def logger(self):
        return logging.getLogger(__name__)
    
    def content_to_html(self, title: str, content: str, 
                        summary: str = None, tags: List[str] = None,
                        date: str = None) -> str:
        """Convert markdown-like content to HTML.
        
        Args:
            title: Article title
            content: Article content (markdown)
            summary: Article summary
            tags: List of tags
            date: Publication date
            
        Returns:
            HTML string
        """
        from bs4 import BeautifulSoup
        
        # Simple markdown to HTML conversion
        html_content = content
        
        # Convert headers
        for i in range(6, 0, -1):
            prefix = '#' * i
            html_content = html_content.replace(
                f'{prefix} ', 
                f'<h{i}>'
            ).replace(
                f'\n{prefix} ', 
                f'</h{i}>\n<h{i}>'
            )
        
        # Convert bold/italic
        html_content = html_content.replace('**', '<strong>')
        html_content = html_content.replace('*', '<em>')
        
        # Convert code blocks
        lines = html_content.split('\n')
        new_lines = []
        in_code = False
        
        for line in lines:
            if line.strip().startswith('```'):
                in_code = not in_code
                if in_code:
                    new_lines.append('<pre><code>')
                else:
                    new_lines.append('</code></pre>')
            else:
                if in_code:
                    new_lines.append(line)
                else:
                    # Convert inline code
                    line = line.replace('`', '<code>').replace('`', '</code>', 1)
                    new_lines.append(f'<p>{line}</p>')
        
        html_content = '\n'.join(new_lines)
        
        # Convert line breaks
        html_content = html_content.replace('\n\n', '</p><p>')
        html_content = html_content.replace('\n', '<br>')
        
        # Clean up
        html_content = html_content.replace('<p></p>', '')
        html_content = html_content.replace('<p><pre>', '<pre>')
        html_content = html_content.replace('</code></pre>', '</code></pre>')
        html_content = html_content.replace('</pre></p>', '</pre>')
        
        date_str = date or datetime.now().strftime('%Y-%m-%d')
        
        # Build full HTML
        tags_html = ''
        if tags:
            tags_html = '<div class="tags">' + ''.join(
                f'<span class="tag">{tag}</span>' for tag in tags
            ) + '</div>'
        
        full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 20px; }}
        h1 {{ color: #333; }}
        .meta {{ color: #666; font-size: 0.9em; }}
        .content {{ margin-top: 20px; }}
        .tags {{ margin-top: 20px; }}
        .tag {{ background: #f0f0f0; padding: 2px 8px; border-radius: 3px; margin-right: 5px; font-size: 0.8em; }}
        code {{ background: #f5f5f5; padding: 2px 5px; border-radius: 3px; }}
        pre {{ background: #f5f5f5; padding: 15px; border-radius: 5px; overflow-x: auto; }}
    </style>
</head>
<body>
    <article>
        <h1>{title}</h1>
        <div class="meta">Published: {date_str}</div>
        {tags_html}
        <div class="content">
            {html_content}
        </div>
    </article>
</body>
</html>"""
        
        return full_html
    
    def deploy_content(self, title: str, content: str,
                       content_type: str = 'news',
                       summary: str = None, 
                       tags: List[str] = None) -> bool:
        """Deploy content to the repository.
        
        Args:
            title: Content title
            content: Content body
            content_type: Type of content
            summary: Optional summary
            tags: Optional tags
            
        Returns:
            True if successful
        """
        if not self.repo:
            self.init_or_clone()
        
        # Create slug for filename
        slug = slugify(title)[:100]
        date_str = datetime.now().strftime('%Y-%m-%d')
        filename = f"{date_str}-{slug}.html"
        
        # Convert to HTML
        html_content = self.content_to_html(title, content, summary, tags, date_str)
        
        # Write to file
        filepath = self.repo_path / filename
        filepath.write_text(html_content, encoding='utf-8')
        
        self.logger.info(f"Wrote content to {filepath}")
        
        # Commit and push
        return self.commit_and_push(f"Add: {title}")
    
    def commit_and_push(self, message: str) -> bool:
        """Commit and push changes to remote.
        
        Args:
            message: Commit message
            
        Returns:
            True if successful
        """
        try:
            # Stage all changes
            self.repo.git.add(A=True)
            
            # Check if there are changes
            if not self.repo.git.diff('--cached'):
                self.logger.info("No changes to commit")
                return True
            
            # Commit
            self.repo.index.commit(message)
            self.logger.info(f"Committed: {message}")
            
            # Push if remote is configured
            if self.repo.remotes:
                origin = self.repo.remotes.origin
                origin.push()
                self.logger.info("Pushed to remote")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to commit/push: {e}")
            return False
    
    def get_published_files(self) -> List[str]:
        """Get list of published content files."""
        if not self.repo_path.exists():
            return []
        
        html_files = list(self.repo_path.glob('*.html'))
        return [f.stem for f in html_files]


def slugify(text: str) -> str:
    """Convert text to URL-friendly slug."""
    import re
    # Remove special characters
    text = re.sub(r'[^\w\s-]', '', text.lower())
    # Replace spaces with hyphens
    text = re.sub(r'[-\s]+', '-', text)
    return text.strip('-')


# Global deployer instance
_deployer: Optional[ContentDeployer] = None


def get_deployer(repo_path: str = None) -> ContentDeployer:
    """Get the global deployer instance."""
    global _deployer
    if _deployer is None:
        _deployer = ContentDeployer(repo_path or "content_data/output")
    return _deployer