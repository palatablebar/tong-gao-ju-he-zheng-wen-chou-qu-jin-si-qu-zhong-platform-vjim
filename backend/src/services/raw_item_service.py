"""原文队列：列表筛选、详情（原始片段 + 抽取正文 + 候选片段）。"""
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.models import Article, RawItem
from src.services import extraction_service
from src.utils.errors import not_found
from src.utils.serializers import article_out, raw_item_out


def list_items(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    status: str | None = None,
    low_confidence: bool = False,
    source_id: int | None = None,
    q: str | None = None,
) -> dict:
    base = select(RawItem)
    if source_id:
        base = base.where(RawItem.source_id == source_id)
    if status:
        base = base.where(RawItem.status == status)
    if q:
        base = base.where(RawItem.title.ilike(f"%{q}%"))
    if low_confidence:
        base = base.join(Article, Article.raw_item_id == RawItem.id).where(
            Article.extract_confidence < 0.4
        )
    total = db.scalar(select(func.count()).select_from(base.subquery())) or 0
    rows = db.scalars(
        base.order_by(RawItem.published_at.desc(), RawItem.id.desc())
        .offset((max(1, page) - 1) * page_size)
        .limit(page_size)
    ).all()
    items = []
    for row in rows:
        article = db.scalar(select(Article).where(Article.raw_item_id == row.id))
        item = raw_item_out(row)
        if article is not None:
            item["article"] = {
                "id": article.id,
                "word_count": article.word_count,
                "content_density": round(article.content_density, 4),
                "extract_confidence": round(article.extract_confidence, 4),
                "extractor": article.extractor,
                "extractor_label": {"readability": "密度抽取", "fallback": "兜底抽取", "manual": "人工校正"}.get(
                    article.extractor, article.extractor
                ),
            }
        items.append(item)
    return {"items": items, "total": total, "page": page, "page_size": page_size}


def get_detail(db: Session, raw_item_id: int) -> dict:
    raw = db.get(RawItem, raw_item_id)
    if raw is None:
        raise not_found("raw_item", raw_item_id)
    article = db.scalar(select(Article).where(Article.raw_item_id == raw_item_id))
    preview = extraction_service.extract_preview(raw.raw_html)
    article_payload = None
    if article is not None:
        article_payload = article_out(article)
        result = extraction_service.extract_preview(raw.raw_html)
        article_payload["blocks"] = [item["text"] for item in result["candidates"]]
        article_payload["extractor_label"] = article_payload["extractor_label"]
    return {
        "item": raw_item_out(raw),
        "raw_html_excerpt": raw.raw_html[:4000],
        "article": article_payload,
        "preview": preview,
    }
