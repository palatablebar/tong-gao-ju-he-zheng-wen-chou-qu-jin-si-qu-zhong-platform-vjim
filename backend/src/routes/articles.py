from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.config.database import get_db
from src.controllers import article_controller
from src.middlewares.auth import get_current_user, require_permission
from src.schemas.article import CorrectBodyRequest

router = APIRouter(prefix="/articles", tags=["articles"])


@router.get("/{article_id}")
def get_article(article_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return article_controller.get_article(db, article_id)


@router.post("/{article_id}/correct")
def correct_body(
    article_id: int,
    payload: CorrectBodyRequest,
    db: Session = Depends(get_db),
    user=Depends(require_permission("article:correct")),
):
    return article_controller.correct_body(db, article_id, payload, user)
