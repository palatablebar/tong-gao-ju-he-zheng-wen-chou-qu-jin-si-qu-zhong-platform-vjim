from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.config.database import get_db
from src.controllers import dedup_controller
from src.middlewares.auth import get_current_user, require_permission
from src.schemas.dedup import DedupRunRequest

router = APIRouter(prefix="/dedup", tags=["dedup"])


@router.post("/runs", status_code=202)
def create_run(
    payload: DedupRunRequest,
    db: Session = Depends(get_db),
    user=Depends(require_permission("dedup:run")),
):
    return dedup_controller.create_run(db, payload, user)


@router.get("/runs")
def list_runs(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return dedup_controller.list_runs(db)


@router.get("/runs/latest")
def latest(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return dedup_controller.latest(db)


@router.get("/runs/{run_id}")
def get_run(run_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return dedup_controller.get_run(db, run_id)
