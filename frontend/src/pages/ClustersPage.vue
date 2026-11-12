<template>
  <section>
    <header class="page-head">
      <div>
        <div class="page-head__kicker">03 / Cluster Desk</div>
        <h2 class="page-head__title">去重簇审查</h2>
        <p class="page-head__lede">
          Celery worker 用 MinHash（128 签名）+ LSH（32 band × 4 row）找候选对，再用精确 Jaccard
          复核：≥ 0.72 判重合并，0.55—0.72 记「疑似边」。代表稿按 0.5×正文长度 + 0.3×发布时间 +
          0.2×信源权重 选出。
        </p>
      </div>
      <div class="page-head__aside">
        <div>RUN · {{ run ? run.status_label : '未运行' }}</div>
        <div>threshold {{ run?.threshold ?? 0.72 }} · suspect {{ run?.suspect_threshold ?? 0.55 }}</div>
      </div>
    </header>

    <div class="stat-strip">
      <div class="stat">
        <div class="stat__value">{{ store.items.length }}<span>簇</span></div>
        <div class="stat__label">去重簇</div>
      </div>
      <div class="stat">
        <div class="stat__value">{{ totalMembers }}<span>篇</span></div>
        <div class="stat__label">入簇通稿</div>
      </div>
      <div class="stat">
        <div class="stat__value">{{ store.suspectEdges.length }}<span>条</span></div>
        <div class="stat__label">疑似边</div>
      </div>
      <div class="stat">
        <div class="stat__value">{{ duplicateRate }}<span>%</span></div>
        <div class="stat__label">重复率 (篇-簇)/篇</div>
      </div>
      <div class="stat">
        <div class="stat__value">{{ largestClusterSize }}<span>篇</span></div>
        <div class="stat__label">最大簇</div>
      </div>
      <div class="stat">
        <div class="stat__value">{{ run ? run.candidate_pair_count : '—' }}<span>对</span></div>
        <div class="stat__label">LSH 候选对</div>
      </div>
    </div>

    <div class="filter-bar" style="align-items: center">
      <button
        class="btn btn--seal seal-button"
        type="button"
        data-testid="run-dedup"
        :disabled="!canRunDedup || store.runBusy"
        :title="canRunDedup ? '触发 Celery 去重任务' : '只读角色无运行权限（后端 403）'"
        @click="triggerRun"
      >
        {{ store.runBusy ? '计算中…' : '运行去重' }}
      </button>
      <span v-if="run" class="mono" style="color: var(--ink-faint)">
        run #{{ run.id }} · {{ run.status_label }} · 触发人 {{ run.triggered_by }} ·
        {{ formatDateTime(run.finished_at || run.started_at) }}
      </span>
      <span v-else class="mono" style="color: var(--ink-faint)">尚未运行，seed 态为初始聚类</span>
      <span v-if="!canRunDedup" class="tag tag--ochre">只读角色：运行去重 → 403</span>
      <div style="flex: 1" />
      <span v-if="store.error" class="forbidden">{{ store.error }}</span>
    </div>

    <div v-if="store.runBusy" class="loading-bar" />

    <div class="split-layout">
      <div class="panel panel--flush">
        <div class="panel__head" style="padding: var(--space-3) var(--space-4) 0">
          <span class="panel__title">簇清单</span>
          <span class="panel__meta">按成员数降序</span>
        </div>
        <ul class="row-list" style="padding: 0 var(--space-2) var(--space-2)">
          <li
            v-for="cluster in store.items"
            :key="cluster.id"
            class="row"
            :class="{ 'is-active': store.detail?.id === cluster.id }"
            data-testid="cluster-row"
            @click="selectCluster(cluster.id)"
          >
            <div class="row__title">{{ cluster.topic_label }}</div>
            <div class="row__meta">
              <span>{{ cluster.member_count }} 篇</span>
              <span>mean {{ cluster.mean_similarity.toFixed(3) }}</span>
              <span class="stamp" :class="`stamp--${cluster.status}`" style="transform: none">
                {{ cluster.status_label }}
              </span>
            </div>
          </li>
        </ul>
      </div>

      <div class="panel" data-testid="cluster-detail-panel">
        <template v-if="detail">
          <div class="panel__head">
            <span class="panel__title">{{ detail.topic_label }}</span>
            <span style="display: flex; align-items: center; gap: var(--space-2)">
              <SimilarityMeter :value="detail.mean_similarity" :threshold="run?.threshold ?? 0.72" />
              <StampBadge
                :label="detail.status_label"
                :tone="detail.status === 'confirmed' ? 'confirmed' : detail.status === 'split' ? 'split' : 'auto'"
                :animate="store.justConfirmed"
              />
            </span>
          </div>

          <div class="detail-meta">
            <span>{{ detail.member_count }} 篇转载</span>
            <span>mean similarity {{ detail.mean_similarity.toFixed(3) }}</span>
            <span>first seen {{ formatDateTime(detail.first_seen_at) }}</span>
            <span>代表稿 {{ representative?.source_name }}</span>
          </div>

          <div class="export-actions" style="margin-bottom: var(--space-2)">
            <button
              v-if="canReviewCluster && detail.status !== 'confirmed'"
              class="btn btn--seal seal-button"
              type="button"
              data-testid="confirm-cluster"
              @click="confirmCurrent"
            >
              确认代表稿（落章）
            </button>
            <span v-else-if="detail.status === 'confirmed'" class="mono" style="color: var(--vermilion)">
              代表稿已确认 · {{ representative?.source_name }}
            </span>
          </div>

          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: var(--space-3); margin-bottom: var(--space-3)">
            <div class="field">
              <label>左栏对照稿</label>
              <select v-model.number="leftArticleId" data-testid="diff-left">
                <option v-for="member in detail.members" :key="member.article_id" :value="member.article_id">
                  {{ member.source_name }} · {{ member.title }}
                </option>
              </select>
            </div>
            <div class="field">
              <label>右栏对照稿</label>
              <select v-model.number="rightArticleId" data-testid="diff-right">
                <option v-for="member in detail.members" :key="member.article_id" :value="member.article_id">
                  {{ member.source_name }} · {{ member.title }}
                </option>
              </select>
            </div>
          </div>

          <BodyDiffPanel
            v-if="leftMember && rightMember"
            mode="diff"
            :left-title="`${leftMember.source_name} · ${leftMember.title}`"
            :left-text="leftMember.body_text"
            :right-title="`${rightMember.source_name} · ${rightMember.title}`"
            :right-text="rightMember.body_text"
          />

          <div v-if="detail.suspect_edges.length" style="margin-top: var(--space-4)">
            <div class="mono" style="color: var(--vermilion); letter-spacing: 0.12em; margin-bottom: var(--space-2)">
              疑似边（0.55 ≤ jaccard &lt; 0.72，未合并）
            </div>
            <ul class="suspect-list">
              <li v-for="edge in detail.suspect_edges" :key="`${edge.article_a_id}-${edge.article_b_id}`" class="suspect">
                <div class="suspect__pair">
                  <span>{{ edge.title_a }}</span>
                  <span>↔ {{ edge.title_b }}</span>
                  <b class="mono" style="color: var(--vermilion)">{{ edge.similarity.toFixed(3) }}</b>
                </div>
              </li>
            </ul>
          </div>

          <div class="member-grid" style="margin-bottom: var(--space-3)">
            <div
              v-for="(member, index) in detail.members"
              :key="member.article_id"
              class="member"
              :class="{ 'is-picked': member.article_id === rightArticleId }"
              data-testid="cluster-member"
              @click="pickRight(member.article_id)"
            >
              <span class="member__rank">{{ String(index + 1).padStart(2, '0') }}</span>
              <div class="member__main">
                <div class="member__title">
                  <span v-if="member.is_representative" class="tag tag--seal" style="margin-right: 0.35rem">代表稿</span>
                  {{ member.title }}
                </div>
                <div class="member__meta">
                  {{ member.source_name }} · {{ formatDateTime(member.published_at) }} · {{ member.word_count }} 字 ·
                  {{ member.extractor }}
                </div>
              </div>
              <span class="member__sim">sim {{ member.similarity_to_rep.toFixed(3) }}</span>
              <span style="display: flex; gap: 0.35rem; align-items: center">
                <input
                  v-if="canSplitCluster && !member.is_representative"
                  v-model="splitSelection"
                  type="checkbox"
                  :value="member.article_id"
                  title="勾选后拆分为新簇"
                  style="accent-color: var(--vermilion)"
                />
                <button
                  v-if="canReviewCluster && !member.is_representative"
                  class="btn btn--ghost"
                  type="button"
                  style="padding: 0.15rem 0.45rem"
                  :data-testid="`set-rep-${member.article_id}`"
                  @click.stop="setRepresentative(member.article_id)"
                >
                  选为
                </button>
                <span v-else-if="member.is_representative" class="mono" style="color: var(--vermilion)">REP</span>
              </span>
            </div>
          </div>


          <div v-if="canSplitCluster" class="export-actions">
            <button
              class="btn btn--ghost"
              type="button"
              data-testid="split-cluster"
              :disabled="!splitSelection.length"
              @click="split"
            >
              拆分选中成员（{{ splitSelection.length }}）
            </button>
            <span class="mono" style="color: var(--ink-faint)">仅主编可拆分 · 簇数 +1</span>
          </div>
        </template>
        <div v-else class="empty">从左侧选择一簇查看并排 diff、相似度与代表稿。</div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useClusterStore } from '../stores/clusters'
import { usePermission } from '../hooks/usePermission'
import { useToast } from '../hooks/useToast'
import { formatDateTime } from '../utils/format'
import SimilarityMeter from '../components/common/SimilarityMeter.vue'
import StampBadge from '../components/common/StampBadge.vue'
import BodyDiffPanel from '../components/common/BodyDiffPanel.vue'

const store = useClusterStore()
const { canRunDedup, canReviewCluster, canSplitCluster } = usePermission()
const { push, failure } = useToast()

const run = computed(() => store.run)
const detail = computed(() => store.detail)
const leftArticleId = ref<number | null>(null)
const rightArticleId = ref<number | null>(null)
const splitSelection = ref<number[]>([])

const totalMembers = computed(() =>
  store.items.reduce((total, cluster) => total + cluster.member_count, 0),
)
const duplicateRate = computed(() => {
  if (!totalMembers.value) return '0.0'
  return (((totalMembers.value - store.items.length) / totalMembers.value) * 100).toFixed(1)
})
const largestClusterSize = computed(() =>
  store.items.reduce((max, cluster) => Math.max(max, cluster.member_count), 0),
)
const representative = computed(
  () => detail.value?.members.find((member) => member.is_representative) || null,
)
const leftMember = computed(
  () => detail.value?.members.find((member) => member.article_id === leftArticleId.value) || null,
)
const rightMember = computed(
  () => detail.value?.members.find((member) => member.article_id === rightArticleId.value) || null,
)

watch(
  () => store.detail?.id,
  () => {
    if (!detail.value) return
    const rep = detail.value.members.find((member) => member.is_representative)
    leftArticleId.value = rep?.article_id ?? detail.value.members[0]?.article_id ?? null
    const other = detail.value.members.find((member) => member.article_id !== leftArticleId.value)
    rightArticleId.value = other?.article_id ?? leftArticleId.value
    splitSelection.value = []
  },
)

onMounted(async () => {
  await store.load()
  const first = store.items[0]
  if (first) {
    await store.loadDetail(first.id)
  }
})

async function selectCluster(clusterId: number) {
  await store.loadDetail(clusterId)
}

function pickRight(articleId: number) {
  rightArticleId.value = articleId
}

async function triggerRun() {
  const result = await store.runDedup()
  if (!result) {
    failure(store.error || '去重任务失败')
    return
  }
  push(`去重完成：${result.article_count} 篇 → ${result.cluster_count} 簇 · 疑似边 ${result.suspect_edge_count}`)
  const first = store.items[0]
  if (first) {
    await store.loadDetail(first.id)
  }
}

async function confirmCurrent() {
  if (!detail.value?.representative_article_id) return
  await setRepresentative(detail.value.representative_article_id)
}

async function setRepresentative(articleId: number) {
  try {
    await store.confirm(articleId)
    push('已确认代表稿，簇状态 confirmed（印章已落下）')
    if (detail.value) {
      leftArticleId.value = detail.value.representative_article_id
    }
  } catch (exc) {
    failure(exc)
  }
}

async function split() {
  if (!detail.value || !splitSelection.value.length) return
  try {
    await store.split([...splitSelection.value])
    push(`已拆出 ${splitSelection.value.length} 篇为新簇，审计日志已记录`)
    splitSelection.value = []
    if (store.detail) {
      await store.loadDetail(store.detail.id)
    }
  } catch (exc) {
    failure(exc)
  }
}
</script>
