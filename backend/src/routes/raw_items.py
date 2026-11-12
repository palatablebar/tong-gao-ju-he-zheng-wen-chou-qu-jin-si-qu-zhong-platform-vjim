from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from src.config.database import get_db
from src.controllers import raw_item_controller
from src.middlewares.auth import get_current_user

router = APIRouter(prefix="/raw-items", tags=["raw-items"])


@router.get("")
def list_items(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status: str | None = None,
    low_confidence: bool = False,
    source_id: int | None = None,
    q: str | None = None,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return raw_item_controller.list_items(
        db, page, page_size, status, low_confidence, source_id, q
    )


@router.get("/{raw_item_id}")
def get_detail(raw_item_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return raw_item_controller.get_detail(db, raw_item_id)
