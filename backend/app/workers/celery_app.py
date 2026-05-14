"""Celery application configuration."""

from celery import Celery
from app.config import settings

celery_app = Celery(
    "sales_workbench",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    # Retry settings
    task_default_retry_delay=5,
    task_max_retries=3,
)

# Auto-discover tasks
celery_app.autodiscover_tasks(["app.workers"])
