from sqlalchemy.orm import Session

from src.services import source_service


def list_sources(db: Session) -> dict:
    return {"items": source_service.list_sources(db)}


def create_source(db: Session, payload, actor) -> dict:
    return source_service.create_source(db, payload, actor)


def update_source(db: Session, source_id: int, payload, actor) -> dict:
    return source_service.update_source(db, source_id, payload, actor)
