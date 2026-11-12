from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.config.database import Base
from src.models.raw_item import RawItem  # noqa: F401  (relationship target)
from src.models.source import Source  # noqa: F401  (relationship target)
from src.models.user import utcnow


class ReextractBatch(Base):
    """按信源发起的一批正文重抽任务。

    ``request_key`` 由「信源 + 抽取规则签名」组成，同一规则下重复发起会复用同一批次，
    不会重复建任务或重复建簇；规则更新后签名变化，才会开启新批次。
    """

    __tablename__ = "reextract_batches"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"), index=True)
    request_key: Mapped[str] = mapped_column(String(160), unique=True, index=True)
    rule_signature: Mapped[str] = mapped_column(String(64), default="")
    status: Mapped[str] = mapped_column(String(20), default="queued", index=True)
    total_count: Mapped[int] = mapped_column(Integer, default=0)
    succeeded_count: Mapped[int] = mapped_column(Integer, default=0)
    failed_count: Mapped[int] = mapped_column(Integer, default=0)
    skipped_count: Mapped[int] = mapped_column(Integer, default=0)
    pending_count: Mapped[int] = mapped_column(Integer, default=0)
    body_changed_count: Mapped[int] = mapped_column(Integer, default=0)
    attempt_count: Mapped[int] = mapped_column(Integer, default=0)
    cursor_raw_item_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    dedup_run_id: Mapped[int | None] = mapped_column(
        ForeignKey("dedup_runs.id"), nullable=True, index=True
    )
    triggered_by: Mapped[str] = mapped_column(String(160), default="")
    error: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    source: Mapped["Source"] = relationship("Source", lazy="joined")  # noqa: F821
    items: Mapped[list["ReextractItem"]] = relationship(
        "ReextractItem",
        back_populates="batch",
        cascade="all, delete-orphan",
        order_by="ReextractItem.raw_item_id",
    )


class ReextractItem(Base):
    """批次内每条抓取记录的结果。

    ``status`` 为 pending / running / succeeded / failed / skipped_manual；
    失败项在批次结束后仍然保留，可通过「重试」从失败项与未处理项继续跑。
    """

    __tablename__ = "reextract_items"
    __table_args__ = (
        UniqueConstraint("batch_id", "raw_item_id", name="uq_reextract_batch_raw"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    batch_id: Mapped[int] = mapped_column(ForeignKey("reextract_batches.id"), index=True)
    raw_item_id: Mapped[int] = mapped_column(ForeignKey("raw_items.id"), index=True)
    article_id: Mapped[int | None] = mapped_column(
        ForeignKey("articles.id"), nullable=True, index=True
    )
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    body_changed: Mapped[bool] = mapped_column(Boolean, default=False)
    before_extractor: Mapped[str] = mapped_column(String(20), default="")
    before_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    after_extractor: Mapped[str] = mapped_column(String(20), default="")
    after_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    error_note: Mapped[str] = mapped_column(String(255), default="")
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    batch: Mapped["ReextractBatch"] = relationship("ReextractBatch", back_populates="items")
    raw_item: Mapped["RawItem"] = relationship("RawItem", lazy="joined")  # noqa: F821
