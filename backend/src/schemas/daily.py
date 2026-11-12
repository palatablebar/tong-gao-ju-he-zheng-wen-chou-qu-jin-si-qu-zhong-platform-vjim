from datetime import date

from pydantic import BaseModel

from src.schemas.event import EventOut


class DailySummary(BaseModel):
    date: date
    event_count: int
    article_count: int
    cluster_count: int
    suspect_count: int
    duplicate_rate: float


class DailyReportOut(BaseModel):
    summary: DailySummary
    events: list[EventOut]
    markdown: str
    last_reextract: dict | None = None


class PublishRequest(BaseModel):
    date: date
