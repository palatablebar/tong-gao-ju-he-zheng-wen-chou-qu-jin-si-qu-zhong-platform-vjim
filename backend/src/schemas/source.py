from datetime import datetime

from pydantic import BaseModel, Field


class SourceCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    homepage: str = Field(min_length=4, max_length=255)
    type: str = Field(pattern="^(media|government|selfmedia)$")
    weight: int = Field(default=3, ge=1, le=5)
    description: str = ""


class SourceUpdate(BaseModel):
    weight: int | None = Field(default=None, ge=1, le=5)
    enabled: bool | None = None
    extract_rule_status: str | None = Field(default=None, pattern="^(ok|degraded|pending)$")
    description: str | None = None


class SourceOut(BaseModel):
    id: int
    name: str
    homepage: str
    type: str
    type_label: str
    weight: int
    extract_rule_status: str
    enabled: bool
    description: str
    last_fetched_at: datetime | None = None
    raw_count: int = 0
    article_count: int = 0
    low_confidence_count: int = 0
