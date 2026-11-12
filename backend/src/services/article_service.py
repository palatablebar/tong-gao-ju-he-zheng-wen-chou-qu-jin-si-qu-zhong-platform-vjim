"""原文正文校正：编辑/主编可改，viewer 403（由路由依赖拦）。"""
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.constants.enums import ExtractorMode
from src.models import Article, RawItem, ReextractItem
from src.services import audit_service
from src.utils.errors import not_found
from src.utils.serializers import article_out
from src.utils.textnorm import chinese_char_count


def list_low_confidence(db: Session, limit: int = 20) -> list[dict]:
    rows = db.scalars(
        select(Article)
        .where(Article.extract_confidence < 0.4)
        .order_by(Article.extract_confidence.asc())
        .limit(limit)
    ).all()
    return [article_out(row) for row in rows]


def correct_body(db: Session, article_id: int, payload, actor) -> dict:
    article = db.get(Article, article_id)
    if article is None:
        raise not_found("article", article_id)
    raw = db.get(RawItem, article.raw_item_id)
    article.body_text = payload.body_text.strip()
    article.word_count = chinese_char_count(article.body_text)
    article.extractor = ExtractorMode.MANUAL.value
    article.extract_confidence = max(0.9, round(article.extract_confidence, 2))
    article.corrected_by = actor.email
    article.corrected_at = datetime.now(timezone.utc)
    # 人工校正优先：任何仍在排队的重抽项都改为 skipped，避免手动保存后被自动覆盖。
    db.query(ReextractItem).filter(
        ReextractItem.raw_item_id == article.raw_item_id,
        ReextractItem.status.in_(["pending", "running"]),
    ).update({ReextractItem.status: "skipped_manual"}, synchronize_session=False)
    audit_service.record(
        db,
        actor,
        action="article.correct_body",
        target_type="article",
        target_id=article.id,
        detail={
            "title": raw.title if raw else "",
            "old_extractor": "manual",
            "word_count": article.word_count,
            "note": payload.note,
        },
    )
    db.commit()
    db.refresh(article)
    return article_out(article)


def get_article(db: Session, article_id: int) -> dict:
    article = db.get(Article, article_id)
    if article is None:
        raise not_found("article", article_id)
    return article_out(article)
