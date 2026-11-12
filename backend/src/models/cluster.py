from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.config.database import Base
from src.models.user import utcnow


class Cluster(Base):
    __tablename__ = "clusters"

    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[int | None] = mapped_column(ForeignKey("dedup_runs.id"), nullable=True, index=True)
    topic_label: Mapped[str] = mapped_column(String(160), index=True)
    representative_article_id: Mapped[int | None] = mapped_column(
        ForeignKey("articles.id"), nullable=True
    )
    member_count: Mapped[int] = mapped_column(Integer, default=0)
    mean_similarity: Mapped[float] = mapped_column(Float, default=0.0)
    first_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="auto", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    members: Mapped[list["ClusterMember"]] = relationship(
        "ClusterMember",
        back_populates="cluster",
        cascade="all, delete-orphan",
        order_by="ClusterMember.similarity_to_rep.desc()",
    )


class ClusterMember(Base):
    __tablename__ = "cluster_members"
    __table_args__ = (UniqueConstraint("cluster_id", "article_id", name="uq_cluster_article"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    cluster_id: Mapped[int] = mapped_column(ForeignKey("clusters.id"), index=True)
    article_id: Mapped[int] = mapped_column(ForeignKey("articles.id"), index=True)
    similarity_to_rep: Mapped[float] = mapped_column(Float, default=0.0)
    is_suspected: Mapped[bool] = mapped_column(default=False)

    cluster: Mapped["Cluster"] = relationship("Cluster", back_populates="members")
    article: Mapped["Article"] = relationship("Article", lazy="joined")  # noqa: F821


class SuspectedEdge(Base):
    __tablename__ = "suspected_edges"

    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[int | None] = mapped_column(ForeignKey("dedup_runs.id"), nullable=True, index=True)
    article_a_id: Mapped[int] = mapped_column(ForeignKey("articles.id"), index=True)
    article_b_id: Mapped[int] = mapped_column(ForeignKey("articles.id"), index=True)
    cluster_a_id: Mapped[int | None] = mapped_column(ForeignKey("clusters.id"), nullable=True)
    cluster_b_id: Mapped[int | None] = mapped_column(ForeignKey("clusters.id"), nullable=True)
    similarity: Mapped[float] = mapped_column(Float, default=0.0)
