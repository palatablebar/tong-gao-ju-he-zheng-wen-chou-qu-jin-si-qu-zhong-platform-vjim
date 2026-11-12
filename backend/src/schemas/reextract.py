from datetime import datetime

from pydantic import BaseModel, Field


class ReextractRequest(BaseModel):
    source_id: int = Field(ge=1)


class ReextractItemOut(BaseModel):
    id: int
    batch_id: int
    raw_item_id: int
    article_id: int | None = None
    title: str = ""
    source_name: str = ""
    status: str
    status_label: str
    body_changed: bool = False
    before_extractor: str = ""
    before_confidence: float = 0.0
    after_extractor: str = ""
    after_confidence: float = 0.0
    error_note: str = ""
    processed_at: datetime | None = None


class ReextractBatchOut(BaseModel):
    id: int
    source_id: int
    source_name: str = ""
    rule_signature: str = ""
    status: str
    status_label: str
    total_count: int = 0
    succeeded_count: int = 0
    failed_count: int = 0
    skipped_count: int = 0
    pending_count: int = 0
    body_changed_count: int = 0
    attempt_count: int = 0
    cursor_raw_item_id: int | None = None
    dedup_run_id: int | None = None
    dedup_run: dict | None = None
    dedup_pending: bool = False
    triggered_by: str = ""
    error: str = ""
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    last_processed_at: datetime | None = None
    deduplicated: bool = False
    items: list[ReextractItemOut] = []
