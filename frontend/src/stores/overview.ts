import { defineStore } from 'pinia'
import { ref } from 'vue'
import { fetchOverview } from '../api/daily'
import type { Overview } from '../types'

export const useOverviewStore = defineStore('overview', () => {
  const data = ref<Overview | null>(null)
  const loading = ref(false)

  async function load(): Promise<void> {
    loading.value = true
    try {
      data.value = await fetchOverview()
    } catch {
      data.value = null
    } finally {
      loading.value = false
    }
  }

  return { data, loading, load }
})
