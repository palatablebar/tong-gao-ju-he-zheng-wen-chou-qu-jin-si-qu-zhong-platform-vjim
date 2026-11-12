import { defineStore } from 'pinia'
import { ref } from 'vue'
import {
  confirmRepresentative,
  fetchCluster,
  listClusters,
  splitCluster,
} from '../api/clusters'
import { fetchRun, startDedupRun } from '../api/dedup'
import type { Cluster, ClusterDetail, DedupRun, SuspectEdge } from '../types'

export const useClusterStore = defineStore('clusters', () => {
  const items = ref<Cluster[]>([])
  const detail = ref<ClusterDetail | null>(null)
  const run = ref<DedupRun | null>(null)
  const suspectEdges = ref<SuspectEdge[]>([])
  const loading = ref(false)
  const detailLoading = ref(false)
  const runBusy = ref(false)
  const error = ref<string | null>(null)
  const justConfirmed = ref(false)

  async function load(): Promise<void> {
    loading.value = true
    error.value = null
    try {
      const response = await listClusters()
      items.value = response.items
      run.value = response.run
      suspectEdges.value = response.suspect_edges
    } catch (exc) {
      error.value = exc instanceof Error ? exc.message : String(exc)
    } finally {
      loading.value = false
    }
  }

  async function loadDetail(clusterId: number): Promise<void> {
    detailLoading.value = true
    try {
      detail.value = await fetchCluster(clusterId)
    } catch (exc) {
      error.value = exc instanceof Error ? exc.message : String(exc)
    } finally {
      detailLoading.value = false
    }
  }

  async function runDedup(): Promise<DedupRun | null> {
    runBusy.value = true
    error.value = null
    justConfirmed.value = false
    try {
      let current = await startDedupRun()
      run.value = current
      const deadline = Date.now() + 120_000
      while (current && ['queued', 'running'].includes(current.status) && Date.now() < deadline) {
        await new Promise((resolve) => window.setTimeout(resolve, 900))
        current = await fetchRun(current.id)
        run.value = current
      }
      await load()
      return current
    } catch (exc) {
      error.value = exc instanceof Error ? exc.message : String(exc)
      return null
    } finally {
      runBusy.value = false
    }
  }

  async function confirm(articleId: number): Promise<void> {
    if (!detail.value) return
    detail.value = await confirmRepresentative(detail.value.id, articleId)
    justConfirmed.value = true
    await load()
  }

  async function split(articleIds: number[]): Promise<void> {
    if (!detail.value) return
    await splitCluster(detail.value.id, articleIds)
    await load()
  }

  return {
    items,
    detail,
    run,
    suspectEdges,
    loading,
    detailLoading,
    runBusy,
    error,
    justConfirmed,
    load,
    loadDetail,
    runDedup,
    confirm,
    split,
  }
})
