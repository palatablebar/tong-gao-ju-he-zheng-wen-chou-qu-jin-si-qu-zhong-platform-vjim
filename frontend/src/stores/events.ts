import { defineStore } from 'pinia'
import { ref } from 'vue'
import { listTimeline } from '../api/events'
import type { TimelineResponse } from '../types'

export const useEventStore = defineStore('events', () => {
  const timeline = ref<TimelineResponse | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)
  const category = ref('')

  async function load(): Promise<void> {
    loading.value = true
    error.value = null
    try {
      timeline.value = await listTimeline({ category: category.value || undefined })
    } catch (exc) {
      error.value = exc instanceof Error ? exc.message : String(exc)
    } finally {
      loading.value = false
    }
  }

  return { timeline, loading, error, category, load }
})
