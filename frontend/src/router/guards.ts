import type { Router } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { ROLE_HOME } from '../constants/roles'
import type { RoleKey } from '../types'

export function setupGuards(router: Router): void {
  router.beforeEach((to) => {
    const auth = useAuthStore()
    if (to.meta.public) {
      if (auth.isAuthenticated && to.path === '/login') {
        return { path: ROLE_HOME[auth.user?.role as RoleKey] || '/sources' }
      }
      return true
    }
    if (!auth.isAuthenticated) {
      return { path: '/login', query: { redirect: to.fullPath } }
    }
    const roles = to.meta.roles as RoleKey[] | undefined
    if (roles && auth.user && !roles.includes(auth.user.role)) {
      return { path: ROLE_HOME[auth.user.role] }
    }
    return true
  })
}
