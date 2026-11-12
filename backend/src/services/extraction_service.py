"""算法 A 的落库封装：raw_html → Article（body/density/confidence/extractor）。"""
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.config.settings import settings
from src.constants.enums import ExtractorMode, RawStatus
from src.models import Article, RawItem
from src.services import readability
from src.utils.textnorm import chinese_char_count


def run_extractor(raw_html: str):
    """Pure algorithm A call with the runtime thresholds."""
    return readability.extract(
        raw_html,
        score_divisor=settings.EXTRACT_SCORE_DIVISOR,
        min_body_chars=settings.EXTRACT_MIN_BODY_CHARS,
    )


def is_manual_corrected(article: Article | None) -> bool:
    """Human-corrected bodies are never overwritten by any automated pass."""
    if article is None:
        return False
    return article.extractor == ExtractorMode.MANUAL.value or article.corrected_by is not None


def extract_preview(raw_html: str) -> dict:
    """Re-run extraction for the review UI (candidate blocks + scores)."""
    result = run_extractor(raw_html)
    return {
        "top_score": result.top_score,
        "page_chars": result.page_chars,
        "body_chars": result.body_chars,
        "candidates": [
            {"block_id": item.block_id, "text": item.text, "score": item.score, "tag": item.tag}
            for item in result.candidates
        ],
    }


def apply_result(db: Session, raw: RawItem, article: Article | None, result) -> Article:
    """Write an extraction result onto a raw item / article (no manual guard here)."""
    if article is None:
        article = Article(raw_item_id=raw.id, canonical_url=raw.url)
        db.add(article)
        db.flush()
    article.body_text = result.body_text
    article.word_count = chinese_char_count(result.body_text)
    article.content_density = result.content_density
    article.extract_confidence = result.extract_confidence
    article.extractor = result.extractor
    article.canonical_url = raw.url
    if not result.body_text:
        article.body_text = ""
        raw.status = RawStatus.FAILED.value
        raw.error_note = raw.error_note or "正文抽取为空"
    else:
        raw.status = RawStatus.PARSED.value
    return article


def extract_and_store(db: Session, raw: RawItem, agent: str | None = None) -> Article:
    result = run_extractor(raw.raw_html)
    article = db.scalar(select(Article).where(Article.raw_item_id == raw.id))
    article = apply_result(db, raw, article, result)
    article.author = agent or article.author or ""
    return article


def extract_all(db: Session, raws: list[RawItem]) -> list[Article]:
    articles = [extract_and_store(db, raw) for raw in raws]
    db.flush()
    return articles
