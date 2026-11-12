<template>
  <section>
    <header class="page-head">
      <div>
        <div class="page-head__kicker">01 / Source Ledger</div>
        <h2 class="page-head__title">信源台账</h2>
        <p class="page-head__lede">
          20 个同行站 + 8 个政务号里已接入 5 个核心信源。抽取规则状态决定该站正文的兜底策略，
          权重参与代表稿打分（0.2 权重项）。
        </p>
      </div>
      <div class="page-head__aside">
        <div>DESK · 采集组</div>
        <div>{{ sources.length }} 个信源 · {{ enabledCount }} 个启用</div>
      </div>
    </header>

    <div class="stat-strip">
      <div class="stat">
        <div class="stat__value">{{ sources.length }}<span>个</span></div>
        <div class="stat__label">在监信源</div>
      </div>
      <div class="stat">
        <div class="stat__value">{{ sumBy('raw_count') }}<span>条</span></div>
        <div class="stat__label">抓取原文</div>
      </div>
      <div class="stat">
        <div class="stat__value">{{ sumBy('article_count') }}<span>篇</span></div>
        <div class="stat__label">抽取正文</div>
      </div>
      <div class="stat">
        <div class="stat__value" style="color: var(--vermilion)">
          {{ sumBy('low_confidence_count') }}<span>篇</span>
        </div>
        <div class="stat__label">低置信待校正</div>
      </div>
      <div class="stat">
        <div class="stat__value">{{ degradedCount }}<span>个</span></div>
        <div class="stat__label">规则待升级</div>
      </div>
    </div>

    <div v-if="store.loading" class="loading-bar" />
    <div v-if="store.error" class="forbidden">{{ store.error }}</div>

    <div class="panel panel--flush">
      <div class="panel__head" style="padding: var(--space-3) var(--space-4) 0">
        <span class="panel__title">信源清单</span>
        <span class="panel__meta">权重 1—5 · 抽取规则 ok / degraded / pending</span>
      </div>
      <div style="padding: 0 var(--space-4) var(--space-4)">
        <div class="src-row src-row--head mono">
          <span>信源</span>
          <span>类型</span>
          <span>权重</span>
          <span>抽取规则</span>
          <span>原文 / 正文 / 低置信</span>
          <span>最近抓取</span>
          <span v-if="canWriteSource">操作</span>
        </div>
        <div v-for="source in sources" :key="source.id" class="src-row" data-testid="source-row">
          <div>
            <div class="src-name">{{ source.name }}</div>
            <a class="src-home mono" :href="source.homepage" target="_blank" rel="noreferrer">
              {{ source.homepage }}
            </a>
          </div>
          <span class="tag" :class="source.type === 'government' ? 'tag--moss' : ''">
            {{ source.type_label }}
          </span>
          <span class="weight" :title="`权重 ${source.weight}`">
            <span v-for="n in 5" :key="n" :class="{ on: n <= source.weight }">●</span>
          </span>
          <span
            class="tag"
            :class="source.extract_rule_status === 'ok' ? 'tag--moss' : 'tag--ochre'"
          >
            {{ source.extract_rule_status }}
          </span>
          <span class="mono counts">
            {{ source.raw_count }} / {{ source.article_count }} /
            <b :style="{ color: source.low_confidence_count ? 'var(--vermilion)' : 'inherit' }">
              {{ source.low_confidence_count }}
            </b>
          </span>
          <span class="mono" style="color: var(--ink-faint)">{{ formatDateTime(source.last_fetched_at) }}</span>
          <span v-if="canWriteSource">
            <button class="btn btn--ghost" type="button" style="padding: 0.2rem 0.6rem" @click="toggle(source)">
              {{ source.enabled ? '停用' : '启用' }}
            </button>
          </span>
        </div>
      </div>
    </div>

    <form v-if="canWriteSource" class="panel" style="margin-top: var(--space-5)" @submit.prevent="create">
      <div class="panel__head">
        <span class="panel__title">新增信源</span>
        <span class="panel__meta">仅主编可操作 · POST /sources</span>
      </div>
      <div style="display: grid; grid-template-columns: 1.3fr 2fr 1fr 0.8fr; gap: var(--space-3)">
        <div class="field">
          <label>名称</label>
          <input v-model="form.name" name="name" required minlength="2" data-testid="source-name" />
        </div>
        <div class="field">
          <label>主页</label>
          <input v-model="form.homepage" name="homepage" required />
        </div>
        <div class="field">
          <label>类型</label>
          <select v-model="form.type" name="type">
            <option value="media">同行媒体</option>
            <option value="government">政府公告</option>
            <option value="selfmedia">自媒体</option>
          </select>
        </div>
        <div class="field">
          <label>权重</label>
          <select v-model.number="form.weight" name="weight">
            <option v-for="n in 5" :key="n" :value="n">{{ n }}</option>
          </select>
        </div>
      </div>
      <div class="export-actions">
        <button class="btn" type="submit" :disabled="submitting">登记信源</button>
      </div>
    </form>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useSourceStore } from '../stores/sources'
import { usePermission } from '../hooks/usePermission'
import { useToast } from '../hooks/useToast'
import { formatDateTime } from '../utils/format'
import type { Source } from '../types'

const store = useSourceStore()
const { canWriteSource } = usePermission()
const { push, failure } = useToast()

const sources = computed(() => store.items)
const submitting = ref(false)
const form = reactive({ name: '', homepage: '', type: 'media', weight: 3 })
const enabledCount = computed(() => sources.value.filter((item) => item.enabled).length)
const degradedCount = computed(
  () => sources.value.filter((item) => item.extract_rule_status !== 'ok').length,
)

function sumBy(key: 'raw_count' | 'article_count' | 'low_confidence_count'): number {
  return sources.value.reduce((total, item) => total + item[key], 0)
}

onMounted(() => {
  void store.load()
})

async function toggle(source: Source) {
  try {
    await store.toggle(source)
    push(`已${source.enabled ? '停用' : '启用'}「${source.name}」`)
  } catch (exc) {
    failure(exc)
  }
}

async function create() {
  submitting.value = true
  try {
    await store.create({ ...form })
    push(`已登记信源「${form.name}」`)
    form.name = ''
    form.homepage = ''
  } catch (exc) {
    failure(exc)
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.src-row {
  display: grid;
  grid-template-columns: 1.5fr 0.8fr 0.7fr 0.9fr 1.2fr 1.1fr 0.6fr;
  gap: var(--space-3);
  align-items: center;
  padding: var(--space-3) 0;
  border-bottom: 1px dotted var(--rule);
}

.src-row--head {
  border-bottom: 3px double var(--rule-strong);
  color: var(--ink-faint);
  font-size: 0.62rem;
  letter-spacing: 0.1em;
}

.src-name {
  font-family: var(--font-display);
  font-size: var(--step-1);
}

.src-home {
  display: block;
  color: var(--ink-faint);
  font-size: 0.62rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.weight span {
  color: var(--rule);
  font-size: 0.6rem;
  margin-right: 0.1rem;
}

.weight span.on {
  color: var(--vermilion);
}

.counts {
  color: var(--ink-soft);
}
</style>
