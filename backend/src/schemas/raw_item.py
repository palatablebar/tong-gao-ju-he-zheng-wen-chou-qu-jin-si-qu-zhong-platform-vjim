from datetime import datetime

from pydantic import BaseModel


class SourceBrief(BaseModel):
    id: int
    name: str
    type: str
    type_label: str
    weight: int


class ArticleBrief(BaseModel):
    id: int
    word_count: int
    content_density: float
    extract_confidence: float
    extractor: str
    extractor_label: str


class RawItemOut(BaseModel):
    id: int
    title: str
    url: str
    published_at: datetime
    fetched_at: datetime
    status: str
    status_label: str
    error_note: str
    source: SourceBrief
    article: ArticleBrief | None = None


class CandidateOut(BaseModel):
    block_id: str
    text: str
    score: float
    tag: str


class ExtractionPreviewOut(BaseModel):
    top_score: float
    page_chars: int
    body_chars: int
    candidates: list[CandidateOut]


class ArticleDetailOut(BaseModel):
    id: int
    body_text: str
    author: str
    word_count: int
    content_density: float
    extract_confidence: float
    extractor: str
    extractor_label: str
    corrected_by: str | None = None
    corrected_at: datetime | None = None
    blocks: list[str] = []  # type: ignore[assignment]


class RawItemDetailOut(BaseModel):
    item: RawItemOut
    raw_html_excerpt: str
    article: ArticleDetailOut | None = None
    preview: ExtractionPreviewOut | None = None
