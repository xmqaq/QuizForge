import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
  { path: '/login',  name: 'Login',   component: () => import('@/views/AuthView.vue'),        meta: { public: true } },
  { path: '/',       name: 'Banks',   component: () => import('@/views/BanksView.vue'),        meta: { requiresAuth: true } },
  { path: '/bank/:id', name: 'Bank',  component: () => import('@/views/BankDetailView.vue'),   meta: { requiresAuth: true } },
  { path: '/quiz',   name: 'Quiz',    component: () => import('@/views/QuizView.vue'),          meta: { requiresAuth: true } },
  { path: '/summary',name: 'Summary', component: () => import('@/views/QuizSummaryView.vue'),  meta: { requiresAuth: true } },
  { path: '/wrong',  name: 'Wrong',   component: () => import('@/views/WrongView.vue'),         meta: { requiresAuth: true } },
  { path: '/stats',  name: 'Stats',   component: () => import('@/views/StatsView.vue'),         meta: { requiresAuth: true } },
  { path: '/plaza',  name: 'Plaza',   component: () => import('@/views/PlazaView.vue'),         meta: { public: true } },
  { path: '/plan',   name: 'Plan',    component: () => import('@/views/PlanView.vue'),           meta: { requiresAuth: true } },
  { path: '/admin',  name: 'Admin',   component: () => import('@/views/AdminView.vue'),          meta: { requiresAuth: true, roles: ['admin'] } },
  { path: '/:pathMatch(.*)*', redirect: '/' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to, _from) => {
  const auth = useAuthStore()

  if (to.meta.requiresAuth && !auth.token) {
    return { name: 'Login', query: { redirect: to.fullPath } }
  }

  if (auth.token && !auth.user) {
    try {
      await auth.fetchMe()
    } catch {
      auth.logout()
      return { name: 'Login' }
    }
  }

  if (to.meta.roles && !to.meta.roles.includes(auth.user?.role)) {
    return { name: 'Banks' }
  }

  if (to.name === 'Login' && auth.isLoggedIn) {
    return { name: 'Banks' }
  }
})

export default router
