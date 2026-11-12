from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.config.database import Base
from src.models.user import utcnow


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    homepage: Mapped[str] = mapped_column(String(255))
    type: Mapped[str] = mapped_column(String(20), index=True)
    weight: Mapped[int] = mapped_column(Integer, default=3)
    extract_rule_status: Mapped[str] = mapped_column(String(20), default="ok")
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    description: Mapped[str] = mapped_column(Text, default="")
    last_fetched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
