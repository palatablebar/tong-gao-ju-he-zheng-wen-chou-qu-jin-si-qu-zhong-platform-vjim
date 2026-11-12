from sqlalchemy.orm import Session

from src.services import event_service


def list_timeline(db: Session, category, date_from, date_to) -> dict:
    return event_service.list_timeline(db, category=category, date_from=date_from, date_to=date_to)


def create_event(db: Session, payload, actor) -> dict:
    return event_service.create_event(db, payload, actor)


def update_event(db: Session, event_id: int, payload, actor) -> dict:
    return event_service.update_event(db, event_id, payload, actor)
