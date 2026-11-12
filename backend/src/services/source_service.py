"""信源台账：列表带统计、主编可增改，编辑/只读只读。"""
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.constants.error_codes import AppError, ErrorCode
from src.models import Article, RawItem, Source
from src.utils.errors import not_found
from src.utils.serializers import source_out
from src.utils.logger import log_event


def _counts(db: Session) -> dict[int, dict]:
    raw_counts = dict(
        db.execute(
            select(RawItem.source_id, func.count(RawItem.id)).group_by(RawItem.source_id)
        ).all()
    )
    article_counts = dict(
        db.execute(
            select(RawItem.source_id, func.count(Article.id))
            .join(Article, Article.raw_item_id == RawItem.id)
            .group_by(RawItem.source_id)
        ).all()
    )
    low_counts = dict(
        db.execute(
            select(RawItem.source_id, func.count(Article.id))
            .join(Article, Article.raw_item_id == RawItem.id)
            .where(Article.extract_confidence < 0.4)
            .group_by(RawItem.source_id)
        ).all()
    )
    return {
        sid: {
            "raw_count": raw_counts.get(sid, 0),
            "article_count": article_counts.get(sid, 0),
            "low_confidence_count": low_counts.get(sid, 0),
        }
        for sid in set(raw_counts) | set(article_counts) | set(low_counts)
    }


def list_sources(db: Session) -> list[dict]:
    rows = db.scalars(select(Source).order_by(Source.weight.desc(), Source.id)).all()
    counts = _counts(db)
    return [source_out(row, counts.get(row.id)) for row in rows]


def create_source(db: Session, payload, actor) -> dict:
    exists = db.scalar(select(Source).where(Source.name == payload.name))
    if exists is not None:
        raise AppError(ErrorCode.CONFLICT, "同名信源已存在")
    row = Source(
        name=payload.name,
        homepage=payload.homepage,
        type=payload.type,
        weight=payload.weight,
        description=payload.description,
        extract_rule_status="pending",
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    log_event("source.created", source_id=row.id, by=actor.email)
    return source_out(row, {})


def update_source(db: Session, source_id: int, payload, actor) -> dict:
    row = db.get(Source, source_id)
    if row is None:
        raise not_found("source", source_id)
    for field in ("weight", "enabled", "extract_rule_status", "description"):
        value = getattr(payload, field, None)
        if value is not None:
            setattr(row, field, value)
    db.commit()
    db.refresh(row)
    log_event("source.updated", source_id=row.id, by=actor.email)
    return source_out(row, _counts(db).get(row.id))
