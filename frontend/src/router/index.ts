import { createRouter, createWebHistory } from 'vue-router'
import { setupGuards } from './guards'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/sources' },
    {
      path: '/login',
      name: 'login',
      component: () => import('../pages/LoginPage.vue'),
      meta: { public: true, title: '登录' },
    },
    {
      path: '/sources',
      name: 'sources',
      component: () => import('../pages/SourcesPage.vue'),
      meta: { title: '信源台账' },
    },
    {
      path: '/raw-items',
      name: 'raw-items',
      component: () => import('../pages/RawItemsPage.vue'),
      meta: { title: '原文队列' },
    },
    {
      path: '/clusters',
      name: 'clusters',
      component: () => import('../pages/ClustersPage.vue'),
      meta: { title: '簇审查' },
    },
    {
      path: '/timeline',
      name: 'timeline',
      component: () => import('../pages/TimelinePage.vue'),
      meta: { title: '事件时间轴' },
    },
    {
      path: '/daily',
      name: 'daily',
      component: () => import('../pages/DailyPage.vue'),
      meta: { title: '日报' },
    },
    { path: '/:pathMatch(.*)*', redirect: '/sources' },
  ],
})

setupGuards(router)

export default router
