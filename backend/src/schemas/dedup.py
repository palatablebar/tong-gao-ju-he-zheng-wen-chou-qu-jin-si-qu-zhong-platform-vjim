from datetime import datetime

from pydantic import BaseModel, Field


class DedupRunRequest(BaseModel):
    threshold: float = Field(default=0.72, ge=0.5, le=0.95)
    suspect_threshold: float = Field(default=0.55, ge=0.3, le=0.7)


class DedupRunOut(BaseModel):
    id: int
    status: str
    status_label: str
    threshold: float
    suspect_threshold: float
    num_perm: int
    bands: int
    shingle_size: int
    article_count: int
    cluster_count: int
    suspect_edge_count: int
    duplicate_rate: float
    candidate_pair_count: int
    cross_source_count: int
    snapshot_path: str
    triggered_by: str
    error: str
    started_at: datetime | None = None
    finished_at: datetime | None = None
    created_at: datetime
