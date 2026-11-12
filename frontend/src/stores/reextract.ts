import { defineStore } from 'pinia'
import { ref } from 'vue'
import {
  fetchReextractBatch,
  listReextractBatches,
  retryReextractBatch,
  startReextract,
} from '../api/reextract'
import type { ReextractBatch } from '../types'

const ACTIVE = ['queued', 'running']

async function pollUntilSettled(
  initial: ReextractBatch,
  onTick: (value: ReextractBatch) => void,
  deadlineMs = 120_000,
): Promise<ReextractBatch> {
  let current = initial
  const deadline = Date.now() + deadlineMs
  while (ACTIVE.includes(current.status) && Date.now() < deadline) {
    await new Promise((resolve) => window.setTimeout(resolve, 800))
    current = await fetchReextractBatch(current.id)
    onTick(current)
  }
  // Also wait for the downstream dedup so «重抽后重新去重» is reflected on the page.
  while (current.dedup_pending && Date.now() < deadline) {
    await new Promise((resolve) => window.setTimeout(resolve, 800))
    current = await fetchReextractBatch(current.id)
    onTick(current)
  }
  return current
}

export const useReextractStore = defineStore('reextract', () => {
  const batches = ref<ReextractBatch[]>([])
  const current = ref<ReextractBatch | null>(null)
  const latest = ref<ReextractBatch | null>(null)
  const busy = ref(false)
  const error = ref<string | null>(null)

  async function load(sourceId?: number): Promise<void> {
    error.value = null
    try {
      const response = await listReextractBatches(sourceId)
      batches.value = response.items
      latest.value = response.latest
      if (current.value) {
        const match = response.items.find((item) => item.id === current.value?.id)
        if (match) current.value = match
      }
    } catch (exc) {
      error.value = exc instanceof Error ? exc.message : String(exc)
    }
  }

  async function selectBatch(batchId: number): Promise<void> {
    current.value = await fetchReextractBatch(batchId)
  }

  async function request(sourceId: number): Promise<ReextractBatch | null> {
    busy.value = true
    error.value = null
    try {
      const created = await startReextract(sourceId)
      current.value = await pollUntilSettled(created, (value) => {
        current.value = value
      })
      await load(sourceId)
      return current.value
    } catch (exc) {
      error.value = exc instanceof Error ? exc.message : String(exc)
      return null
    } finally {
      busy.value = false
    }
  }

  async function retry(batchId: number): Promise<ReextractBatch | null> {
    busy.value = true
    error.value = null
    try {
      const resumed = await retryReextractBatch(batchId)
      current.value = await pollUntilSettled(resumed, (value) => {
        current.value = value
      })
      await load()
      return current.value
    } catch (exc) {
      error.value = exc instanceof Error ? exc.message : String(exc)
      return null
    } finally {
      busy.value = false
    }
  }

  return { batches, current, latest, busy, error, load, selectBatch, request, retry }
})
