"""
Automation scheduler using APScheduler for 24/7 content automation.
"""

import logging
from datetime import datetime
from typing import Optional, Callable, Dict
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger


logger = logging.getLogger(__name__)


class ContentScheduler:
    """Scheduler for automated content fetching, generation, and deployment."""
    
    def __init__(self):
        """Initialize the scheduler."""
        self.scheduler = BlockingScheduler()
        self.logger = logging.getLogger(__name__)
        self.jobs: Dict[str, dict] = {}
    
    def add_interval_job(self, func: Callable, job_id: str, 
                         minutes: int = 60, **kwargs):
        """Add an interval-based job.
        
        Args:
            func: Function to execute
            job_id: Unique job identifier
            minutes: Interval in minutes
            **kwargs: Additional arguments passed to func
        """
        trigger = IntervalTrigger(minutes=minutes)
        
        self.scheduler.add_job(
            func,
            trigger=trigger,
            id=job_id,
            replace_existing=True,
            kwargs=kwargs
        )
        
        self.jobs[job_id] = {
            'type': 'interval',
            'interval_minutes': minutes,
            'func': func.__name__,
        }
        
        self.logger.info(f"Added interval job '{job_id}' every {minutes} minutes")
    
    def add_cron_job(self, func: Callable, job_id: str, 
                     hour: int = None, minute: int = 0, **kwargs):
        """Add a cron-based job.
        
        Args:
            func: Function to execute
            job_id: Unique job identifier
            hour: Hour to run (0-23)
            minute: Minute to run (0-59)
            **kwargs: Additional arguments passed to func
        """
        trigger = CronTrigger(hour=hour, minute=minute)
        
        self.scheduler.add_job(
            func,
            trigger=trigger,
            id=job_id,
            replace_existing=True,
            kwargs=kwargs
        )
        
        self.jobs[job_id] = {
            'type': 'cron',
            'hour': hour,
            'minute': minute,
            'func': func.__name__,
        }
        
        self.logger.info(f"Added cron job '{job_id}' at {hour}:{minute:02d}")
    
    def add_daily_job(self, func: Callable, job_id: str, 
                      hour: int = 6, minute: int = 0, **kwargs):
        """Add a job that runs daily at a specific time.
        
        Args:
            func: Function to execute
            job_id: Unique job identifier
            hour: Hour to run (0-23)
            minute: Minute to run (0-59)
            **kwargs: Additional arguments passed to func
        """
        return self.add_cron_job(func, job_id, hour, minute, **kwargs)
    
    def remove_job(self, job_id: str):
        """Remove a job from the scheduler.
        
        Args:
            job_id: Job identifier to remove
        """
        try:
            self.scheduler.remove_job(job_id)
            if job_id in self.jobs:
                del self.jobs[job_id]
            self.logger.info(f"Removed job '{job_id}'")
        except Exception as e:
            self.logger.error(f"Failed to remove job '{job_id}': {e}")
    
    def start(self):
        """Start the scheduler."""
        self.logger.info("Starting content scheduler...")
        self.scheduler.start()
    
    def shutdown(self):
        """Shutdown the scheduler gracefully."""
        self.logger.info("Shutting down content scheduler...")
        self.scheduler.shutdown(wait=True)
    
    def get_jobs(self) -> Dict[str, dict]:
        """Get all scheduled jobs."""
        return self.jobs.copy()
    
    def run_job_now(self, job_id: str):
        """Manually trigger a job to run immediately.
        
        Args:
            job_id: Job identifier to run
        """
        try:
            job = self.scheduler.get_job(job_id)
            if job:
                job.func()
                self.logger.info(f"Manually triggered job '{job_id}'")
            else:
                self.logger.warning(f"Job '{job_id}' not found")
        except Exception as e:
            self.logger.error(f"Failed to run job '{job_id}': {e}")


# Global scheduler instance
_scheduler: Optional[ContentScheduler] = None


def get_scheduler() -> ContentScheduler:
    """Get the global scheduler instance."""
    global _scheduler
    if _scheduler is None:
        _scheduler = ContentScheduler()
    return _scheduler