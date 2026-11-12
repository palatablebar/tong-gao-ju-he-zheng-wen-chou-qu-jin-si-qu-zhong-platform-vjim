"""ORM rows → API dictionaries (labels resolved from the shared enums)."""
from src.constants.enums import (
    CLUSTER_STATUS_LABELS,
    DEDUP_RUN_STATUS_LABELS,
    EVENT_CATEGORY_VALUES,
    EXTRACTOR_LABELS,
    RAW_STATUS_LABELS,
    REEXTRACT_BATCH_STATUS_LABELS,
    REEXTRACT_ITEM_STATUS_LABELS,
    SOURCE_TYPE_LABELS,
)
from src.constants.roles import ROLE_LABELS


def user_out(user) -> dict:
    return {
        "id": user.id,
        "email": user.email,
        "display_name": user.display_name,
        "role": user.role,
        "role_label": ROLE_LABELS.get(user.role, user.role),
    }


def source_out(row, counts: dict | None = None) -> dict:
    counts = counts or {}
    return {
        "id": row.id,
        "name": row.name,
        "homepage": row.homepage,
        "type": row.type,
        "type_label": SOURCE_TYPE_LABELS.get(row.type, row.type),
        "weight": row.weight,
        "extract_rule_status": row.extract_rule_status,
        "enabled": row.enabled,
        "description": row.description,
        "last_fetched_at": row.last_fetched_at,
        "raw_count": counts.get("raw_count", 0),
        "article_count": counts.get("article_count", 0),
        "low_confidence_count": counts.get("low_confidence_count", 0),
    }


def article_brief(article) -> dict:
    return {
        "id": article.id,
        "word_count": article.word_count,
        "content_density": round(article.content_density, 4),
        "extract_confidence": round(article.extract_confidence, 4),
        "extractor": article.extractor,
        "extractor_label": EXTRACTOR_LABELS.get(article.extractor, article.extractor),
    }


def article_out(article) -> dict:
    raw = article.raw_item
    source = raw.source if raw else None
    return {
        "id": article.id,
        "raw_item_id": article.raw_item_id,
        "canonical_url": article.canonical_url,
        "body_text": article.body_text,
        "author": article.author,
        "word_count": article.word_count,
        "content_density": round(article.content_density, 4),
        "extract_confidence": round(article.extract_confidence, 4),
        "extractor": article.extractor,
        "extractor_label": EXTRACTOR_LABELS.get(article.extractor, article.extractor),
        "corrected_by": article.corrected_by,
        "corrected_at": article.corrected_at,
        "title": raw.title if raw else "",
        "source_name": source.name if source else "",
        "published_at": raw.published_at if raw else None,
    }


def raw_item_out(raw) -> dict:
    source = raw.source
    article = getattr(raw, "article", None)
    return {
        "id": raw.id,
        "title": raw.title,
        "url": raw.url,
        "published_at": raw.published_at,
        "fetched_at": raw.fetched_at,
        "status": raw.status,
        "status_label": RAW_STATUS_LABELS.get(raw.status, raw.status),
        "error_note": raw.error_note,
        "source": {
            "id": source.id,
            "name": source.name,
            "type": source.type,
            "type_label": SOURCE_TYPE_LABELS.get(source.type, source.type),
            "weight": source.weight,
        },
        "article": article_brief(article) if article else None,
    }


def cluster_out(cluster) -> dict:
    rep = None
    for member in cluster.members:
        if member.article_id == cluster.representative_article_id:
            rep = member.article
            break
    rep_source = ""
    published_at = None
    rep_title = ""
    if rep is not None:
        rep_title = rep.raw_item.title if rep.raw_item else ""
        rep_source = rep.raw_item.source.name if rep.raw_item and rep.raw_item.source else ""
        published_at = rep.raw_item.published_at if rep.raw_item else None
    return {
        "id": cluster.id,
        "topic_label": cluster.topic_label,
        "member_count": cluster.member_count,
        "mean_similarity": round(cluster.mean_similarity, 4),
        "first_seen_at": cluster.first_seen_at,
        "status": cluster.status,
        "status_label": CLUSTER_STATUS_LABELS.get(cluster.status, cluster.status),
        "representative_title": rep_title,
        "representative_source": rep_source,
        "representative_article_id": cluster.representative_article_id,
        "published_at": published_at,
    }


def event_out(event, cluster=None) -> dict:
    rep_title = ""
    rep_source = ""
    published_at = None
    member_count = 0
    if cluster is not None:
        member_count = cluster.member_count
        for member in cluster.members:
            if member.article_id == cluster.representative_article_id:
                article = member.article
                if article and article.raw_item:
                    rep_title = article.raw_item.title
                    rep_source = article.raw_item.source.name if article.raw_item.source else ""
                    published_at = article.raw_item.published_at
                break
    return {
        "id": event.id,
        "title": event.title,
        "category": event.category,
        "event_date": event.event_date,
        "region": event.region,
        "note": event.note,
        "cluster_id": event.cluster_id,
        "cluster_label": cluster.topic_label if cluster else "",
        "member_count": member_count,
        "representative_title": rep_title,
        "representative_source": rep_source,
        "published_at": published_at,
        "category_options": EVENT_CATEGORY_VALUES,
    }


def dedup_run_out(run) -> dict:
    return {
        "id": run.id,
        "status": run.status,
        "status_label": DEDUP_RUN_STATUS_LABELS.get(run.status, run.status),
        "threshold": run.threshold,
        "suspect_threshold": run.suspect_threshold,
        "num_perm": run.num_perm,
        "bands": run.bands,
        "shingle_size": run.shingle_size,
        "article_count": run.article_count,
        "cluster_count": run.cluster_count,
        "suspect_edge_count": run.suspect_edge_count,
        "duplicate_rate": run.duplicate_rate,
        "candidate_pair_count": run.candidate_pair_count,
        "cross_source_count": run.cross_source_count,
        "snapshot_path": run.snapshot_path,
        "triggered_by": run.triggered_by,
        "error": run.error,
        "started_at": run.started_at,
        "finished_at": run.finished_at,
        "created_at": run.created_at,
    }


def reextract_batch_out(batch, dedup_run=None) -> dict:
    """Batch counters are always the persisted totals (no silent failures)."""
    return {
        "id": batch.id,
        "source_id": batch.source_id,
        "source_name": batch.source.name if batch.source else "",
        "rule_signature": batch.rule_signature,
        "status": batch.status,
        "status_label": REEXTRACT_BATCH_STATUS_LABELS.get(batch.status, batch.status),
        "total_count": batch.total_count,
        "succeeded_count": batch.succeeded_count,
        "failed_count": batch.failed_count,
        "skipped_count": batch.skipped_count,
        "pending_count": batch.pending_count,
        "body_changed_count": batch.body_changed_count,
        "attempt_count": batch.attempt_count,
        "cursor_raw_item_id": batch.cursor_raw_item_id,
        "dedup_run_id": batch.dedup_run_id,
        "dedup_run": dedup_run,
        "dedup_pending": bool(batch.dedup_run_id) and dedup_run is not None
        and dedup_run.get("status") in ("queued", "running"),
        "triggered_by": batch.triggered_by,
        "error": batch.error,
        "created_at": batch.created_at,
        "started_at": batch.started_at,
        "finished_at": batch.finished_at,
        "last_processed_at": batch.last_processed_at,
    }


def reextract_item_out(item, raw=None) -> dict:
    raw = raw or getattr(item, "raw_item", None)
    return {
        "id": item.id,
        "batch_id": item.batch_id,
        "raw_item_id": item.raw_item_id,
        "article_id": item.article_id,
        "title": raw.title if raw else "",
        "source_name": raw.source.name if raw and raw.source else "",
        "status": item.status,
        "status_label": REEXTRACT_ITEM_STATUS_LABELS.get(item.status, item.status),
        "body_changed": item.body_changed,
        "before_extractor": item.before_extractor,
        "before_confidence": round(item.before_confidence or 0.0, 4),
        "after_extractor": item.after_extractor,
        "after_confidence": round(item.after_confidence or 0.0, 4),
        "error_note": item.error_note,
        "processed_at": item.processed_at,
    }
