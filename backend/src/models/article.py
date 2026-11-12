from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.config.database import Base
from src.models.user import utcnow


class Article(Base):
    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(primary_key=True)
    raw_item_id: Mapped[int] = mapped_column(ForeignKey("raw_items.id"), unique=True, index=True)
    canonical_url: Mapped[str] = mapped_column(String(512))
    body_text: Mapped[str] = mapped_column(Text, default="")
    author: Mapped[str] = mapped_column(String(80), default="")
    word_count: Mapped[int] = mapped_column(Integer, default=0)
    content_density: Mapped[float] = mapped_column(Float, default=0.0)
    extract_confidence: Mapped[float] = mapped_column(Float, default=0.0, index=True)
    extractor: Mapped[str] = mapped_column(String(20), default="readability")
    corrected_by: Mapped[str | None] = mapped_column(String(160), nullable=True)
    corrected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    raw_item: Mapped["RawItem"] = relationship("RawItem", lazy="joined")  # noqa: F821

    @property
    def source_id(self) -> int:
        return self.raw_item.source_id
