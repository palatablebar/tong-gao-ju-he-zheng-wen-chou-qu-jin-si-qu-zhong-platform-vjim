from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.config.database import get_db
from src.controllers import event_controller
from src.middlewares.auth import get_current_user, require_permission
from src.schemas.event import EventCreate, EventUpdate

router = APIRouter(prefix="/events", tags=["events"])


@router.get("")
def list_events(
    category: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return event_controller.list_timeline(db, category, date_from, date_to)


@router.post("", status_code=201)
def create_event(
    payload: EventCreate,
    db: Session = Depends(get_db),
    user=Depends(require_permission("event:write")),
):
    return event_controller.create_event(db, payload, user)


@router.patch("/{event_id}")
def update_event(
    event_id: int,
    payload: EventUpdate,
    db: Session = Depends(get_db),
    user=Depends(require_permission("event:write")),
):
    return event_controller.update_event(db, event_id, payload, user)
