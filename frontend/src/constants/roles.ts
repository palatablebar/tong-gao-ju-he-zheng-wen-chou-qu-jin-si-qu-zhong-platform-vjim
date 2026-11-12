import type { RoleKey } from '../types'

export const ROLE_LABELS: Record<RoleKey, string> = {
  admin: '主编',
  analyst: '编辑',
  viewer: '只读',
}

/** 与后端 backend/src/constants/roles.py 的 PERMISSIONS 一一对应 */
export const PERMISSIONS: Record<string, RoleKey[]> = {
  'source:write': ['admin'],
  'raw:read': ['admin', 'analyst', 'viewer'],
  'article:correct': ['admin', 'analyst'],
  'cluster:review': ['admin', 'analyst'],
  'cluster:split': ['admin'],
  'dedup:run': ['admin', 'analyst'],
  'event:write': ['admin', 'analyst'],
  'daily:export': ['admin', 'analyst', 'viewer'],
  'audit:read': ['admin'],
}

export const ROLE_HOME: Record<RoleKey, string> = {
  admin: '/sources',
  analyst: '/raw-items',
  viewer: '/timeline',
}
