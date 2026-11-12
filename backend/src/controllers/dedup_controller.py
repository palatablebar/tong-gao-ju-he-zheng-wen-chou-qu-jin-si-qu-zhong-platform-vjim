from sqlalchemy.orm import Session

from src.config.settings import settings
from src.constants.messages import RATE_LIMITED
from src.services import dedup_service
from src.utils.ratelimit import enforce


def create_run(db: Session, payload, actor) -> dict:
    enforce(f"dedupwire:dedup:{actor.id}", settings.DEDUP_RATE_LIMIT_PER_MINUTE, RATE_LIMITED)
    return dedup_service.create_run(db, payload, actor)


def get_run(db: Session, run_id: int) -> dict:
    return dedup_service.get_run(db, run_id)


def latest(db: Session) -> dict:
    run = dedup_service.latest_run(db)
    return {"run": dedup_service.dedup_run_out(run) if run else None}


def list_runs(db: Session) -> dict:
    return {"items": dedup_service.list_runs(db)}
