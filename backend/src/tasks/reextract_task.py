"""Celery 任务：按信源重抽正文批次（前端轮询 reextract_batches 状态）。"""
from src.config.celery_app import celery_app
from src.services import reextract_service
from src.utils.logger import log_event


@celery_app.task(name="dedupwire.run_reextract", bind=True, max_retries=0)
def run_reextract_task(self, batch_id: int) -> dict:
    log_event("reextract.worker_start", batch_id=batch_id)
    reextract_service.execute_batch(batch_id)
    return {"batch_id": batch_id}
