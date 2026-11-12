/** 与后端 backend/src/constants/enums.py 保持一致（共享枚举 2 组：角色 + 业务状态） */
export const SOURCE_TYPE_LABELS: Record<string, string> = {
  media: '同行媒体',
  government: '政府公告',
  selfmedia: '自媒体',
}

export const RAW_STATUS_LABELS: Record<string, string> = {
  new: '待解析',
  parsed: '已抽取',
  failed: '采集失败',
}

export const EXTRACTOR_LABELS: Record<string, string> = {
  readability: '密度抽取',
  fallback: '兜底抽取',
  manual: '人工校正',
}

export const CLUSTER_STATUS_LABELS: Record<string, string> = {
  auto: '自动聚类',
  confirmed: '已确认',
  split: '已拆分',
}

export const DEDUP_STATUS_LABELS: Record<string, string> = {
  queued: '排队中',
  running: '计算中',
  succeeded: '已完成',
  failed: '失败',
}

export const REEXTRACT_BATCH_STATUS_LABELS: Record<string, string> = {
  queued: '排队中',
  running: '重抽中',
  succeeded: '已完成',
  failed: '失败',
  partial: '部分失败',
}

export const REEXTRACT_ITEM_STATUS_LABELS: Record<string, string> = {
  pending: '待重抽',
  running: '重抽中',
  succeeded: '已重抽',
  failed: '重抽失败',
  skipped_manual: '人工校正（跳过）',
}

export const EVENT_CATEGORIES = ['政策', '产业', '民生', '财经'] as const

export const LOW_CONFIDENCE_THRESHOLD = 0.4
export const DEDUP_SIM_THRESHOLD = 0.72
export const DEDUP_SUSPECT_THRESHOLD = 0.55
export const DAILY_DATE = '2026-11-10'
