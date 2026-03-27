"""
Database module for the tech content automation system.
Provides SQLite-based storage for raw content, generated content, and metadata.
"""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
import json


class Database:
    """SQLite database manager for content automation."""
    
    def __init__(self, db_path: str = "content_data/content.db"):
        """Initialize database connection.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection with row factory."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _init_schema(self):
        """Initialize database schema."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Sources table - tracks content sources and performance
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                source_type TEXT NOT NULL,
                base_url TEXT,
                api_key_env TEXT,
                enabled BOOLEAN DEFAULT 1,
                fetch_interval_minutes INTEGER DEFAULT 60,
                weight REAL DEFAULT 1.0,
                total_fetched INTEGER DEFAULT 0,
                successful_fetches INTEGER DEFAULT 0,
                last_fetched_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Raw content table - stores fetched content before processing
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS raw_content (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_id INTEGER NOT NULL,
                external_id TEXT,
                title TEXT NOT NULL,
                url TEXT NOT NULL,
                content_text TEXT,
                author TEXT,
                published_at TIMESTAMP,
                fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                raw_metadata TEXT,
                engagement_score REAL DEFAULT 0,
                is_processed BOOLEAN DEFAULT 0,
                FOREIGN KEY (source_id) REFERENCES sources(id)
            )
        """)
        
        # Generated content table - AI-generated blog posts
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS generated_content (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                raw_content_id INTEGER,
                source_id INTEGER,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                content_type TEXT NOT NULL,
                summary TEXT,
                tags TEXT,
                word_count INTEGER,
                quality_score REAL DEFAULT 0,
                generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (raw_content_id) REFERENCES raw_content(id),
                FOREIGN KEY (source_id) REFERENCES sources(id)
            )
        """)
        
        # Published content table - deployed posts
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS published_content (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                generated_content_id INTEGER NOT NULL,
                slug TEXT UNIQUE NOT NULL,
                published_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                deployment_status TEXT DEFAULT 'pending',
                deployment_log TEXT,
                views INTEGER DEFAULT 0,
                FOREIGN KEY (generated_content_id) REFERENCES generated_content(id)
            )
        """)
        
        # Content type performance table - for self-learning
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS content_type_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content_type TEXT NOT NULL,
                total_published INTEGER DEFAULT 0,
                total_views INTEGER DEFAULT 0,
                avg_engagement REAL DEFAULT 0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes for performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_raw_source ON raw_content(source_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_raw_processed ON raw_content(is_processed)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_gen_source ON generated_content(source_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_published_date ON published_content(published_at)")
        
        conn.commit()
        conn.close()
    
    def add_source(self, name: str, source_type: str, base_url: str = None, 
                   api_key_env: str = None, fetch_interval: int = 60) -> int:
        """Add a new content source."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO sources (name, source_type, base_url, api_key_env, fetch_interval_minutes)
            VALUES (?, ?, ?, ?, ?)
        """, (name, source_type, base_url, api_key_env, fetch_interval))
        source_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return source_id
    
    def get_source_by_name(self, name: str) -> Optional[Dict]:
        """Get source by name."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sources WHERE name = ?", (name,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    
    def get_enabled_sources(self) -> List[Dict]:
        """Get all enabled sources."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sources WHERE enabled = 1")
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def update_source_stats(self, source_id: int, success: bool):
        """Update source fetch statistics."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE sources 
            SET total_fetched = total_fetched + 1,
                successful_fetches = successful_fetches + ?,
                last_fetched_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (1 if success else 0, source_id))
        conn.commit()
        conn.close()
    
    def add_raw_content(self, source_id: int, title: str, url: str, 
                        content_text: str = None, author: str = None,
                        published_at: str = None, metadata: Dict = None,
                        external_id: str = None) -> int:
        """Add raw content from a source."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO raw_content 
            (source_id, external_id, title, url, content_text, author, published_at, raw_metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (source_id, external_id, title, url, content_text, author, 
              published_at, json.dumps(metadata) if metadata else None))
        content_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return content_id
    
    def get_unprocessed_content(self, limit: int = 50) -> List[Dict]:
        """Get unprocessed raw content."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT rc.*, s.name as source_name, s.source_type
            FROM raw_content rc
            JOIN sources s ON rc.source_id = s.id
            WHERE rc.is_processed = 0
            ORDER BY rc.fetched_at DESC
            LIMIT ?
        """, (limit,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def mark_content_processed(self, content_id: int):
        """Mark raw content as processed."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE raw_content SET is_processed = 1 WHERE id = ?", (content_id,))
        conn.commit()
        conn.close()
    
    def add_generated_content(self, raw_content_id: int, source_id: int, title: str,
                              content: str, content_type: str, summary: str = None,
                              tags: str = None, word_count: int = 0) -> int:
        """Add generated content."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO generated_content 
            (raw_content_id, source_id, title, content, content_type, summary, tags, word_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (raw_content_id, source_id, title, content, content_type, 
              summary, tags, word_count))
        content_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return content_id
    
    def get_latest_generated_content(self, limit: int = 10) -> List[Dict]:
        """Get latest generated content."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT gc.*, s.name as source_name
            FROM generated_content gc
            JOIN sources s ON gc.source_id = s.id
            ORDER BY gc.generated_at DESC
            LIMIT ?
        """, (limit,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def add_published_content(self, generated_content_id: int, slug: str,
                              status: str = 'pending', log: str = None) -> int:
        """Add published content."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO published_content 
            (generated_content_id, slug, deployment_status, deployment_log)
            VALUES (?, ?, ?, ?)
        """, (generated_content_id, slug, status, log))
        content_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return content_id
    
    def update_published_status(self, published_id: int, status: str, log: str = None):
        """Update published content status."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE published_content 
            SET deployment_status = ?, deployment_log = ?
            WHERE id = ?
        """, (status, log, published_id))
        conn.commit()
        conn.close()
    
    def get_published_content(self, limit: int = 20) -> List[Dict]:
        """Get published content."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT pc.*, gc.title, gc.content, gc.content_type, gc.summary, gc.tags
            FROM published_content pc
            JOIN generated_content gc ON pc.generated_content_id = gc.id
            ORDER BY pc.published_at DESC
            LIMIT ?
        """, (limit,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def check_content_exists(self, url: str) -> bool:
        """Check if content with URL already exists."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM raw_content WHERE url = ?", (url,))
        count = cursor.fetchone()[0]
        conn.close()
        return count > 0
    
    def update_content_type_performance(self, content_type: str, views: int = 0):
        """Update content type performance metrics."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Insert or update
        cursor.execute("""
            INSERT INTO content_type_performance (content_type, total_published, total_views)
            VALUES (?, 1, ?)
            ON CONFLICT(content_type) DO UPDATE SET
                total_published = total_published + 1,
                total_views = total_views + ?,
                last_updated = CURRENT_TIMESTAMP
        """, (content_type, views, views))
        
        conn.commit()
        conn.close()
    
    def get_content_type_stats(self) -> List[Dict]:
        """Get performance stats for all content types."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT content_type, total_published, total_views, 
                   CASE WHEN total_published > 0 
                   THEN CAST(total_views AS REAL) / total_published 
                   ELSE 0 END as avg_engagement
            FROM content_type_performance
            ORDER BY avg_engagement DESC
        """)
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]


# Global database instance
db = Database()