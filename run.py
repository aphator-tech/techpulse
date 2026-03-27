"""
Main entry point for the tech content automation system.
"""

import os
import sys
import logging
import argparse
from pathlib import Path


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def setup_env():
    """Setup environment variables from .env file."""
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        from dotenv import load_dotenv
        load_dotenv(env_path)
        logger.info("Loaded environment from .env")


def run_fetch(engine):
    """Run content fetching from all sources."""
    logger.info("Fetching content from all sources...")
    results = engine.fetch_from_all_sources(limit=10)
    
    total = sum(results.values())
    logger.info(f"Fetched {total} items total")
    for source, count in results.items():
        logger.info(f"  {source}: {count} items")
    
    return total


def run_generate(engine):
    """Run content generation for unprocessed items."""
    logger.info("Generating content from raw data...")
    processed = engine.process_unprocessed(max_items=5)
    logger.info(f"Generated {processed} articles")
    return processed


def run_deploy(deployer):
    """Deploy generated content."""
    from db import Database
    
    db = Database('content_data/content.db')
    generated = db.get_latest_generated_content(limit=5)
    
    for item in generated:
        try:
            deployer.deploy_content(
                title=item['title'],
                content=item['content'],
                content_type=item['content_type'],
                summary=item['summary'],
                tags=item['tags'].split(',') if item['tags'] else []
            )
            logger.info(f"Deployed: {item['title']}")
        except Exception as e:
            logger.error(f"Failed to deploy {item['title']}: {e}")
    
    return len(generated)


def run_full_cycle():
    """Run the complete automation cycle."""
    from core import get_engine, get_deployer
    
    engine = get_engine()
    deployer = get_deployer()
    
    # Fetch
    run_fetch(engine)
    
    # Generate
    run_generate(engine)
    
    # Deploy
    run_deploy(deployer)
    
    # Stats
    stats = engine.get_stats()
    logger.info(f"System stats: {stats}")


def run_scheduler():
    """Run the scheduler for continuous automation."""
    from core import get_scheduler, get_engine, get_deployer
    
    scheduler = get_scheduler()
    engine = get_engine()
    deployer = get_deployer()
    
    # Add jobs
    scheduler.add_interval_job(
        lambda: run_fetch(engine),
        job_id='fetch',
        minutes=30
    )
    
    scheduler.add_interval_job(
        lambda: run_generate(engine),
        job_id='generate',
        minutes=60
    )
    
    scheduler.add_interval_job(
        lambda: run_deploy(deployer),
        job_id='deploy',
        minutes=120
    )
    
    # Start
    logger.info("Starting scheduler...")
    scheduler.start()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Tech Content Automation System')
    parser.add_argument('command', choices=['fetch', 'generate', 'deploy', 'cycle', 'serve', 'stats'],
                       help='Command to run')
    parser.add_argument('--db', default='content_data/content.db',
                       help='Database path')
    parser.add_argument('--port', type=int, default=8080,
                       help='Port for serve command')
    
    args = parser.parse_args()
    
    # Setup
    setup_env()
    
    if args.command == 'fetch':
        from core import get_engine
        engine = get_engine(args.db)
        run_fetch(engine)
        
    elif args.command == 'generate':
        from core import get_engine
        engine = get_engine(args.db)
        run_generate(engine)
        
    elif args.command == 'deploy':
        from core import get_deployer
        deployer = get_deployer()
        run_deploy(deployer)
        
    elif args.command == 'cycle':
        run_full_cycle()
        
    elif args.command == 'serve':
        import http.server
        import socketserver
        
        os.chdir('frontend')
        PORT = args.port
        handler = http.server.SimpleHTTPRequestHandler
        logger.info(f"Serving on port {PORT}...")
        with socketserver.TCPServer(("", PORT), handler) as httpd:
            httpd.serve_forever()
    
    elif args.command == 'stats':
        from core import get_engine
        engine = get_engine(args.db)
        stats = engine.get_stats()
        print("\n=== System Statistics ===")
        print(f"Sources: {stats['sources']}")
        print(f"Raw content pending: {stats['raw_pending']}")
        print(f"Generated articles: {stats['generated_count']}")
        print(f"Published articles: {stats['published_count']}")
        print("\nContent Type Performance:")
        for t in stats['type_stats']:
            print(f"  {t['content_type']}: {t['total_published']} published, {t['avg_engagement']:.1f} avg engagement")


if __name__ == '__main__':
    main()