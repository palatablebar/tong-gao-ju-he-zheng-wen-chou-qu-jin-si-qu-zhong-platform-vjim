import { defineStore } from 'pinia'
import { reactive, ref } from 'vue'
import { correctArticle, fetchRawItem, listRawItems } from '../api/rawItems'
import type { RawItem, RawItemDetail } from '../types'

export interface RawFilters {
  status: string
  low_confidence: boolean
  source_id: number | null
  q: string
  page: number
}

export const useRawItemStore = defineStore('rawItems', () => {
  const items = ref<RawItem[]>([])
  const total = ref(0)
  const loading = ref(false)
  const error = ref<string | null>(null)
  const detail = ref<RawItemDetail | null>(null)
  const detailLoading = ref(false)
  const filters = reactive<RawFilters>({
    status: '',
    low_confidence: false,
    source_id: null,
    q: '',
    page: 1,
  })

  async function load(): Promise<void> {
    loading.value = true
    error.value = null
    try {
      const response = await listRawItems({
        page: filters.page,
        page_size: 24,
        status: filters.status || undefined,
        low_confidence: filters.low_confidence || undefined,
        source_id: filters.source_id ?? undefined,
        q: filters.q || undefined,
      })
      items.value = response.items
      total.value = response.total
    } catch (exc) {
      error.value = exc instanceof Error ? exc.message : String(exc)
    } finally {
      loading.value = false
    }
  }

  async function loadDetail(rawItemId: number): Promise<void> {
    detailLoading.value = true
    try {
      detail.value = await fetchRawItem(rawItemId)
    } catch (exc) {
      error.value = exc instanceof Error ? exc.message : String(exc)
    } finally {
      detailLoading.value = false
    }
  }

  async function correct(articleId: number, bodyText: string, note = ''): Promise<void> {
    await correctArticle(articleId, bodyText, note)
    if (detail.value) {
      await loadDetail(detail.value.item.id)
    }
    await load()
  }

  return { items, total, loading, error, detail, detailLoading, filters, load, loadDetail, correct }
})
