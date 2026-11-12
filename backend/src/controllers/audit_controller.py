from sqlalchemy.orm import Session

from src.services import audit_service


def list_logs(db: Session, limit: int) -> dict:
    return {"items": audit_service.list_logs(db, limit)}
