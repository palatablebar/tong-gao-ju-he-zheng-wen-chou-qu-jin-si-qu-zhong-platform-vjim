import { defineStore } from 'pinia'
import { ref } from 'vue'
import { createSource, listSources, updateSource } from '../api/sources'
import type { Source } from '../types'

export const useSourceStore = defineStore('sources', () => {
  const items = ref<Source[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function load(): Promise<void> {
    loading.value = true
    error.value = null
    try {
      items.value = await listSources()
    } catch (exc) {
      error.value = exc instanceof Error ? exc.message : String(exc)
    } finally {
      loading.value = false
    }
  }

  async function create(payload: {
    name: string
    homepage: string
    type: string
    weight: number
    description: string
  }): Promise<Source> {
    const created = await createSource(payload)
    await load()
    return created
  }

  async function toggle(source: Source): Promise<void> {
    await updateSource(source.id, { enabled: !source.enabled })
    await load()
  }

  return { items, loading, error, load, create, toggle }
})
