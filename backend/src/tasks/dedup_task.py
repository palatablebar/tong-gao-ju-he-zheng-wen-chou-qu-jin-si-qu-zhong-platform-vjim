"""Celery 任务：执行 MinHash + LSH 去重（前端轮询 dedup_runs 状态）。"""
from src.config.celery_app import celery_app
from src.services import dedup_service
from src.utils.logger import log_event


@celery_app.task(name="dedupwire.run_dedup", bind=True, max_retries=0)
def run_dedup_task(self, run_id: int) -> dict:
    log_event("dedup.worker_start", run_id=run_id)
    dedup_service.execute_run(run_id)
    return {"run_id": run_id, "status": "succeeded"}
