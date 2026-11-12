<template>
  <section>
    <header class="page-head">
      <div>
        <div class="page-head__kicker">04 / Event Timeline</div>
        <h2 class="page-head__title">事件时间轴</h2>
        <p class="page-head__lede">
          编辑把当日去重簇归档成事件，按日排成时间轴；事件右侧挂代表团簇，供选题会拍板用。
          事件与簇的关联在重跑去重后保持（簇按代表稿原地更新）。
        </p>
      </div>
      <div class="page-head__aside">
        <div>TIMELINE · {{ timeline?.total ?? 0 }} 条事件</div>
        <div>{{ days.length }} 个自然日</div>
      </div>
    </header>

    <div class="filter-bar">
      <div class="field">
        <label>分类</label>
        <select v-model="store.category" data-testid="timeline-category" @change="reload">
          <option value="">全部分类</option>
          <option v-for="category in categories" :key="category" :value="category">
            {{ category }}
          </option>
        </select>
      </div>
      <span class="mono" style="color: var(--ink-faint); padding-bottom: 0.55rem">
        时间轴按日倒序 · 点击事件查看族关联
      </span>
    </div>

    <div v-if="store.loading" class="loading-bar" />
    <div v-if="store.error" class="forbidden">{{ store.error }}</div>

    <div class="split-layout">
      <div class="panel">
        <div class="panel__head">
          <span class="panel__title">按日分组</span>
          <span class="panel__meta">EVENT / DATE</span>
        </div>
        <div v-for="day in days" :key="day.date" class="timeline__day">
          <div class="timeline__date">
            <span>{{ day.date }}</span>
            <span style="color: var(--ink-faint)">{{ weekdayLabel(day.date) }} · {{ day.events.length }} 条</span>
          </div>
          <ul class="timeline" style="margin-left: 0.35rem">
            <li
              v-for="event in day.events"
              :key="event.id"
              class="timeline__event"
              :class="{ 'is-active': selectedEvent?.id === event.id }"
              data-testid="event-item"
              @click="selectedEventId = event.id"
            >
              <div class="timeline__event-title">{{ event.title }}</div>
              <div class="timeline__event-note">
                <span class="tag" :class="event.category === '政策' ? 'tag--seal' : event.category === '财经' ? 'tag--ochre' : 'tag--moss'">
                  {{ event.category }}
                </span>
                <span style="margin-left: 0.5rem">{{ event.region }} · {{ event.member_count }} 篇转载</span>
              </div>
            </li>
          </ul>
        </div>
        <div v-if="!days.length && !store.loading" class="empty">该分类下暂无事件。</div>
      </div>

      <div class="panel">
        <div class="panel__head">
          <span class="panel__title">事件侧栏</span>
          <span class="panel__meta">{{ selectedEvent ? selectedEvent.event_date : 'SELECT AN EVENT' }}</span>
        </div>
        <template v-if="selectedEvent">
          <h3 style="font-family: var(--font-display); font-size: var(--step-2); margin-bottom: var(--space-2)">
            {{ selectedEvent.title }}
          </h3>
          <div class="detail-meta">
            <span>{{ selectedEvent.category }}</span>
            <span>{{ selectedEvent.region }}</span>
            <span>{{ selectedEvent.event_date }}</span>
            <span>{{ selectedEvent.member_count }} 篇转载</span>
          </div>
          <p style="color: var(--ink-soft)">{{ selectedEvent.note }}</p>
          <hr class="rule" />
          <div class="mono" style="color: var(--ink-faint); letter-spacing: 0.12em">关联簇</div>
          <div style="margin: var(--space-2) 0 var(--space-4)">
            <RouterLink class="btn btn--ghost" :to="{ path: '/clusters' }" style="display: inline-block">
              {{ selectedEvent.cluster_label || '未关联簇' }}
            </RouterLink>
          </div>
          <div class="mono" style="color: var(--ink-faint); letter-spacing: 0.12em">代表稿</div>
          <p style="margin-top: var(--space-2)">{{ selectedEvent.representative_title }}</p>
          <p class="mono" style="color: var(--ink-faint)">
            {{ selectedEvent.representative_source }} ·
            {{ formatDateTime(selectedEvent.published_at) }}
          </p>
        </template>
        <div v-else class="empty">点击左侧事件，查看分类、关联簇与代表稿。</div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useEventStore } from '../stores/events'
import { formatDateTime, weekdayLabel } from '../utils/format'

const store = useEventStore()
const selectedEventId = ref<number | null>(null)

const timeline = computed(() => store.timeline)
const days = computed(() => timeline.value?.days ?? [])
const categories = computed(() => timeline.value?.categories ?? ['政策', '产业', '民生', '财经'])
const selectedEvent = computed(() => {
  for (const day of days.value) {
    const found = day.events.find((event) => event.id === selectedEventId.value)
    if (found) return found
  }
  return null
})

watch(
  () => days.value,
  (value) => {
    if (value.length && selectedEventId.value === null) {
      selectedEventId.value = value[0].events[0]?.id ?? null
    }
  },
)

onMounted(async () => {
  await store.load()
})

async function reload() {
  selectedEventId.value = null
  await store.load()
}
</script>
