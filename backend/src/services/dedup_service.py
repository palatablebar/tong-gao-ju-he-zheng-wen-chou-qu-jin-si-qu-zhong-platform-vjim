"""算法 B 的编排：创建 Celery 任务 → worker 执行 → 结果落库 + 快照。

簇采用「按代表稿原地更新」的写法：代表稿不变时 cluster.id 不变，
因此 Event.cluster_id 外键在重算后依然有效（不破坏用户的已确认状态）。
"""
import json
import os
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.config.database import SessionLocal
from src.config.settings import settings
from src.constants.enums import ClusterStatus, DedupRunStatus
from src.constants.error_codes import AppError, ErrorCode
from src.constants.messages import DEDUP_BUSY
from src.models import Article, Cluster, ClusterMember, DedupRun, Event, SuspectedEdge
from src.services import audit_service
from src.services.dedup import ArticleDoc, DedupParams, run_dedup
from src.utils.logger import log_event
from src.utils.serializers import dedup_run_out
from src.utils.textnorm import chinese_char_count


class _SystemActor:
    email = "system:dedup"
    role = "system"


_SYSTEM_ACTOR = _SystemActor()


def article_doc(article: Article) -> ArticleDoc:
    raw = article.raw_item
    source = raw.source
    return ArticleDoc(
        article_id=article.id,
        text=article.body_text or "",
        title=raw.title,
        published_at=raw.published_at,
        source_id=raw.source_id,
        source_weight=source.weight if source else 3,
        word_count=article.word_count or chinese_char_count(article.body_text),
    )


def build_docs(db: Session) -> list[ArticleDoc]:
    articles = db.scalars(select(Article).order_by(Article.id)).all()
    return [article_doc(article) for article in articles if (article.body_text or "").strip()]


def _run_params(run: DedupRun) -> DedupParams:
    return DedupParams(
        threshold=run.threshold,
        suspect_threshold=run.suspect_threshold,
        num_perm=run.num_perm,
        bands=run.bands,
        shingle_size=run.shingle_size,
        hash_seed=settings.DEDUP_HASH_SEED,
    )


def latest_run(db: Session) -> DedupRun | None:
    return db.scalar(select(DedupRun).order_by(DedupRun.id.desc()).limit(1))


def list_runs(db: Session, limit: int = 8) -> list[dict]:
    rows = db.scalars(select(DedupRun).order_by(DedupRun.id.desc()).limit(limit)).all()
    return [dedup_run_out(row) for row in rows]


def create_run(db: Session, payload, actor) -> dict:
    active = db.scalar(
        select(DedupRun).where(DedupRun.status.in_([DedupRunStatus.QUEUED.value, DedupRunStatus.RUNNING.value]))
    )
    if active is not None:
        raise AppError(ErrorCode.CONFLICT, DEDUP_BUSY)
    return request_run(db, payload, actor)


def request_run(db: Session, payload, actor) -> dict:
    """Create + queue a dedup run without the busy guard (callers handle dedup themselves)."""
    run = DedupRun(
        status=DedupRunStatus.QUEUED.value,
        threshold=payload.threshold,
        suspect_threshold=payload.suspect_threshold,
        num_perm=settings.DEDUP_NUM_PERM,
        bands=settings.DEDUP_BANDS,
        shingle_size=settings.DEDUP_SHINGLE_SIZE,
        triggered_by=actor.email,
    )
    db.add(run)
    audit_service.record(
        db,
        actor,
        action="dedup.run_requested",
        target_type="dedup_run",
        target_id="pending",
        detail={"threshold": payload.threshold, "suspect_threshold": payload.suspect_threshold},
    )
    db.commit()
    db.refresh(run)
    log_event("dedup.run_created", run_id=run.id, by=actor.email)
    try:
        from src.tasks.dedup_task import run_dedup_task

        run_dedup_task.delay(run.id)
    except Exception as exc:  # noqa: BLE001 - broker down: compute inline, never silently fail
        log_event("dedup.broker_unavailable", run_id=run.id, error=str(exc))
        execute_run(run.id)
        db.refresh(run)
    return dedup_run_out(run)


def get_run(db: Session, run_id: int) -> dict:
    run = db.get(DedupRun, run_id)
    if run is None:
        raise AppError(ErrorCode.NOT_FOUND, f"记录不存在：dedup_run#{run_id}")
    return dedup_run_out(run)


def _write_snapshot(run: DedupRun, result) -> str:
    directory = os.path.join(settings.VAR_DIR, "runs")
    os.makedirs(directory, exist_ok=True)
    path = os.path.join(directory, f"run-{run.id}.json")
    payload = {
        "run_id": run.id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "params": {
            "threshold": run.threshold,
            "suspect_threshold": run.suspect_threshold,
            "num_perm": run.num_perm,
            "bands": run.bands,
            "shingle_size": run.shingle_size,
            "hash_seed": settings.DEDUP_HASH_SEED,
        },
        "article_count": result.article_count,
        "cluster_count": len(result.clusters),
        "suspect_edge_count": len(result.suspect_edges),
        "duplicate_rate": result.duplicate_rate,
        "candidate_pairs": result.candidate_pairs,
        "clusters": [
            {
                "topic_label": cluster.topic_label,
                "representative_id": cluster.representative_id,
                "members": cluster.members,
                "mean_similarity": cluster.mean_similarity,
                "first_seen_at": cluster.first_seen_at.isoformat() if cluster.first_seen_at else None,
            }
            for cluster in result.clusters
        ],
        "suspect_edges": [
            {
                "article_a_id": edge.article_a_id,
                "article_b_id": edge.article_b_id,
                "similarity": edge.similarity,
            }
            for edge in result.suspect_edges
        ],
    }
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
    return path


def _persist(db: Session, run: DedupRun, result, docs: list[ArticleDoc]) -> dict:
    by_id = {doc.article_id: doc for doc in docs}
    new_rep_ids = {cluster.representative_id for cluster in result.clusters}
    member_sets = {spec.representative_id: set(spec.members) for spec in result.clusters}

    old_clusters = db.scalars(select(Cluster).order_by(Cluster.id)).all()
    old_by_rep = {cluster.representative_article_id: cluster for cluster in old_clusters}
    cluster_id_map: dict[int, int] = {
        rep: cluster.id for rep, cluster in old_by_rep.items() if rep is not None
    }

    # 代表稿相同：原地更新。代表稿变化：沿用成员重叠最多的旧簇（保留 cluster.id、
    # confirmed/split 状态与 Event.cluster_id 关联），保证重抽后可追溯。
    orphaned = [
        cluster
        for cluster in old_clusters
        if cluster.representative_article_id not in new_rep_ids
    ]
    claimed: dict[int, int] = {}  # old_cluster_id -> new representative id
    cluster_for_spec: dict[int, Cluster] = {}
    for spec in result.clusters:
        if spec.representative_id in old_by_rep:
            cluster_for_spec[spec.representative_id] = old_by_rep[spec.representative_id]
            continue
        best_cluster, best_overlap = None, 0
        for cluster in orphaned:
            if cluster.id in claimed:
                continue
            overlap = len(
                {member.article_id for member in cluster.members}
                & member_sets[spec.representative_id]
            )
            if overlap > best_overlap:
                best_cluster, best_overlap = cluster, overlap
        if best_cluster is not None and best_overlap > 0:
            claimed[best_cluster.id] = spec.representative_id
            cluster_for_spec[spec.representative_id] = best_cluster
        else:
            cluster_for_spec[spec.representative_id] = None

    for cluster in orphaned:
        if cluster.id in claimed:
            continue
        db.query(Event).filter(Event.cluster_id == cluster.id).update({Event.cluster_id: None})
        db.query(ClusterMember).filter(ClusterMember.cluster_id == cluster.id).delete()
        db.delete(cluster)
    db.flush()

    for spec in result.clusters:
        cluster = cluster_for_spec.get(spec.representative_id)
        if cluster is None:
            # 真正新增的簇：NOT NULL 字段在 flush 前填好，避免先插入空标签。
            cluster = Cluster(
                run_id=run.id,
                status=ClusterStatus.AUTO.value,
                topic_label=spec.topic_label,
                representative_article_id=spec.representative_id,
                member_count=len(spec.members),
                mean_similarity=spec.mean_similarity,
                first_seen_at=spec.first_seen_at,
            )
            db.add(cluster)
            db.flush()
        else:
            db.query(ClusterMember).filter(ClusterMember.cluster_id == cluster.id).delete()
        cluster.run_id = run.id
        cluster.topic_label = spec.topic_label
        cluster.representative_article_id = spec.representative_id
        cluster.member_count = len(spec.members)
        cluster.mean_similarity = spec.mean_similarity
        cluster.first_seen_at = spec.first_seen_at
        if cluster.status not in (ClusterStatus.CONFIRMED.value, ClusterStatus.SPLIT.value):
            cluster.status = ClusterStatus.AUTO.value
        db.flush()
        cluster_id_map[spec.representative_id] = cluster.id
        for article_id in spec.members:
            db.add(
                ClusterMember(
                    cluster_id=cluster.id,
                    article_id=article_id,
                    similarity_to_rep=spec.member_similarity.get(article_id, 1.0),
                )
            )
    db.flush()

    # 旧簇无法复用而被删除时，把「事件关联去向」写入审计：确认过的簇与事件仍可追溯。
    removed_clusters = []
    for cluster in orphaned:
        if cluster.id in claimed:
            continue
        old_events = [
            event.id
            for event in db.scalars(select(Event).where(Event.cluster_id == cluster.id)).all()
        ]
        removed_clusters.append(
            {
                "cluster_id": cluster.id,
                "representative_article_id": cluster.representative_article_id,
                "unlinked_event_ids": old_events,
            }
        )
    if removed_clusters:
        audit_service.record(
            db,
            _SYSTEM_ACTOR,
            action="dedup.cluster_replaced",
            target_type="dedup_run",
            target_id=run.id,
            detail={"removed_clusters": removed_clusters},
        )

    db.query(SuspectedEdge).delete()
    for edge in result.suspect_edges:
        db.add(
            SuspectedEdge(
                run_id=run.id,
                article_a_id=edge.article_a_id,
                article_b_id=edge.article_b_id,
                similarity=edge.similarity,
            )
        )

    cross_source = 0
    for spec in result.clusters:
        rep_source = by_id[spec.representative_id].source_id
        for article_id in spec.members:
            if article_id != spec.representative_id and by_id[article_id].source_id != rep_source:
                cross_source += 1

    return {
        "article_count": result.article_count,
        "cluster_count": len(result.clusters),
        "suspect_edge_count": len(result.suspect_edges),
        "duplicate_rate": result.duplicate_rate,
        "cross_source_count": cross_source,
        "candidate_pair_count": result.candidate_pairs,
        "event_relinks": [],
    }


def execute_run(run_id: int) -> None:
    db: Session = SessionLocal()
    try:
        run = db.get(DedupRun, run_id)
        if run is None:
            return
        run.status = DedupRunStatus.RUNNING.value
        run.started_at = datetime.now(timezone.utc)
        db.commit()

        docs = build_docs(db)
        result = run_dedup(docs, _run_params(run))
        stats = _persist(db, run, result, docs)
        relinks = stats.pop("event_relinks", [])
        for key, value in stats.items():
            setattr(run, key, value)
        if relinks:
            audit_service.record(
                db,
                _SYSTEM_ACTOR,
                action="dedup.event_relinked",
                target_type="dedup_run",
                target_id=run.id,
                detail={"relinks": relinks},
            )
        run.snapshot_path = _write_snapshot(run, result)
        run.status = DedupRunStatus.SUCCEEDED.value
        run.finished_at = datetime.now(timezone.utc)
        run.error = ""
        db.commit()
        log_event(
            "dedup.run_succeeded",
            run_id=run.id,
            clusters=stats["cluster_count"],
            suspects=stats["suspect_edge_count"],
            duplicate_rate=stats["duplicate_rate"],
        )
    except Exception as exc:  # noqa: BLE001 - persisted as run.error
        db.rollback()
        run = db.get(DedupRun, run_id)
        if run is not None:
            run.status = DedupRunStatus.FAILED.value
            run.error = f"{type(exc).__name__}: {exc}"
            run.finished_at = datetime.now(timezone.utc)
            db.commit()
        log_event("dedup.run_failed", run_id=run_id, error=str(exc))
        raise
    finally:
        db.close()
