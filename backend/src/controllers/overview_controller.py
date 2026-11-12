from sqlalchemy.orm import Session

from src.services import overview_service


def get_overview(db: Session) -> dict:
    return overview_service.get_overview(db)
