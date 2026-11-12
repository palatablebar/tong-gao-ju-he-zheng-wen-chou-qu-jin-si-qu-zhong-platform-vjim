<template>
  <section>
    <header class="page-head">
      <div>
        <div class="page-head__kicker">05 / Daily Brief</div>
        <h2 class="page-head__title">日报预览与导出</h2>
        <p class="page-head__lede">
          按日聚合事件与代表团簇，生成 Markdown 预览；Markdown 与 CSV 都由后端渲染，行数一致。
          只读角色同样可以下载日报。
        </p>
      </div>
      <div class="page-head__aside">
        <div>DAILY · {{ report?.summary.date || store.date }}</div>
        <div>编辑：{{ signedBy }}</div>
      </div>
    </header>

    <div class="filter-bar">
      <div class="field">
        <label>日报日期</label>
        <input v-model="dateInput" type="date" data-testid="daily-date" />
      </div>
      <button class="btn" type="button" data-testid="daily-generate" @click="generate">生成日报</button>
      <button class="btn btn--ghost" type="button" data-testid="export-md" @click="exportAs('md')">
        下载 Markdown
      </button>
      <button class="btn btn--ghost" type="button" data-testid="export-csv" @click="exportAs('csv')">
        下载 CSV
      </button>
      <button
        v-if="isAdmin"
        class="btn btn--seal"
        type="button"
        data-testid="publish-daily"
        @click="publish"
      >
        发布日报
      </button>
      <div style="flex: 1" />
      <span class="mono" style="color: var(--ink-faint); padding-bottom: 0.55rem">
        MD / CSV 同源生成 · 4 条事件 = 4 行
      </span>
    </div>

    <div v-if="store.loading" class="loading-bar" />
    <div v-if="store.error" class="forbidden">{{ store.error }}</div>

    <template v-if="report">
      <div class="stat-strip">
        <div class="stat">
          <div class="stat__value">{{ report.summary.event_count }}<span>条</span></div>
          <div class="stat__label">当日事件</div>
        </div>
        <div class="stat">
          <div class="stat__value">{{ report.summary.article_count }}<span>篇</span></div>
          <div class="stat__label">通稿库总量</div>
        </div>
        <div class="stat">
          <div class="stat__value">{{ report.summary.cluster_count }}<span>簇</span></div>
          <div class="stat__label">去重簇</div>
        </div>
        <div class="stat">
          <div class="stat__value">{{ report.summary.suspect_count }}<span>条</span></div>
          <div class="stat__label">疑似边</div>
        </div>
        <div class="stat">
          <div class="stat__value">
            {{ (report.summary.duplicate_rate * 100).toFixed(1) }}<span>%</span>
          </div>
          <div class="stat__label">重复率</div>
        </div>
      </div>

      <div class="split-layout">
        <div class="panel">
          <div class="panel__head">
            <span class="panel__title">当日事件单</span>
            <span class="panel__meta">{{ report.events.length }} 行</span>
          </div>
          <table style="width: 100%; border-collapse: collapse; font-size: var(--step--1)">
            <thead>
              <tr style="text-align: left; border-bottom: 3px double var(--rule-strong)">
                <th style="padding: 0.4rem 0.3rem">#</th>
                <th style="padding: 0.4rem 0.3rem">事件</th>
                <th style="padding: 0.4rem 0.3rem">分类</th>
                <th style="padding: 0.4rem 0.3rem">代表稿</th>
                <th style="padding: 0.4rem 0.3rem">转载</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(event, index) in report.events" :key="event.id" style="border-bottom: 1px dotted var(--rule)">
                <td style="padding: 0.45rem 0.3rem" class="mono">{{ String(index + 1).padStart(2, '0') }}</td>
                <td style="padding: 0.45rem 0.3rem">{{ event.title }}</td>
                <td style="padding: 0.45rem 0.3rem">{{ event.category }}</td>
                <td style="padding: 0.45rem 0.3rem; color: var(--ink-soft)">{{ event.representative_title }}</td>
                <td style="padding: 0.45rem 0.3rem" class="mono">{{ event.member_count }}</td>
              </tr>
            </tbody>
          </table>
          <div class="export-actions">
            <span class="mono" style="color: var(--ink-faint)">
              CSV 表头：序号 / 事件标题 / 分类 / 地区 / 代表稿标题 / 信源 / 发布时间 / 重复篇数 / 平均相似度
            </span>
          </div>
        </div>

        <div class="panel">
          <div class="panel__head">
            <span class="panel__title">Markdown 预览</span>
            <span class="panel__meta">由后端 /daily 接口返回</span>
          </div>
          <pre class="markdown-preview" data-testid="daily-markdown">{{ report.markdown }}</pre>
        </div>
      </div>
    </template>
    <div v-else class="empty">选择日期后点击「生成日报」。</div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useDailyStore } from '../stores/daily'
import { useAuthStore } from '../stores/auth'
import { useToast } from '../hooks/useToast'
import { DAILY_DATE } from '../constants/enums'

const store = useDailyStore()
const auth = useAuthStore()
const { push, failure } = useToast()

const dateInput = ref(DAILY_DATE)
const report = computed(() => store.report)
const isAdmin = computed(() => auth.user?.role === 'admin')
const signedBy = computed(() => auth.user?.display_name || '—')

onMounted(() => {
  void store.load(DAILY_DATE)
})

async function generate() {
  await store.load(dateInput.value)
  if (store.report) push(`已生成 ${dateInput.value} 日报：${store.report.events.length} 条事件`)
}

async function exportAs(format: 'md' | 'csv') {
  try {
    const filename = await store.exportAs(format)
    push(`已下载 ${filename}`)
  } catch (exc) {
    failure(exc)
  }
}

async function publish() {
  try {
    const message = await store.publish()
    push(message)
  } catch (exc) {
    failure(exc)
  }
}
</script>
