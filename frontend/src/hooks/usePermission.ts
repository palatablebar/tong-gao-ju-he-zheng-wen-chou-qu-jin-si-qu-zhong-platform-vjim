import { computed } from 'vue'
import { useAuthStore } from '../stores/auth'
import { PERMISSIONS } from '../constants/roles'

/** 前端权限提示（后端仍然强制校验，前端只负责隐藏/禁用按钮） */
export function usePermission() {
  const auth = useAuthStore()

  function can(permission: string): boolean {
    if (!auth.user) return false
    const allowed = PERMISSIONS[permission] || []
    return allowed.includes(auth.user.role)
  }

  const canCorrect = computed(() => can('article:correct'))
  const canRunDedup = computed(() => can('dedup:run'))
  const canReviewCluster = computed(() => can('cluster:review'))
  const canSplitCluster = computed(() => can('cluster:split'))
  const canWriteSource = computed(() => can('source:write'))
  const canExportDaily = computed(() => can('daily:export'))

  return {
    can,
    canCorrect,
    canRunDedup,
    canReviewCluster,
    canSplitCluster,
    canWriteSource,
    canExportDaily,
  }
}
