import { http } from './http'
import type { ClusterDetail, ClusterListResponse } from '../types'

export async function listClusters(status?: string): Promise<ClusterListResponse> {
  const { data } = await http.get<ClusterListResponse>('/clusters', {
    params: status ? { status } : {},
  })
  return data
}

export async function fetchCluster(clusterId: number): Promise<ClusterDetail> {
  const { data } = await http.get<ClusterDetail>(`/clusters/${clusterId}`)
  return data
}

export async function confirmRepresentative(
  clusterId: number,
  articleId: number,
): Promise<ClusterDetail> {
  const { data } = await http.post<ClusterDetail>(`/clusters/${clusterId}/confirm`, {
    representative_article_id: articleId,
  })
  return data
}

export async function splitCluster(clusterId: number, articleIds: number[]): Promise<void> {
  await http.post(`/clusters/${clusterId}/split`, { article_ids: articleIds })
}
