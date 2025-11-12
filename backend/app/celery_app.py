"""Celery application configuration"""
from celery import Celery
from celery.schedules import crontab
from app.config import settings

# Create Celery app
celery_app = Celery(
    "communitycircle",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.tasks.reminders",
        "app.tasks.expiry",
        "app.tasks.cache",
    ]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes
    task_soft_time_limit=240,  # 4 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    # Check for shifts needing 24h reminders every hour
    "send-24h-reminders": {
        "task": "app.tasks.reminders.send_24h_reminders",
        "schedule": crontab(minute=0),  # Every hour at minute 0
    },
    # Check for shifts needing 2h reminders every 15 minutes
    "send-2h-reminders": {
        "task": "app.tasks.reminders.send_2h_reminders",
        "schedule": crontab(minute="*/15"),  # Every 15 minutes
    },
    # Expire old posts daily at 2 AM
    "expire-old-posts": {
        "task": "app.tasks.expiry.expire_old_posts",
        "schedule": crontab(hour=2, minute=0),  # Daily at 2 AM
    },
    # Refresh expired resource cache weekly on Sundays at 3 AM
    "refresh-resource-cache": {
        "task": "app.tasks.cache.refresh_expired_resources",
        "schedule": crontab(day_of_week=0, hour=3, minute=0),  # Sundays at 3 AM
    },
}

if __name__ == "__main__":
    celery_app.start()
