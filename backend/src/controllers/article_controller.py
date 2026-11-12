from sqlalchemy.orm import Session

from src.services import article_service


def correct_body(db: Session, article_id: int, payload, actor) -> dict:
    return article_service.correct_body(db, article_id, payload, actor)


def get_article(db: Session, article_id: int) -> dict:
    return article_service.get_article(db, article_id)
