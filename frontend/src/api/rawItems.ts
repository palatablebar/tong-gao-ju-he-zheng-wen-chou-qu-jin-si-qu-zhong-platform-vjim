import { http } from './http'
import type { RawItemDetail, RawItemListResponse } from '../types'

export interface RawItemQuery {
  page?: number
  page_size?: number
  status?: string
  low_confidence?: boolean
  source_id?: number
  q?: string
}

export async function listRawItems(query: RawItemQuery): Promise<RawItemListResponse> {
  const { data } = await http.get<RawItemListResponse>('/raw-items', { params: query })
  return data
}

export async function fetchRawItem(rawItemId: number): Promise<RawItemDetail> {
  const { data } = await http.get<RawItemDetail>(`/raw-items/${rawItemId}`)
  return data
}

export async function correctArticle(
  articleId: number,
  bodyText: string,
  note = '',
): Promise<void> {
  await http.post(`/articles/${articleId}/correct`, { body_text: bodyText, note })
}
