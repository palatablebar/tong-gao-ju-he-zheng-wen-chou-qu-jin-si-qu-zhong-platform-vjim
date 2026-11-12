from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from src.config.database import get_db
from src.controllers import reextract_controller
from src.middlewares.auth import get_current_user, require_permission
from src.schemas.reextract import ReextractRequest

router = APIRouter(prefix="/reextract", tags=["reextract"])


@router.post("/batches", status_code=202)
def request_batch(
    payload: ReextractRequest,
    db: Session = Depends(get_db),
    user=Depends(require_permission("reextract:run")),
):
    return reextract_controller.request_batch(db, payload.source_id, user)


@router.get("/batches")
def list_batches(
    source_id: int | None = None,
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return reextract_controller.list_batches(db, source_id, limit)


@router.get("/batches/{batch_id}")
def get_batch(batch_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return reextract_controller.get_batch(db, batch_id)


@router.post("/batches/{batch_id}/retry", status_code=202)
def retry_batch(
    batch_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_permission("reextract:run")),
):
    return reextract_controller.retry_batch(db, batch_id, user)
