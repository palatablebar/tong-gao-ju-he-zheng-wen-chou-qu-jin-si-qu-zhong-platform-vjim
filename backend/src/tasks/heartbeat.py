"""Celery beat 心跳：worker 健康检查读这个 Redis key。"""
import time

from src.config.celery_app import celery_app
from src.utils.ratelimit import worker_heartbeat


@celery_app.task(name="dedupwire.heartbeat")
def heartbeat_task() -> dict:
    worker_heartbeat(time.time())
    return {"ok": True}
