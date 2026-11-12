"""总览数字：给报头与信源页使用。"""
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.models import Article, Cluster, DedupRun, Event, RawItem, Source, SuspectedEdge
from src.services import dedup_service


def get_overview(db: Session) -> dict:
    sources = db.scalar(select(func.count(Source.id))) or 0
    raws = db.scalar(select(func.count(RawItem.id))) or 0
    articles = db.scalar(select(func.count(Article.id))) or 0
    low_confidence = db.scalar(
        select(func.count(Article.id)).where(Article.extract_confidence < 0.4)
    ) or 0
    clusters = db.scalar(select(func.count(Cluster.id))) or 0
    suspect_count = db.scalar(select(func.count(SuspectedEdge.id))) or 0
    events = db.scalar(select(func.count(Event.id))) or 0
    members = db.scalar(select(func.sum(Cluster.member_count))) or 0
    duplicate_rate = (
        round((members - clusters) / members, 4) if members else 0.0
    )
    run = dedup_service.latest_run(db)
    last_run = None
    if run is not None:
        last_run = {
            "id": run.id,
            "status": run.status,
            "finished_at": run.finished_at,
            "article_count": run.article_count,
            "cluster_count": run.cluster_count,
            "suspect_edge_count": run.suspect_edge_count,
            "duplicate_rate": run.duplicate_rate,
        }
    return {
        "sources": sources,
        "raws": raws,
        "articles": articles,
        "low_confidence": low_confidence,
        "clusters": clusters,
        "suspect_edges": suspect_count,
        "events": events,
        "members": members,
        "duplicate_rate": duplicate_rate,
        "last_run": last_run,
    }
