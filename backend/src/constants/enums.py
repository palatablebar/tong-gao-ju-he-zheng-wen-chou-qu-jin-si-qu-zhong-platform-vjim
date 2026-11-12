"""Shared domain enums. The frontend mirrors these in src/constants/enums.ts."""
from enum import Enum


class SourceType(str, Enum):
    MEDIA = "media"
    GOVERNMENT = "government"
    SELFMEDIA = "selfmedia"


SOURCE_TYPE_LABELS = {
    SourceType.MEDIA.value: "同行媒体",
    SourceType.GOVERNMENT.value: "政府公告",
    SourceType.SELFMEDIA.value: "自媒体",
}


class RawStatus(str, Enum):
    NEW = "new"
    PARSED = "parsed"
    FAILED = "failed"


RAW_STATUS_LABELS = {
    RawStatus.NEW.value: "待解析",
    RawStatus.PARSED.value: "已抽取",
    RawStatus.FAILED.value: "采集失败",
}


class ExtractorMode(str, Enum):
    READABILITY = "readability"
    FALLBACK = "fallback"
    MANUAL = "manual"


EXTRACTOR_LABELS = {
    ExtractorMode.READABILITY.value: "密度抽取",
    ExtractorMode.FALLBACK.value: "兜底抽取",
    ExtractorMode.MANUAL.value: "人工校正",
}


class ClusterStatus(str, Enum):
    AUTO = "auto"
    CONFIRMED = "confirmed"
    SPLIT = "split"


CLUSTER_STATUS_LABELS = {
    ClusterStatus.AUTO.value: "自动聚类",
    ClusterStatus.CONFIRMED.value: "已确认",
    ClusterStatus.SPLIT.value: "已拆分",
}


class DedupRunStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


DEDUP_RUN_STATUS_LABELS = {
    DedupRunStatus.QUEUED.value: "排队中",
    DedupRunStatus.RUNNING.value: "计算中",
    DedupRunStatus.SUCCEEDED.value: "已完成",
    DedupRunStatus.FAILED.value: "失败",
}


class EventCategory(str, Enum):
    POLICY = "政策"
    INDUSTRY = "产业"
    LIVELIHOOD = "民生"
    FINANCE = "财经"


EVENT_CATEGORY_VALUES = [c.value for c in EventCategory]


class ReextractBatchStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    PARTIAL = "partial"


REEXTRACT_BATCH_STATUS_LABELS = {
    ReextractBatchStatus.QUEUED.value: "排队中",
    ReextractBatchStatus.RUNNING.value: "重抽中",
    ReextractBatchStatus.SUCCEEDED.value: "已完成",
    ReextractBatchStatus.FAILED.value: "失败",
    ReextractBatchStatus.PARTIAL.value: "部分失败",
}


class ReextractItemStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    SKIPPED_MANUAL = "skipped_manual"


REEXTRACT_ITEM_STATUS_LABELS = {
    ReextractItemStatus.PENDING.value: "待重抽",
    ReextractItemStatus.RUNNING.value: "重抽中",
    ReextractItemStatus.SUCCEEDED.value: "已重抽",
    ReextractItemStatus.FAILED.value: "重抽失败",
    ReextractItemStatus.SKIPPED_MANUAL.value: "人工校正（跳过）",
}
