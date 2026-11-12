export interface User {
  id: number
  email: string
  display_name: string
  role: RoleKey
  role_label: string
}

export type RoleKey = 'admin' | 'analyst' | 'viewer'

export interface LoginResponse {
  access_token: string
  token_type: string
  user: User
}

export interface Source {
  id: number
  name: string
  homepage: string
  type: SourceType
  type_label: string
  weight: number
  extract_rule_status: 'ok' | 'degraded' | 'pending'
  enabled: boolean
  description: string
  last_fetched_at: string | null
  raw_count: number
  article_count: number
  low_confidence_count: number
}

export type SourceType = 'media' | 'government' | 'selfmedia'

export interface ArticleBrief {
  id: number
  word_count: number
  content_density: number
  extract_confidence: number
  extractor: 'readability' | 'fallback' | 'manual'
  extractor_label: string
}

export interface RawItem {
  id: number
  title: string
  url: string
  published_at: string
  fetched_at: string
  status: 'new' | 'parsed' | 'failed'
  status_label: string
  error_note: string
  source: { id: number; name: string; type: SourceType; type_label: string; weight: number }
  article: ArticleBrief | null
}

export interface CandidateBlock {
  block_id: string
  text: string
  score: number
  tag: string
}

export interface ExtractionPreview {
  top_score: number
  page_chars: number
  body_chars: number
  candidates: CandidateBlock[]
}

export interface ArticleDetail {
  id: number
  raw_item_id: number
  canonical_url: string
  body_text: string
  author: string
  word_count: number
  content_density: number
  extract_confidence: number
  extractor: 'readability' | 'fallback' | 'manual'
  extractor_label: string
  corrected_by: string | null
  corrected_at: string | null
  title: string
  source_name: string
  published_at: string | null
  blocks: string[]
}

export interface RawItemDetail {
  item: RawItem
  raw_html_excerpt: string
  article: ArticleDetail | null
  preview: ExtractionPreview | null
}

export interface RawItemListResponse {
  items: RawItem[]
  total: number
  page: number
  page_size: number
}

export interface ClusterMember {
  article_id: number
  title: string
  source_name: string
  source_id: number
  published_at: string
  word_count: number
  similarity_to_rep: number
  is_representative: boolean
  extractor: string
  body_text: string
  url: string
  extract_confidence: number
}

export interface SuspectEdge {
  article_a_id: number
  article_b_id: number
  similarity: number
  title_a: string
  title_b: string
}

export interface Cluster {
  id: number
  topic_label: string
  member_count: number
  mean_similarity: number
  first_seen_at: string | null
  status: 'auto' | 'confirmed' | 'split'
  status_label: string
  representative_title: string
  representative_source: string
  representative_article_id: number | null
  published_at: string | null
}

export interface ClusterDetail extends Cluster {
  members: ClusterMember[]
  suspect_edges: SuspectEdge[]
}

export interface DedupRun {
  id: number
  status: 'queued' | 'running' | 'succeeded' | 'failed'
  status_label: string
  threshold: number
  suspect_threshold: number
  num_perm: number
  bands: number
  shingle_size: number
  article_count: number
  cluster_count: number
  suspect_edge_count: number
  duplicate_rate: number
  candidate_pair_count: number
  cross_source_count: number
  snapshot_path: string
  triggered_by: string
  error: string
  started_at: string | null
  finished_at: string | null
  created_at: string
}

export interface ClusterListResponse {
  items: Cluster[]
  total_clusters: number
  total_members: number
  run: DedupRun | null
  suspect_edges: SuspectEdge[]
  last_reextract: ReextractBatch | null
  reextract_chain: ReextractBatch | null
}

export type ReextractItemStatus = 'pending' | 'running' | 'succeeded' | 'failed' | 'skipped_manual'

export interface ReextractItem {
  id: number
  batch_id: number
  raw_item_id: number
  article_id: number | null
  title: string
  source_name: string
  status: ReextractItemStatus
  status_label: string
  body_changed: boolean
  before_extractor: string
  before_confidence: number
  after_extractor: string
  after_confidence: number
  error_note: string
  processed_at: string | null
}

export type ReextractBatchStatus = 'queued' | 'running' | 'succeeded' | 'failed' | 'partial'

export interface ReextractBatch {
  id: number
  source_id: number
  source_name: string
  rule_signature: string
  status: ReextractBatchStatus
  status_label: string
  total_count: number
  succeeded_count: number
  failed_count: number
  skipped_count: number
  pending_count: number
  body_changed_count: number
  attempt_count: number
  cursor_raw_item_id: number | null
  dedup_run_id: number | null
  dedup_run: DedupRun | null
  dedup_pending: boolean
  triggered_by: string
  error: string
  created_at: string
  started_at: string | null
  finished_at: string | null
  last_processed_at: string | null
  deduplicated?: boolean
  items?: ReextractItem[]
}

export interface ReextractListResponse {
  items: ReextractBatch[]
  latest: ReextractBatch | null
}

export interface EventItem {
  id: number
  title: string
  category: '政策' | '产业' | '民生' | '财经'
  event_date: string
  region: string
  note: string
  cluster_id: number | null
  cluster_label: string
  member_count: number
  representative_title: string
  representative_source: string
  published_at: string | null
}

export interface TimelineResponse {
  days: Array<{ date: string; events: EventItem[] }>
  total: number
  categories: string[]
}

export interface DailyReport {
  summary: {
    date: string
    event_count: number
    article_count: number
    cluster_count: number
    suspect_count: number
    duplicate_rate: number
  }
  events: EventItem[]
  markdown: string
  last_reextract?: ReextractBatch | null
}

export interface Overview {
  sources: number
  raws: number
  articles: number
  low_confidence: number
  clusters: number
  suspect_edges: number
  events: number
  members: number
  duplicate_rate: number
  last_run: {
    id: number
    status: string
    finished_at: string | null
    article_count: number
    cluster_count: number
    suspect_edge_count: number
    duplicate_rate: number
  } | null
  last_reextract?: ReextractBatch | null
}

export interface AuditLog {
  id: number
  actor_email: string
  actor_role: string
  action: string
  target_type: string
  target_id: string
  detail: Record<string, unknown>
  created_at: string
}
