"""去重簇审查：列表 / 详情 / 确认代表稿 / 拆分 / 合并。

簇内成员相似度由 MinHash 用的同一套归一化 + 4-gram Jaccard 真算，拆分合并后
重新计算 mean_similarity，不在前端伪造数字。
"""
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.config.settings import settings
from src.constants.enums import ClusterStatus
from src.models import Article, Cluster, ClusterMember, SuspectedEdge
from src.services import audit_service, dedup_service, reextract_service
from src.services.dedup import _representative
from src.utils.errors import bad_request, not_found
from src.utils.serializers import cluster_out
from src.utils.textnorm import jaccard, normalize_text, shingles


def _shingle_set(article: Article) -> set[str]:
    return shingles(normalize_text(article.body_text or ""), settings.DEDUP_SHINGLE_SIZE)


def _load_articles(db: Session, article_ids: list[int]) -> dict[int, Article]:
    if not article_ids:
        return {}
    rows = db.scalars(select(Article).where(Article.id.in_(article_ids))).all()
    return {row.id: row for row in rows}


def _recompute(db: Session, cluster: Cluster, member_ids: list[int], rep_id: int | None = None) -> None:
    articles = _load_articles(db, member_ids)
    docs = [dedup_service.article_doc(articles[aid]) for aid in member_ids if aid in articles]
    if not docs:
        cluster.member_count = 0
        cluster.mean_similarity = 0.0
        cluster.representative_article_id = None
        return
    if rep_id is None or rep_id not in {doc.article_id for doc in docs}:
        rep_id = _representative([doc.article_id for doc in docs], {doc.article_id: doc for doc in docs})
    rep_set = _shingle_set(articles[rep_id])
    sims = {}
    for article_id in member_ids:
        if article_id not in articles:
            continue
        sims[article_id] = 1.0 if article_id == rep_id else round(
            jaccard(rep_set, _shingle_set(articles[article_id])), 4
        )
    cluster.representative_article_id = rep_id
    cluster.member_count = len(sims)
    others = [sim for aid, sim in sims.items() if aid != rep_id]
    cluster.mean_similarity = round(sum(others) / len(others), 4) if others else 1.0
    cluster.first_seen_at = min(
        (articles[aid].raw_item.published_at for aid in member_ids if aid in articles),
        default=cluster.first_seen_at,
    )
    cluster.status = ClusterStatus.SPLIT.value if cluster.status == ClusterStatus.SPLIT.value else cluster.status
    db.query(ClusterMember).filter(ClusterMember.cluster_id == cluster.id).delete()
    db.flush()
    for article_id, sim in sims.items():
        db.add(ClusterMember(cluster_id=cluster.id, article_id=article_id, similarity_to_rep=sim))


def _suspect_payload(db: Session, cluster_ids: set[int]) -> list[dict]:
    edges = db.scalars(
        select(SuspectedEdge).where(
            (SuspectedEdge.cluster_a_id.in_(cluster_ids)) | (SuspectedEdge.cluster_b_id.in_(cluster_ids))
        )
    ).all()
    if not edges:
        edges = db.scalars(select(SuspectedEdge)).all()
    article_ids = {edge.article_a_id for edge in edges} | {edge.article_b_id for edge in edges}
    titles = {}
    if article_ids:
        rows = db.scalars(select(Article).where(Article.id.in_(article_ids))).all()
        for row in rows:
            titles[row.id] = row.raw_item.title if row.raw_item else f"#{row.id}"
    return [
        {
            "article_a_id": edge.article_a_id,
            "article_b_id": edge.article_b_id,
            "similarity": round(edge.similarity, 4),
            "title_a": titles.get(edge.article_a_id, ""),
            "title_b": titles.get(edge.article_b_id, ""),
        }
        for edge in edges
    ]


def list_clusters(db: Session, status: str | None = None, q: str | None = None) -> dict:
    query = select(Cluster)
    if status:
        query = query.where(Cluster.status == status)
    if q:
        query = query.where(Cluster.topic_label.ilike(f"%{q}%"))
    clusters = db.scalars(query.order_by(Cluster.member_count.desc(), Cluster.id)).all()
    run = dedup_service.latest_run(db)
    members_total = sum(cluster.member_count for cluster in clusters)
    items = [cluster_out(cluster) for cluster in clusters]
    for item in items:
        item["first_seen_at"] = item["first_seen_at"].isoformat() if item["first_seen_at"] else None
    suspect_edges = _suspect_payload(db, {cluster.id for cluster in clusters})
    return {
        "items": items,
        "total_clusters": len(items),
        "total_members": members_total,
        "run": dedup_service.dedup_run_out(run) if run else None,
        "suspect_edges": suspect_edges,
        "last_reextract": reextract_service.last_reextract_summary(db),
        "reextract_chain": reextract_service.pending_chain(
            db, reextract_service.latest_active(db)
        ),
    }


def get_cluster(db: Session, cluster_id: int) -> dict:
    cluster = db.get(Cluster, cluster_id)
    if cluster is None:
        raise not_found("cluster", cluster_id)
    payload = cluster_out(cluster)
    members = []
    for member in sorted(cluster.members, key=lambda row: (-row.similarity_to_rep, row.article_id)):
        article = member.article
        raw = article.raw_item if article else None
        source = raw.source if raw else None
        members.append(
            {
                "article_id": article.id,
                "title": raw.title if raw else "",
                "source_name": source.name if source else "",
                "source_id": source.id if source else 0,
                "published_at": raw.published_at if raw else None,
                "word_count": article.word_count,
                "similarity_to_rep": round(member.similarity_to_rep, 4),
                "is_representative": article.id == cluster.representative_article_id,
                "extractor": article.extractor,
                "body_text": article.body_text,
                "url": raw.url if raw else "",
                "extract_confidence": round(article.extract_confidence, 4),
            }
        )
    payload["members"] = members
    payload["suspect_edges"] = _suspect_payload(db, {cluster.id})
    payload["first_seen_at"] = payload["first_seen_at"].isoformat() if payload["first_seen_at"] else None
    return payload


def confirm_representative(db: Session, cluster_id: int, payload, actor) -> dict:
    cluster = db.get(Cluster, cluster_id)
    if cluster is None:
        raise not_found("cluster", cluster_id)
    member_ids = [member.article_id for member in cluster.members]
    if payload.representative_article_id not in member_ids:
        raise bad_request("代表稿必须是本簇成员")
    _recompute(db, cluster, member_ids, payload.representative_article_id)
    cluster.status = ClusterStatus.CONFIRMED.value
    audit_service.record(
        db,
        actor,
        action="cluster.confirm",
        target_type="cluster",
        target_id=cluster.id,
        detail={"representative_article_id": payload.representative_article_id, "member_count": cluster.member_count},
    )
    db.commit()
    db.refresh(cluster)
    return get_cluster(db, cluster_id)


def split_cluster(db: Session, cluster_id: int, article_ids: list[int], actor) -> dict:
    cluster = db.get(Cluster, cluster_id)
    if cluster is None:
        raise not_found("cluster", cluster_id)
    member_ids = [member.article_id for member in cluster.members]
    moved = [aid for aid in article_ids if aid in member_ids]
    remaining = [aid for aid in member_ids if aid not in moved]
    if not moved:
        raise bad_request("拆分时至少要移动一名成员")
    if not remaining:
        raise bad_request("不能把全部成员移出，至少保留一篇")
    original_rep = cluster.representative_article_id
    new_cluster = Cluster(
        run_id=cluster.run_id,
        topic_label=f"{cluster.topic_label}（拆分）",
        status=ClusterStatus.AUTO.value,
    )
    db.add(new_cluster)
    db.flush()
    _recompute(db, new_cluster, moved)
    keep_rep = original_rep if original_rep in remaining else None
    _recompute(db, cluster, remaining, keep_rep)
    cluster.status = ClusterStatus.SPLIT.value
    audit_service.record(
        db,
        actor,
        action="cluster.split",
        target_type="cluster",
        target_id=cluster.id,
        detail={"moved_article_ids": moved, "new_cluster_id": new_cluster.id, "remaining": len(remaining)},
    )
    db.commit()
    db.expire_all()
    return {"original": get_cluster(db, cluster.id), "created": get_cluster(db, new_cluster.id)}


def merge_clusters(db: Session, source_cluster_id: int, target_cluster_id: int, actor) -> dict:
    source = db.get(Cluster, source_cluster_id)
    target = db.get(Cluster, target_cluster_id)
    if source is None:
        raise not_found("cluster", source_cluster_id)
    if target is None:
        raise not_found("cluster", target_cluster_id)
    if source.id == target.id:
        raise bad_request("不能把簇合并到自身")
    merged_ids = [member.article_id for member in target.members] + [
        member.article_id for member in source.members
    ]
    audit_service.record(
        db,
        actor,
        action="cluster.merge",
        target_type="cluster",
        target_id=target.id,
        detail={"source_cluster_id": source.id, "merged_member_count": len(merged_ids)},
    )
    db.query(ClusterMember).filter(ClusterMember.cluster_id == source.id).delete()
    db.query(ClusterMember).filter(ClusterMember.cluster_id == target.id).delete()
    db.flush()
    db.delete(source)
    db.flush()
    _recompute(db, target, merged_ids)
    db.commit()
    db.expire_all()
    return get_cluster(db, target.id)
