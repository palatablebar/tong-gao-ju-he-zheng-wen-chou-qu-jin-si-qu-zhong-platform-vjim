<template>
  <div class="reextract-panel" data-testid="reextract-panel">
    <div class="reextract-panel__head">
      <span class="panel__title">按信源重抽</span>
      <span class="panel__meta mono">
        批次汇总 · 成功 / 失败 / 人工校正跳过
      </span>
    </div>

    <div v-if="actionSourceId === null" class="reextract-panel__hint mono">
      在信源清单中选择一个信源，发起正文重抽（仅重算该信源下的抓取记录）。
    </div>

    <div class="reextract-panel__action">
      <span v-if="actionSource" class="mono">
        目标信源：<b>{{ actionSource.name }}</b> · {{ actionSource.raw_count }} 条抓取记录
      </span>
      <span v-else class="mono" style="color: var(--ink-faint)">未选择信源</span>
      <button
        class="btn btn--seal"
        type="button"
        data-testid="start-reextract"
        :disabled="!actionSource || !canReextract || store.busy"
        :title="canReextract ? '按信源重抽正文并在完成后重新去重' : '只读角色无重抽权限（后端 403）'"
        @click="start"
      >
        {{ store.busy ? '重抽中…' : '发起重抽' }}
      </button>
    </div>

    <div v-if="!canReextract" class="reextract-panel__hint mono">
      只读角色：发起重抽 → 403（可查看批次结果与失败项）。
    </div>
    <div v-if="store.error" class="forbidden">{{ store.error }}</div>
    <div v-if="store.busy" class="loading-bar" />

    <template v-if="batch">
      <div class="batch-strip" data-testid="reextract-batch-summary">
        <div class="batch-cell">
          <div class="batch-cell__value">{{ batch.total_count }}</div>
          <div class="batch-cell__label">本批抓取</div>
        </div>
        <div class="batch-cell batch-cell--ok">
          <div class="batch-cell__value">{{ batch.succeeded_count }}</div>
          <div class="batch-cell__label">成功</div>
        </div>
        <div class="batch-cell batch-cell--bad">
          <div class="batch-cell__value">{{ batch.failed_count }}</div>
          <div class="batch-cell__label">失败</div>
        </div>
        <div class="batch-cell batch-cell--skip">
          <div class="batch-cell__value">{{ batch.skipped_count }}</div>
          <div class="batch-cell__label">人工校正跳过</div>
        </div>
        <div class="batch-cell">
          <div class="batch-cell__value">{{ batch.body_changed_count }}</div>
          <div class="batch-cell__label">正文有变化</div>
        </div>
        <div class="batch-cell">
          <div class="batch-cell__value">{{ batch.status_label }}</div>
          <div class="batch-cell__label">
            #{{ batch.id }} · 续跑 {{ batch.attempt_count }} 次
          </div>
        </div>
      </div>

      <div class="batch-meta mono">
        <span>信源：{{ batch.source_name }}</span>
        <span>规则签名 {{ batch.rule_signature }}</span>
        <span v-if="batch.dedup_run_id">
          去重 #{{ batch.dedup_run_id }} · {{ batch.dedup_run?.status_label || '排队中' }}
          <template v-if="batch.dedup_run">
            · {{ batch.dedup_run.cluster_count }} 簇 / 疑似边 {{ batch.dedup_run.suspect_edge_count }}
          </template>
        </span>
        <span v-else>未触发去重</span>
        <span v-if="batch.cursor_raw_item_id">断点 raw#{{ batch.cursor_raw_item_id }}</span>
        <span v-if="batch.deduplicated" class="batch-meta__flag">同规则重复发起 · 复用原批次</span>
      </div>

      <div v-if="batch.error" class="batch-error mono">{{ batch.error }}</div>

      <div class="export-actions" style="margin-bottom: var(--space-2)">
        <button
          v-if="canReextract"
          class="btn btn--ghost"
          type="button"
          data-testid="retry-reextract"
          :disabled="store.busy || !resumable"
          @click="retry"
        >
          重试失败项 / 续跑（{{ resumableCount }}）
        </button>
        <span class="mono" style="color: var(--ink-faint)">
          失败项保留在批次中，续跑从断点继续；已人工校正的稿件不会重算。
        </span>
      </div>

      <div class="item-table">
        <div class="item-row item-row--head mono">
          <span>抓取记录</span>
          <span>结果</span>
          <span>抽取器 / 置信度</span>
          <span>说明</span>
        </div>
        <div
          v-for="item in visibleItems"
          :key="item.id"
          class="item-row"
          :class="`item-row--${item.status}`"
          data-testid="reextract-item"
        >
          <span class="item-row__title">
            <span class="mono" style="color: var(--ink-faint)">#{{ item.raw_item_id }}</span>
            {{ item.title }}
          </span>
          <span class="tag" :class="statusClass(item.status)">{{ item.status_label }}</span>
          <span class="mono">
            <template v-if="item.status === 'skipped_manual'">
              {{ item.after_extractor || 'manual' }} · 未改动
            </template>
            <template v-else-if="item.status === 'failed'">—</template>
            <template v-else>
              {{ item.after_extractor }} · {{ item.after_confidence.toFixed(2) }}
              <b v-if="item.body_changed" style="color: var(--vermilion)">正文已更新</b>
            </template>
          </span>
          <span class="item-row__note">{{ item.error_note || '—' }}</span>
        </div>
      </div>
      <div v-if="!batch.items?.length" class="empty">该信源暂无抓取记录，批次为空。</div>
      <div v-else-if="visibleItems.length === 0" class="empty">当前筛选下没有条目。</div>

      <div class="filter-bar" style="padding-top: var(--space-2)">
        <div class="field">
          <label>结果筛选</label>
          <select v-model="itemFilter" data-testid="reextract-filter">
            <option value="">全部条目</option>
            <option value="failed">只看失败</option>
            <option value="skipped_manual">只看人工校正跳过</option>
            <option value="succeeded">只看成功</option>
          </select>
        </div>
        <span class="mono" style="color: var(--ink-faint); padding-bottom: 0.55rem">
          失败项不会消失 · 人工校正正文不会被覆盖
        </span>
      </div>
    </template>
    <div v-else-if="!store.busy" class="empty">
      尚无重抽批次。选择信源后点击「发起重抽」。
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useReextractStore } from '../../stores/reextract'
import { usePermission } from '../../hooks/usePermission'
import { useToast } from '../../hooks/useToast'
import type { ReextractBatch, ReextractItemStatus, Source } from '../../types'

const props = defineProps<{
  sources: Source[]
  /** 从信源列表行选中的信源（发起重抽的目标） */
  selectedSourceId: number | null
}>()

const store = useReextractStore()
const { canReextract } = usePermission()
const { push, failure } = useToast()

const itemFilter = ref<'' | ReextractItemStatus>('')
const actionSourceId = computed(() => props.selectedSourceId)
const actionSource = computed(
  () => props.sources.find((source) => source.id === actionSourceId.value) || null,
)
const batch = computed<ReextractBatch | null>(() => store.current || store.latest)
const visibleItems = computed(() =>
  (batch.value?.items || []).filter((item) => !itemFilter.value || item.status === itemFilter.value),
)
const resumableCount = computed(() => {
  const value = batch.value
  if (!value) return 0
  return value.failed_count + value.pending_count
})
const resumable = computed(() => resumableCount.value > 0)

onMounted(() => {
  void store.load()
})

watch(
  () => props.selectedSourceId,
  async (sourceId) => {
    if (sourceId === null || store.busy) return
    await store.load(sourceId)
    const existing = store.batches.find((row) => row.source_id === sourceId) || store.latest
    if (existing) {
      await store.selectBatch(existing.id)
    }
  },
  { immediate: true },
)

function statusClass(status: ReextractItemStatus): string {
  if (status === 'failed') return 'tag--ochre'
  if (status === 'skipped_manual') return 'tag--seal'
  if (status === 'succeeded') return 'tag--moss'
  return ''
}

async function start() {
  if (!actionSource.value) return
  const result = await store.request(actionSource.value.id)
  if (!result) {
    failure(store.error || '重抽失败')
    return
  }
  push(
    `重抽完成：成功 ${result.succeeded_count} · 失败 ${result.failed_count} · 人工校正跳过 ${result.skipped_count}；已重新去重`,
  )
}

async function retry() {
  if (!batch.value) return
  const result = await store.retry(batch.value.id)
  if (!result) {
    failure(store.error || '续跑失败')
    return
  }
  push(`续跑完成：成功 ${result.succeeded_count} · 失败 ${result.failed_count} · 跳过 ${result.skipped_count}`)
}
</script>

<style scoped>
.reextract-panel {
  margin-top: var(--space-5);
  border: 1px solid var(--rule);
  background: var(--paper-soft);
  padding: var(--space-4);
}

.reextract-panel__head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  border-bottom: 3px double var(--rule-strong);
  padding-bottom: var(--space-2);
  margin-bottom: var(--space-3);
}

.reextract-panel__hint {
  color: var(--ink-faint);
  font-size: var(--step--1);
  margin-bottom: var(--space-2);
}

.reextract-panel__action {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
  margin-bottom: var(--space-3);
}

.batch-strip {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(96px, 1fr));
  border-top: 1px solid var(--rule);
  border-bottom: 1px solid var(--rule);
  margin-bottom: var(--space-3);
}

.batch-cell {
  padding: var(--space-2) var(--space-3) var(--space-2) 0;
  border-right: 1px dotted var(--rule);
}

.batch-cell:last-child {
  border-right: 0;
}

.batch-cell__value {
  font-family: var(--font-display);
  font-size: var(--step-1);
  line-height: 1.1;
}

.batch-cell--ok .batch-cell__value {
  color: var(--moss, #3f5d43);
}

.batch-cell--bad .batch-cell__value {
  color: var(--vermilion);
}

.batch-cell--skip .batch-cell__value {
  color: var(--ochre, #8a6a25);
}

.batch-cell__label {
  font-family: var(--font-mono);
  font-size: 0.62rem;
  letter-spacing: 0.1em;
  color: var(--ink-faint);
  margin-top: 0.2rem;
}

.batch-meta {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2) var(--space-4);
  font-size: var(--step--1);
  color: var(--ink-soft);
  margin-bottom: var(--space-2);
}

.batch-meta__flag {
  color: var(--vermilion);
}

.batch-error {
  color: var(--vermilion);
  font-size: var(--step--1);
  margin-bottom: var(--space-2);
}

.item-table {
  border-top: 1px solid var(--rule);
}

.item-row {
  display: grid;
  grid-template-columns: 2.2fr 0.9fr 1.3fr 1.6fr;
  gap: var(--space-3);
  align-items: center;
  padding: 0.45rem 0;
  border-bottom: 1px dotted var(--rule);
  font-size: var(--step--1);
}

.item-row--head {
  border-bottom: 3px double var(--rule-strong);
  color: var(--ink-faint);
  font-size: 0.62rem;
  letter-spacing: 0.1em;
}

.item-row--failed {
  background: color-mix(in srgb, var(--vermilion) 6%, transparent);
}

.item-row__title {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.item-row__note {
  color: var(--ink-faint);
}

.tag {
  justify-self: start;
}
</style>
