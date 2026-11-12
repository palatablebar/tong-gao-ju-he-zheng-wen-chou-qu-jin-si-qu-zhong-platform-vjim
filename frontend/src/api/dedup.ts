import { http } from './http'
import type { DedupRun } from '../types'

export async function startDedupRun(payload?: {
  threshold?: number
  suspect_threshold?: number
}): Promise<DedupRun> {
  const { data } = await http.post<DedupRun>('/dedup/runs', payload ?? {})
  return data
}

export async function fetchRun(runId: number): Promise<DedupRun> {
  const { data } = await http.get<DedupRun>(`/dedup/runs/${runId}`)
  return data
}

export async function fetchLatestRun(): Promise<DedupRun | null> {
  const { data } = await http.get<{ run: DedupRun | null }>('/dedup/runs/latest')
  return data.run
}
