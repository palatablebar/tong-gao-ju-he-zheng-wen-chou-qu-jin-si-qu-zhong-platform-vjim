<template>
  <div class="shell">
    <header class="masthead">
      <div class="masthead__brand">
        <h1 class="masthead__title">通稿聚合台</h1>
        <span class="masthead__latin">Dedupwire</span>
      </div>
      <div class="masthead__meta">
        <div>三江传媒集团 · 通稿池 · 第 314 期</div>
        <div>
          <span class="issue">{{ today }}</span>
          · {{ auth.user?.display_name }} / {{ auth.user?.role_label }}
          <button class="logout" type="button" @click="logout">退出</button>
        </div>
      </div>
    </header>

    <div class="shell__body">
      <nav class="index-nav" aria-label="主导航">
        <div class="index-nav__heading">Index · 版面索引</div>
        <ul class="index-nav__list">
          <li v-for="item in navItems" :key="item.path">
            <RouterLink
              class="index-nav__item"
              :class="{ 'is-active': route.path.startsWith(item.path) }"
              :to="item.path"
            >
              <span class="index-nav__num">{{ item.num }}</span>
              <span class="index-nav__label">{{ item.label }}</span>
            </RouterLink>
          </li>
        </ul>
        <div class="index-nav__note">
          <div>信源 {{ overview?.sources ?? '—' }} · 原文 {{ overview?.raws ?? '—' }}</div>
          <div>抽取稿 {{ overview?.articles ?? '—' }} · 簇 {{ overview?.clusters ?? '—' }}</div>
          <div>
            低置信
            <span :style="{ color: 'var(--vermilion)' }">{{ overview?.low_confidence ?? '—' }}</span>
            · 疑似边 {{ overview?.suspect_edges ?? '—' }}
          </div>
          <div style="margin-top: 0.6rem">正文抽取 Readability 式 · 去重 MinHash+LSH</div>
        </div>
      </nav>

      <main class="page">
        <slot />
      </main>
    </div>

    <footer class="shell__footer">
      <span>dedupwire · 三江传媒 · 铅字排版间</span>
      <span>正文抽取 + 近似去重 + 事件时间轴 + 日报</span>
      <span>PostgreSQL 16 · FastAPI · Celery · Vue 3</span>
    </footer>

    <div class="toast-stack">
      <div v-for="toast in toastItems" :key="toast.id" class="toast" :class="{ 'toast--error': toast.tone === 'error' }">
        {{ toast.message }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../../stores/auth'
import { useOverviewStore } from '../../stores/overview'
import { useToast } from '../../hooks/useToast'

const auth = useAuthStore()
const overviewStore = useOverviewStore()
const route = useRoute()
const router = useRouter()
const { items: toastItems } = useToast()

const overview = computed(() => overviewStore.data)
const today = computed(() => new Date().toISOString().slice(0, 10))

const navItems = [
  { num: '01', label: '信源台账', path: '/sources' },
  { num: '02', label: '原文队列', path: '/raw-items' },
  { num: '03', label: '簇审查', path: '/clusters' },
  { num: '04', label: '事件时间轴', path: '/timeline' },
  { num: '05', label: '日报', path: '/daily' },
]

onMounted(() => {
  void overviewStore.load()
})

function logout() {
  auth.logout()
  void router.push('/login')
}
</script>

<style scoped>
.logout {
  margin-left: 0.6rem;
  font-family: var(--font-mono);
  font-size: 0.66rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--vermilion);
  border-bottom: 1px solid var(--vermilion);
  padding: 0;
}
</style>
