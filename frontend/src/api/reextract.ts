import { http } from './http'
import type { ReextractBatch, ReextractListResponse } from '../types'

export async function startReextract(sourceId: number): Promise<ReextractBatch> {
  const { data } = await http.post<ReextractBatch>('/reextract/batches', { source_id: sourceId })
  return data
}

export async function fetchReextractBatch(batchId: number): Promise<ReextractBatch> {
  const { data } = await http.get<ReextractBatch>(`/reextract/batches/${batchId}`)
  return data
}

export async function listReextractBatches(sourceId?: number): Promise<ReextractListResponse> {
  const { data } = await http.get<ReextractListResponse>('/reextract/batches', {
    params: sourceId ? { source_id: sourceId } : {},
  })
  return data
}

export async function retryReextractBatch(batchId: number): Promise<ReextractBatch> {
  const { data } = await http.post<ReextractBatch>(`/reextract/batches/${batchId}/retry`)
  return data
}
