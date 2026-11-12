from sqlalchemy.orm import Session

from src.services import reextract_service


def request_batch(db: Session, source_id: int, actor) -> dict:
    return reextract_service.request_batch(db, source_id, actor)


def retry_batch(db: Session, batch_id: int, actor) -> dict:
    return reextract_service.retry_batch(db, batch_id, actor)


def list_batches(db: Session, source_id: int | None, limit: int) -> dict:
    return reextract_service.list_batches(db, source_id=source_id, limit=limit)


def get_batch(db: Session, batch_id: int) -> dict:
    return reextract_service.get_batch(db, batch_id)
