from datetime import date, datetime

from pydantic import BaseModel, Field


class EventCreate(BaseModel):
    title: str = Field(min_length=4, max_length=200)
    category: str = Field(pattern="^(政策|产业|民生|财经)$")
    event_date: date
    region: str = Field(default="", max_length=80)
    note: str = ""
    cluster_id: int | None = None


class EventUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=4, max_length=200)
    category: str | None = Field(default=None, pattern="^(政策|产业|民生|财经)$")
    region: str | None = None
    note: str | None = None
    cluster_id: int | None = None


class EventOut(BaseModel):
    id: int
    title: str
    category: str
    event_date: date
    region: str
    note: str
    cluster_id: int | None = None
    cluster_label: str = ""
    member_count: int = 0
    representative_title: str = ""
    representative_source: str = ""
    published_at: datetime | None = None
