import { createRouter, createWebHistory } from 'vue-router'
import { routes } from 'vue-router/auto-routes'
import { clearToken, getToken } from '@/api/tokens'
import { safeReturn } from '@/platform'
import { cardOnly } from '@/platform/release-mode'
import { cardOnlyRedirect } from './card-only'
export const router = createRouter({ history: createWebHistory(import.meta.env.BASE_URL), routes, scrollBehavior: () => ({ top: 0 }) })
if (cardOnly) router.beforeEach(cardOnlyRedirect)
router.beforeEach((to) => {
 if (!to.path.startsWith('/staff/')) return
 if (!getToken('staff') && to.path !== '/staff/login') return { path: '/staff/login', query: { redirect: to.fullPath } }
 if (getToken('staff') && localStorage.getItem('shuke.must-change') === 'true' && to.path !== '/staff/login') return { path: '/staff/login', query: { change: '1', redirect: to.fullPath } }
})
window.addEventListener('staff-session-expired', () => {
 clearToken('staff'); router.replace({ path: '/staff/login', query: { redirect: safeReturn(router.currentRoute.value.fullPath) } })
})
