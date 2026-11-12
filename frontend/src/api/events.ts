import { http } from './http'
import type { TimelineResponse } from '../types'

export async function listTimeline(params?: { category?: string }): Promise<TimelineResponse> {
  const { data } = await http.get<TimelineResponse>('/events', { params: params ?? {} })
  return data
}
