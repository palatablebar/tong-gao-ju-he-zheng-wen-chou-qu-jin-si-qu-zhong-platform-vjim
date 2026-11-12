import { http } from './http'
import type { Source } from '../types'

export async function listSources(): Promise<Source[]> {
  const { data } = await http.get<{ items: Source[] }>('/sources')
  return data.items
}

export async function createSource(payload: {
  name: string
  homepage: string
  type: string
  weight: number
  description: string
}): Promise<Source> {
  const { data } = await http.post<Source>('/sources', payload)
  return data
}

export async function updateSource(
  sourceId: number,
  payload: Partial<{ enabled: boolean; weight: number; extract_rule_status: string; description: string }>,
): Promise<Source> {
  const { data } = await http.patch<Source>(`/sources/${sourceId}`, payload)
  return data
}
