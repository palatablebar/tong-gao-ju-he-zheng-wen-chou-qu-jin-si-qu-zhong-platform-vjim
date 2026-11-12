import { defineStore } from 'pinia'
import { ref } from 'vue'
import {
  downloadDailyExport,
  fetchDailyReport,
  publishDaily,
} from '../api/daily'
import type { DailyReport } from '../types'

export const useDailyStore = defineStore('daily', () => {
  const report = ref<DailyReport | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)
  const date = ref('2026-11-10')

  async function load(target = date.value): Promise<void> {
    loading.value = true
    error.value = null
    date.value = target
    try {
      report.value = await fetchDailyReport(target)
    } catch (exc) {
      error.value = exc instanceof Error ? exc.message : String(exc)
    } finally {
      loading.value = false
    }
  }

  async function exportAs(format: 'md' | 'csv'): Promise<string> {
    return downloadDailyExport(date.value, format)
  }

  async function publish(): Promise<string> {
    const response = await publishDaily(date.value)
    return response.message
  }

  return { report, loading, error, date, load, exportAs, publish }
})
