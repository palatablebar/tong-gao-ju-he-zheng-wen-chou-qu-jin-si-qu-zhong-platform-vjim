"""Celery application shared by backend (producer) and worker (consumer)."""
from celery import Celery

from src.config.settings import settings

celery_app = Celery(
    "dedupwire",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["src.tasks.dedup_task", "src.tasks.heartbeat", "src.tasks.reextract_task"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Asia/Shanghai",
    enable_utc=False,
    task_track_started=True,
    broker_connection_retry_on_startup=True,
    worker_hijack_root_logger=False,
    task_acks_late=False,
    beat_schedule={
        "worker-heartbeat": {
            "task": "dedupwire.heartbeat",
            "schedule": 20.0,
        }
    },
)

app = celery_app
celery = celery_app
