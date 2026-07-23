from __future__ import annotations

from celery import Celery
from celery.schedules import crontab

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "hqa-worker",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    timezone=settings.celery_timezone,
    enable_utc=False,
    task_track_started=True,
    beat_schedule={
        "sync-ebay-0800": {
            "task": "app.worker.tasks.sync_ebay",
            "schedule": crontab(hour=8, minute=0),
        },
        "sync-reverb-0805": {
            "task": "app.worker.tasks.sync_reverb",
            "schedule": crontab(hour=8, minute=5),
        },
        "sync-etsy-0810": {
            "task": "app.worker.tasks.sync_etsy",
            "schedule": crontab(hour=8, minute=10),
        },
    },
)

celery_app.autodiscover_tasks(["app.worker"])
