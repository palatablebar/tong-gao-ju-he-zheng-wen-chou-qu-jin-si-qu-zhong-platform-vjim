from datetime import datetime

from pydantic import BaseModel, Field


class CorrectBodyRequest(BaseModel):
    body_text: str = Field(min_length=20, max_length=20000)
    note: str = Field(default="", max_length=200)


class ArticleOut(BaseModel):
    id: int
    raw_item_id: int
    canonical_url: str
    body_text: str
    author: str
    word_count: int
    content_density: float
    extract_confidence: float
    extractor: str
    extractor_label: str
    corrected_by: str | None = None
    corrected_at: datetime | None = None
    title: str = ""
    source_name: str = ""
    published_at: datetime | None = None
