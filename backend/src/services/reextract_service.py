"""按信源发起正文重抽：批次编排、断点续跑、人工校正保护、完成后再去重。

语义（对应验收要求）：
  * 每个信源 + 抽取规则签名对应一个批次（``request_key`` 唯一）。同一规则下重复
    发起返回同一批，不新增任务；规则更新后签名变化才开新批次。
  * ``skipped_manual``：``extractor=manual`` 或 ``corrected_by`` 非空的稿件永不被覆盖，
    在批次内单列为「因人工校正跳过」。
  * 失败项落库为 ``failed`` 并保留 ``error_note``；重试时从 pending / failed /
    中断在 running 的项继续跑（断点由 ``cursor_raw_item_id`` + 逐项提交保证）。
  * 批次主体完成后自动发起一次去重（``dedup_run_id``），簇按代表稿原地更新，
    Event.cluster_id 关联与已确认簇状态保持不变（见 dedup_service._persist）。
  * 结果在簇审查与日报里通过 ``last_reextract`` / ``reextract_chain`` 展示。
"""
import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.config.database import SessionLocal
from src.config.settings import settings
from src.constants.enums import (
    ReextractBatchStatus,
    ReextractItemStatus,
    RawStatus,
)
from src.constants.error_codes import AppError, ErrorCode
from src.models import Article, RawItem, ReextractBatch, ReextractItem, Source
from src.services import audit_service, dedup_service, extraction_service
from src.utils.logger import log_event
from src.utils.serializers import reextract_batch_out, reextract_item_out

WAITING_STATUSES = {ReextractBatchStatus.QUEUED.value, ReextractBatchStatus.RUNNING.value}
RETRYABLE_STATUSES = {
    ReextractItemStatus.PENDING.value,
    ReextractItemStatus.FAILED.value,
    ReextractItemStatus.RUNNING.value,
}


def rule_signature(source: Source | None = None) -> str:
    """抽取规则签名：全局算法阈值 + 信源规则状态；变更后才允许开启新批次。"""
    payload = "|".join(
        [
            "algorithm-a:v1",
            f"divisor={settings.EXTRACT_SCORE_DIVISOR}",
            f"min_body={settings.EXTRACT_MIN_BODY_CHARS}",
            f"source_rule={getattr(source, 'extract_rule_status', 'ok')}",
        ]
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def build_request_key(source_id: int, signature: str | None = None) -> str:
    return f"source:{source_id}:rule:{signature or rule_signature()}"


def _batch_scope(db: Session, source_id: int):
    """该信源下需要覆盖的抓取记录：所有已落库的 raw_items（含失败与待解析）。"""
    return (
        select(RawItem)
        .where(RawItem.source_id == source_id)
        .order_by(RawItem.id)
    )


def _count_items(db: Session, batch: ReextractBatch) -> dict[str, int]:
    rows = db.execute(
        select(ReextractItem.status, func.count(ReextractItem.id))
        .where(ReextractItem.batch_id == batch.id)
        .group_by(ReextractItem.status)
    ).all()
    counts = {status: count for status, count in rows}
    return {
        "total": sum(counts.values()),
        "succeeded": counts.get(ReextractItemStatus.SUCCEEDED.value, 0),
        "failed": counts.get(ReextractItemStatus.FAILED.value, 0),
        "skipped": counts.get(ReextractItemStatus.SKIPPED_MANUAL.value, 0),
        "pending": counts.get(ReextractItemStatus.PENDING.value, 0)
        + counts.get(ReextractItemStatus.RUNNING.value, 0),
    }


def refresh_counts(db: Session, batch: ReextractBatch) -> None:
    counts = _count_items(db, batch)
    batch.total_count = counts["total"]
    batch.succeeded_count = counts["succeeded"]
    batch.failed_count = counts["failed"]
    batch.skipped_count = counts["skipped"]
    batch.pending_count = counts["pending"]
    batch.body_changed_count = (
        db.scalar(
            select(func.count(ReextractItem.id)).where(
                ReextractItem.batch_id == batch.id,
                ReextractItem.body_changed.is_(True),
            )
        )
        or 0
    )


def _seed_items(db: Session, batch: ReextractBatch, raws: list[RawItem]) -> None:
    """Create one item per raw item; manual-corrected rows are recorded as skipped."""
    for raw in raws:
        article = db.scalar(select(Article).where(Article.raw_item_id == raw.id))
        item = ReextractItem(
            batch_id=batch.id,
            raw_item_id=raw.id,
            article_id=article.id if article else None,
            before_extractor=article.extractor if article else "",
            before_confidence=article.extract_confidence if article else 0.0,
        )
        if extraction_service.is_manual_corrected(article):
            item.status = ReextractItemStatus.SKIPPED_MANUAL.value
            item.after_extractor = article.extractor
            item.after_confidence = article.extract_confidence
            item.error_note = "已有编辑人工校正，自动重抽不覆盖"
            item.processed_at = datetime.now(timezone.utc)
        db.add(item)
    # autoflush 关闭：先落库再统计，保证批次汇总与审计日志不是 0。
    db.flush()


def request_batch(db: Session, source_id: int, actor) -> dict:
    """幂等发起：同一信源 + 同一规则签名始终复用同一个批次。"""
    source = db.get(Source, source_id)
    if source is None:
        raise AppError(ErrorCode.NOT_FOUND, f"记录不存在：source#{source_id}")

    signature = rule_signature(source)
    request_key = build_request_key(source_id, signature)
    batch = db.scalar(
        select(ReextractBatch).where(ReextractBatch.request_key == request_key)
    )
    raws = list(db.scalars(_batch_scope(db, source_id)).all())
    is_new_batch = batch is None
    if is_new_batch:
        batch = ReextractBatch(
            source_id=source_id,
            request_key=request_key,
            rule_signature=signature,
            status=ReextractBatchStatus.QUEUED.value,
            triggered_by=actor.email,
        )
        db.add(batch)
        db.flush()
    elif batch.status in WAITING_STATUSES:
        # 已在重抽中：同一批次直接返回，不重复投递任务。
        payload = get_batch(db, batch.id)
        payload["deduplicated"] = True
        return payload

    # 批次内只补录尚未入批的抓取记录：重复发起不重复建任务。
    known = {
        row[0]
        for row in db.execute(
            select(ReextractItem.raw_item_id).where(ReextractItem.batch_id == batch.id)
        ).all()
    } if not is_new_batch else set()
    new_raws = [raw for raw in raws if raw.id not in known]
    added = False
    if new_raws:
        _seed_items(db, batch, new_raws)
        refresh_counts(db, batch)
        added = True
        # 规则未变但批次后又采集到新记录：回到排队态，只补跑新记录。
        batch.status = ReextractBatchStatus.QUEUED.value
        batch.finished_at = None
        batch.error = ""

    if is_new_batch or added:
        audit_service.record(
            db,
            actor,
            action="reextract.batch_requested",
            target_type="reextract_batch",
            target_id=batch.id,
            detail={
                "source_id": source_id,
                "source_name": source.name,
                "rule_signature": signature,
                "total": batch.total_count,
                "skipped_manual": batch.skipped_count,
            },
        )
    db.commit()
    db.refresh(batch)

    dispatched = False
    if is_new_batch or (added and batch.pending_count > 0 and batch.status not in WAITING_STATUSES):
        log_event(
            "reextract.batch_created",
            batch_id=batch.id,
            source_id=source_id,
            by=actor.email,
            total=batch.total_count,
        )
        _dispatch(batch.id)
        dispatched = True

    if dispatched:
        # Inline execution (broker down) wrote through a different session; drop stale
        # identity-map state so the response reflects the persisted counters.
        db.expire_all()
    payload = get_batch(db, batch.id)
    payload["deduplicated"] = not dispatched
    return payload


def _dispatch(batch_id: int) -> None:
    try:
        from src.tasks.reextract_task import run_reextract_task

        run_reextract_task.delay(batch_id)
    except Exception as exc:  # noqa: BLE001 - broker down: run inline, never silently drop
        log_event("reextract.broker_unavailable", batch_id=batch_id, error=str(exc))
        execute_batch(batch_id)


def retry_batch(db: Session, batch_id: int, actor) -> dict:
    """Resume from the failure point: pending / failed / interrupted items only."""
    batch = db.get(ReextractBatch, batch_id)
    if batch is None:
        raise AppError(ErrorCode.NOT_FOUND, f"记录不存在：reextract_batch#{batch_id}")
    if batch.status in WAITING_STATUSES:
        raise AppError(ErrorCode.CONFLICT, "该批次仍在重抽中，请等待完成")

    scope = list(db.scalars(_batch_scope(db, batch.source_id)).all())
    known_ids = {
        row[0]
        for row in db.execute(
            select(ReextractItem.raw_item_id).where(ReextractItem.batch_id == batch.id)
        ).all()
    }
    # 新落库的抓取记录（批次创建之后才采集到）也纳入本次重抽。
    new_raws = [raw for raw in scope if raw.id not in known_ids]
    if new_raws:
        _seed_items(db, batch, new_raws)

    reset = (
        db.query(ReextractItem)
        .filter(
            ReextractItem.batch_id == batch.id,
            ReextractItem.status.in_(sorted(RETRYABLE_STATUSES)),
        )
        .update({ReextractItem.status: ReextractItemStatus.PENDING.value}, synchronize_session=False)
    )
    db.flush()
    refresh_counts(db, batch)
    if reset == 0 and not new_raws:
        # Nothing left to resume: the same batch is not re-run, no new task or cluster.
        db.commit()
        return get_batch(db, batch.id)
    batch.status = ReextractBatchStatus.QUEUED.value
    batch.error = ""
    batch.attempt_count = (batch.attempt_count or 0) + 1
    batch.finished_at = None
    refresh_counts(db, batch)
    audit_service.record(
        db,
        actor,
        action="reextract.batch_retried",
        target_type="reextract_batch",
        target_id=batch.id,
        detail={"requeued_items": reset},
    )
    db.commit()
    db.refresh(batch)
    log_event("reextract.batch_retried", batch_id=batch.id, requeued=reset, by=actor.email)
    _dispatch(batch.id)
    db.expire_all()
    return get_batch(db, batch.id)


def process_item(db: Session, item: ReextractItem, raw: RawItem) -> str:
    """Re-extract one row; returns the final item status. Never overwrites manual bodies."""
    item.status = ReextractItemStatus.RUNNING.value
    db.flush()
    article = db.scalar(select(Article).where(Article.raw_item_id == raw.id))
    if extraction_service.is_manual_corrected(article):
        item.status = ReextractItemStatus.SKIPPED_MANUAL.value
        item.article_id = article.id
        item.after_extractor = article.extractor
        item.after_confidence = article.extract_confidence
        item.error_note = "已有编辑人工校正，自动重抽不覆盖"
        item.processed_at = datetime.now(timezone.utc)
        return item.status

    before_body = (article.body_text if article is not None else "") or ""
    try:
        if not (raw.raw_html or "").strip():
            raise ValueError("抓取页无原始 HTML，无法重抽")
        result = extraction_service.run_extractor(raw.raw_html)
        item.article_id = article.id if article else None
        item.after_extractor = result.extractor
        item.after_confidence = result.extract_confidence
        if not result.body_text:
            item.status = ReextractItemStatus.FAILED.value
            item.error_note = "重抽后正文为空（低于兜底阈值）"
            raw.status = RawStatus.FAILED.value
            raw.error_note = raw.error_note or item.error_note
            item.processed_at = datetime.now(timezone.utc)
            return item.status

        article = extraction_service.apply_result(db, raw, article, result)
        item.article_id = article.id
        # 「有变化」以正文内容为准：新抽出正文、或正文被重抽改写都算变化。
        item.body_changed = before_body.strip() != (result.body_text or "").strip()
        item.status = ReextractItemStatus.SUCCEEDED.value
        item.error_note = ""
        item.processed_at = datetime.now(timezone.utc)
        raw.error_note = ""
        return item.status
    except Exception as exc:  # noqa: BLE001 - failure is recorded, not swallowed
        db.rollback()
        item = db.get(ReextractItem, item.id)
        item.status = ReextractItemStatus.FAILED.value
        item.error_note = f"{type(exc).__name__}: {exc}"[:255]
        item.processed_at = datetime.now(timezone.utc)
        db.commit()
        return item.status


def _finalize(db: Session, batch: ReextractBatch) -> None:
    refresh_counts(db, batch)
    if batch.failed_count:
        batch.status = (
            ReextractBatchStatus.PARTIAL.value
            if batch.succeeded_count or batch.skipped_count
            else ReextractBatchStatus.FAILED.value
        )
        batch.error = f"{batch.failed_count} 条重抽失败，可重试续跑"
    else:
        batch.status = ReextractBatchStatus.SUCCEEDED.value
        batch.error = ""
    batch.finished_at = datetime.now(timezone.utc)
    db.commit()


def execute_batch(batch_id: int) -> None:
    """Run (or resume) a batch with per-item commits so a crash keeps its progress."""
    db: Session = SessionLocal()
    try:
        batch = db.get(ReextractBatch, batch_id)
        if batch is None:
            return
        if batch.status not in WAITING_STATUSES:
            # Only an explicitly queued batch (first request / retry) may run. A re-delivered
            # task for a finished batch must not create another dedup run or clusters.
            return
        if batch.pending_count == 0 and not batch.failed_count:
            # Nothing to run (e.g. all items are manual skips): finalize without a dedup run.
            _finalize(db, batch)
            return
        batch.status = ReextractBatchStatus.RUNNING.value
        batch.started_at = batch.started_at or datetime.now(timezone.utc)
        batch.finished_at = None
        db.commit()

        pending = db.scalars(
            select(ReextractItem)
            .where(
                ReextractItem.batch_id == batch.id,
                ReextractItem.status.in_(sorted(RETRYABLE_STATUSES)),
            )
            .order_by(ReextractItem.raw_item_id)
        ).all()
        processed_any = False
        failed_only = True
        for item in pending:
            if item.status == ReextractItemStatus.FAILED.value:
                # retry explictly resets failed rows to pending; stray failed rows are retried
                item.status = ReextractItemStatus.PENDING.value
            raw = db.get(RawItem, item.raw_item_id)
            if raw is None:
                item.status = ReextractItemStatus.FAILED.value
                item.error_note = "抓取记录已不存在"
                item.processed_at = datetime.now(timezone.utc)
                db.commit()
                continue
            status = process_item(db, item, raw)
            processed_any = True
            if status in (
                ReextractItemStatus.SUCCEEDED.value,
                ReextractItemStatus.SKIPPED_MANUAL.value,
            ):
                failed_only = False
            batch.cursor_raw_item_id = item.raw_item_id
            batch.last_processed_at = datetime.now(timezone.utc)
            refresh_counts(db, batch)
            db.commit()

        _finalize(db, batch)
        log_event(
            "reextract.batch_finished",
            batch_id=batch.id,
            status=batch.status,
            succeeded=batch.succeeded_count,
            failed=batch.failed_count,
            skipped=batch.skipped_count,
        )

        if processed_any and not failed_only:
            # 有成功重抽才重新去重；全部失败时保留原有簇与事件关联。
            _trigger_dedup(db, batch)
    except Exception as exc:  # noqa: BLE001 - persisted as batch.error
        db.rollback()
        batch = db.get(ReextractBatch, batch_id)
        if batch is not None:
            batch.status = ReextractBatchStatus.FAILED.value
            batch.error = f"{type(exc).__name__}: {exc}"
            batch.finished_at = datetime.now(timezone.utc)
            refresh_counts(db, batch)
            db.commit()
        log_event("reextract.batch_failed", batch_id=batch_id, error=str(exc))
        raise
    finally:
        db.close()


def _trigger_dedup(db: Session, batch: ReextractBatch) -> None:
    """Re-dedup after re-extraction; reuse an in-flight run instead of creating duplicates."""
    from src.models import DedupRun

    active = db.scalar(
        select(DedupRun).where(DedupRun.status.in_(["queued", "running"]))
    )
    if active is not None:
        batch.dedup_run_id = active.id
        db.commit()
        return
    run = dedup_service.request_run(
        db,
        _DedupPayload(settings.DEDUP_SIM_THRESHOLD, settings.DEDUP_SUSPECT_THRESHOLD),
        _SystemActor(f"system:reextract#{batch.id}"),
    )
    batch.dedup_run_id = run["id"]
    db.commit()


@dataclass
class _DedupPayload:
    threshold: float
    suspect_threshold: float


@dataclass
class _SystemActor:
    email: str
    role: str = "system"


def get_batch(db: Session, batch_id: int) -> dict:
    batch = db.get(ReextractBatch, batch_id)
    if batch is None:
        raise AppError(ErrorCode.NOT_FOUND, f"记录不存在：reextract_batch#{batch_id}")
    batch_run = None
    if batch.dedup_run_id:
        batch_run = dedup_service.get_run(db, batch.dedup_run_id)
    payload = reextract_batch_out(batch, batch_run)
    payload["items"] = [
        reextract_item_out(item, item.raw_item) for item in batch.items
    ]
    return payload


def list_batches(db: Session, source_id: int | None = None, limit: int = 10) -> dict:
    query = select(ReextractBatch)
    if source_id:
        query = query.where(ReextractBatch.source_id == source_id)
    rows = db.scalars(query.order_by(ReextractBatch.id.desc()).limit(limit)).all()
    items = []
    for batch in rows:
        run = dedup_service.get_run(db, batch.dedup_run_id) if batch.dedup_run_id else None
        items.append(reextract_batch_out(batch, run))
    latest = _latest_finished(db, source_id) if source_id else _latest_finished(db)
    return {
        "items": items,
        "latest": reextract_batch_out(latest, dedup_service.get_run(db, latest.dedup_run_id)
                                      if latest and latest.dedup_run_id else None)
        if latest
        else None,
    }


def _latest_finished(db: Session, source_id: int | None = None) -> ReextractBatch | None:
    query = select(ReextractBatch).where(
        ReextractBatch.status.in_(
            [
                ReextractBatchStatus.SUCCEEDED.value,
                ReextractBatchStatus.PARTIAL.value,
                ReextractBatchStatus.FAILED.value,
            ]
        )
    )
    if source_id:
        query = query.where(ReextractBatch.source_id == source_id)
    return db.scalar(query.order_by(ReextractBatch.id.desc()).limit(1))


# ---- 供其他页面（簇审查 / 日报）等待「重抽 → 去重」链路 ----------------------


def pending_chain(db: Session, batch) -> dict | None:
    """Return a light summary while a batch or its downstream dedup is still running."""
    if batch is None:
        return None
    if batch.status in WAITING_STATUSES:
        return reextract_batch_out(batch, None)
    if batch.dedup_run_id:
        from src.models import DedupRun

        run = db.get(DedupRun, batch.dedup_run_id)
        if run is not None and run.status in ("queued", "running"):
            return reextract_batch_out(batch, dedup_service.dedup_run_out(run))
    return None


def latest_active(db: Session) -> ReextractBatch | None:
    return db.scalar(select(ReextractBatch).order_by(ReextractBatch.id.desc()).limit(1))


def last_reextract_summary(db: Session) -> dict | None:
    """Cross-page summary (cluster desk / daily) of the most recent re-extraction batch."""
    batch = _latest_finished(db)
    if batch is None:
        return None
    run = dedup_service.get_run(db, batch.dedup_run_id) if batch.dedup_run_id else None
    return reextract_batch_out(batch, run)
