from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.config.database import Base
from src.models.user import utcnow


class DedupRun(Base):
    __tablename__ = "dedup_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    status: Mapped[str] = mapped_column(String(20), default="queued", index=True)
    threshold: Mapped[float] = mapped_column(Float, default=0.72)
    suspect_threshold: Mapped[float] = mapped_column(Float, default=0.55)
    num_perm: Mapped[int] = mapped_column(Integer, default=128)
    bands: Mapped[int] = mapped_column(Integer, default=32)
    shingle_size: Mapped[int] = mapped_column(Integer, default=4)
    article_count: Mapped[int] = mapped_column(Integer, default=0)
    cluster_count: Mapped[int] = mapped_column(Integer, default=0)
    suspect_edge_count: Mapped[int] = mapped_column(Integer, default=0)
    duplicate_rate: Mapped[float] = mapped_column(Float, default=0.0)
    cross_source_count: Mapped[int] = mapped_column(Integer, default=0)
    candidate_pair_count: Mapped[int] = mapped_column(Integer, default=0)
    snapshot_path: Mapped[str] = mapped_column(String(255), default="")
    triggered_by: Mapped[str] = mapped_column(String(160), default="")
    error: Mapped[str] = mapped_column(Text, default="")
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
