<template>
  <section>
    <header class="page-head">
      <div>
        <div class="page-head__kicker">02 / Raw Queue</div>
        <h2 class="page-head__title">原文队列 · 正文校正</h2>
        <p class="page-head__lede">
          左侧是抓取到的原始 HTML 片段，右侧是密度抽取（Readability 式）的正文。
          置信度低于 0.40 的稿件进入低置信队列，编辑可合并候选片段后人工校正（extractor 记为 manual）。
        </p>
      </div>
      <div class="page-head__aside">
        <div>QUEUE · {{ store.total }} 条</div>
        <div>当前筛选：{{ filters.low_confidence ? '低置信' : '全部' }}</div>
      </div>
    </header>

    <div class="filter-bar">
      <div class="field">
        <label>状态</label>
        <select v-model="store.filters.status" data-testid="filter-status">
          <option value="">全部</option>
          <option value="new">待解析</option>
          <option value="parsed">已抽取</option>
          <option value="failed">采集失败</option>
        </select>
      </div>
      <div class="field">
        <label>信源</label>
        <select v-model="store.filters.source_id" data-testid="filter-source">
          <option :value="null">全部信源</option>
          <option v-for="source in sources" :key="source.id" :value="source.id">
            {{ source.name }}
          </option>
        </select>
      </div>
      <div class="field">
        <label>标题关键词</label>
        <input v-model="store.filters.q" name="q" data-testid="filter-q" placeholder="运河 / 医保 …" />
      </div>
      <label class="checkline" style="padding-bottom: 0.55rem">
        <input v-model="store.filters.low_confidence" type="checkbox" data-testid="filter-low" />
        只看低置信
      </label>
      <button class="btn" type="button" data-testid="apply-filter" @click="applyFilters">刷新队列</button>
    </div>

    <div v-if="store.loading" class="loading-bar" />
    <div v-if="store.error" class="forbidden">{{ store.error }}</div>

    <div class="split-layout split-layout--wide-left">
      <div class="panel panel--flush">
        <div class="panel__head" style="padding: var(--space-3) var(--space-4) 0">
          <span class="panel__title">抓取记录</span>
          <span class="panel__meta">按发布时间倒序</span>
        </div>
        <ul class="row-list" style="padding: 0 var(--space-2) var(--space-2)">
          <li
            v-for="item in store.items"
            :key="item.id"
            class="row"
            :class="{ 'is-active': store.detail?.item.id === item.id }"
            data-testid="raw-row"
            @click="selectItem(item.id)"
          >
            <div class="row__title">{{ item.title }}</div>
            <div class="row__meta">
              <span>{{ item.source.name }}</span>
              <span>{{ formatDateTime(item.published_at) }}</span>
              <span class="tag" :class="item.status === 'failed' ? 'tag--ochre' : item.status === 'new' ? '' : 'tag--moss'">
                {{ item.status_label }}
              </span>
              <span
                v-if="item.article"
                class="mono"
                :style="{ color: item.article.extract_confidence < 0.4 ? 'var(--vermilion)' : 'var(--ink-faint)' }"
              >
                conf {{ formatConfidence(item.article.extract_confidence) }} ·
                {{ item.article.extractor_label }}
              </span>
            </div>
          </li>
        </ul>
        <div v-if="!store.items.length && !store.loading" class="empty" style="margin: var(--space-3)">
          当前筛选下没有抓取记录。清空「只看低置信」或切换状态再试。
        </div>
      </div>

      <div class="panel">
        <template v-if="detail">
          <div class="panel__head">
            <span class="panel__title">{{ detail.item.title }}</span>
            <span class="panel__meta">{{ detail.item.source.name }} · {{ formatDateTime(detail.item.published_at) }}</span>
          </div>
          <div class="detail-meta">
            <span>{{ detail.item.status_label }}</span>
            <span>{{ detail.article?.extractor_label || '未抽取' }}</span>
            <span v-if="detail.article">confidence {{ formatConfidence(detail.article.extract_confidence) }}</span>
            <span v-if="detail.article">density {{ (detail.article.content_density * 100).toFixed(1) }}%</span>
            <span v-if="detail.article">{{ detail.article.word_count }} 字</span>
            <span v-if="detail.article?.corrected_by">校正人 {{ detail.article.corrected_by }}</span>
            <a :href="detail.item.url" target="_blank" rel="noreferrer">原链接 ↗</a>
          </div>

          <div v-if="detail.item.status === 'failed'" class="forbidden" style="margin-bottom: var(--space-3)">
            采集失败：{{ detail.item.error_note }}。该记录未产出正文，可在信源台账升级抽取规则后重试。
          </div>

          <BodyDiffPanel
            v-if="detail.article"
            mode="correct"
            left-title="原始 HTML 片段"
            :left-text="rawExcerpt"
            right-title="抽取正文（可编辑）"
            :right-text="detail.article.body_text"
            :editable="canCorrect"
            :saving="saving"
            :candidates="detail.preview?.candidates || []"
            @save="saveCorrection"
          />
          <div v-else class="empty">该抓取记录状态为「{{ detail.item.status_label }}」，暂无抽取正文。</div>
        </template>
        <div v-else class="empty">从左侧队列选择一条抓取记录，查看原始片段与抽取正文。</div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRawItemStore } from '../stores/rawItems'
import { useSourceStore } from '../stores/sources'
import { usePermission } from '../hooks/usePermission'
import { useToast } from '../hooks/useToast'
import { formatConfidence, formatDateTime } from '../utils/format'
import BodyDiffPanel from '../components/common/BodyDiffPanel.vue'

const store = useRawItemStore()
const sourceStore = useSourceStore()
const { canCorrect } = usePermission()
const { push, failure } = useToast()

const sources = computed(() => sourceStore.items)
const detail = computed(() => store.detail)
const filters = store.filters
const saving = ref(false)
const rawExcerpt = computed(() => {
  const html = detail.value?.raw_html_excerpt || ''
  return html.length > 1400 ? `${html.slice(0, 1400)}…` : html
})

onMounted(async () => {
  await Promise.all([sourceStore.load(), store.load()])
  if (!store.detail && store.items.length) {
    await selectItem(store.items[0].id)
  }
})

async function applyFilters() {
  store.filters.page = 1
  await store.load()
  if (store.items.length && !store.detail) {
    await selectItem(store.items[0].id)
  }
}

async function selectItem(rawItemId: number) {
  await store.loadDetail(rawItemId)
}

async function saveCorrection(body: string) {
  if (!detail.value?.article?.id) return
  saving.value = true
  try {
    await store.correct(detail.value.article.id, body, '原文队列人工校正')
    push('正文已校正，extractor=manual，审计日志已记录')
  } catch (exc) {
    failure(exc)
  } finally {
    saving.value = false
  }
}
</script>
