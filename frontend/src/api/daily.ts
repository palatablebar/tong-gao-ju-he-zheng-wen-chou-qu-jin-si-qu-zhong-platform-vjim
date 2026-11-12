import { http, extractFileName } from './http'
import type { DailyReport, Overview } from '../types'

export async function fetchDailyReport(date: string): Promise<DailyReport> {
  const { data } = await http.get<DailyReport>('/daily', { params: { date } })
  return data
}

export async function downloadDailyExport(date: string, format: 'md' | 'csv'): Promise<string> {
  const response = await http.get(`/daily/export`, {
    params: { date, format },
    responseType: 'blob',
  })
  const blob = new Blob([response.data], {
    type: format === 'csv' ? 'text/csv;charset=utf-8' : 'text/markdown;charset=utf-8',
  })
  const filename = extractFileName(
    response.headers['content-disposition'] as string | undefined,
    `dedupwire-daily-${date}.${format}`,
  )
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = filename
  anchor.click()
  URL.revokeObjectURL(url)
  return filename
}

export async function publishDaily(date: string): Promise<{ message: string }> {
  const { data } = await http.post<{ message: string }>('/daily/publish', { date })
  return data
}

export async function fetchOverview(): Promise<Overview> {
  const { data } = await http.get<Overview>('/overview')
  return data
}
