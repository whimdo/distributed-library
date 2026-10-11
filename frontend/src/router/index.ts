import { createRouter, createWebHistory } from 'vue-router'
import AppLayout from '@/layouts/AppLayout.vue'
import PortalLayout from '@/layouts/PortalLayout.vue'
import { useAuthStore } from '@/stores/auth'
import type { UserRole } from '@/types'

declare module 'vue-router' {
  interface RouteMeta {
    title?: string
    eyebrow?: string
    public?: boolean
    roles?: UserRole[]
  }
}

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/login' },
    { path: '/login', name: 'login', component: () => import('@/views/LoginView.vue'), meta: { title: '登录', public: true } },
    {
      path: '/portal', component: PortalLayout, meta: { roles: ['STUDENT'] },
      children: [
        { path: '', name: 'portal-home', component: () => import('@/views/portal/PortalHomeView.vue'), meta: { title: '图书共享服务', roles: ['STUDENT'] } },
        { path: 'map', name: 'portal-map', component: () => import('@/views/portal/PortalMapView.vue'), meta: { title: '附近图书馆', roles: ['STUDENT'] } },
        { path: 'borrowings', name: 'portal-borrowings', component: () => import('@/views/portal/PortalBorrowingView.vue'), meta: { title: '我的借阅', roles: ['STUDENT'] } },
      ],
    },
    {
      path: '/admin', component: AppLayout, meta: { roles: ['ADMIN', 'SITE_ADMIN'] },
      children: [
        { path: '', name: 'admin-home', component: () => import('@/views/AdminHomeView.vue'), meta: { title: '管理总览', eyebrow: 'ADMIN OVERVIEW', roles: ['ADMIN', 'SITE_ADMIN'] } },
        { path: 'resources', name: 'admin-resources', component: () => import('@/views/AdminResourcesView.vue'), meta: { title: '资源管理', eyebrow: 'RESOURCE MANAGEMENT', roles: ['ADMIN', 'SITE_ADMIN'] } },
        { path: 'map', name: 'admin-map', component: () => import('@/views/MapView.vue'), meta: { title: 'GIS 空间信息', eyebrow: 'GEOSPATIAL VIEW', roles: ['ADMIN', 'SITE_ADMIN'] } },
        { path: 'monitor', name: 'admin-monitor', component: () => import('@/views/MonitorView.vue'), meta: { title: '节点实时监控', eyebrow: 'NODE OBSERVABILITY', roles: ['ADMIN', 'SITE_ADMIN'] } },
        { path: 'query', name: 'admin-query', component: () => import('@/views/QueryView.vue'), meta: { title: 'SQL 查询工作台', eyebrow: 'DISTRIBUTED QUERY', roles: ['ADMIN'] } },
        { path: 'schema', name: 'admin-schema', component: () => import('@/views/SchemaView.vue'), meta: { title: '逻辑数据字典', eyebrow: 'LOGICAL CATALOG', roles: ['ADMIN'] } },
      ],
    },
    { path: '/:pathMatch(.*)*', redirect: '/login' },
  ],
})

router.beforeEach((to) => {
  const auth = useAuthStore()
  if (to.meta.public) {
    if (to.path === '/login' && auth.authenticated) return auth.isStudent ? '/portal' : '/admin'
    return true
  }
  if (!auth.authenticated) return { path: '/login', query: { redirect: to.fullPath } }
  if (!auth.hasRole(to.meta.roles)) return auth.isStudent ? '/portal' : '/admin'
  return true
})

router.afterEach((to) => {
  document.title = `${String(to.meta.title || '控制台')} · 蓉图云`
})

export default router
