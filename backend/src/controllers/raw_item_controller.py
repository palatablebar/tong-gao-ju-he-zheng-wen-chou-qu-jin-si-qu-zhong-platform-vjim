from sqlalchemy.orm import Session

from src.services import raw_item_service


def list_items(db: Session, page: int, page_size: int, status, low_confidence, source_id, q) -> dict:
    return raw_item_service.list_items(
        db,
        page=page,
        page_size=page_size,
        status=status,
        low_confidence=low_confidence,
        source_id=source_id,
        q=q,
    )


def get_detail(db: Session, raw_item_id: int) -> dict:
    return raw_item_service.get_detail(db, raw_item_id)
