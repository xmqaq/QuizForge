<template>
  <div class="app">
    <aside class="rail">
      <div class="brand">
        <div class="mark">Q</div>
        <div><b>QuizForge</b><span>智能题库系统</span></div>
      </div>

      <button
        v-for="nav in visibleNav"
        :key="nav.v"
        class="nav"
        :class="{ on: isActive(nav.v) }"
        @click="go(nav.v)"
      >
        <span class="ic">{{ nav.ic }}</span>{{ nav.l }}
      </button>

      <div class="spacer"></div>

      <div class="userbar">
        <div class="avatar">{{ avatarLetter }}</div>
        <div class="userinfo">
          <div class="uname">{{ auth.user?.username }}</div>
          <div class="urole">{{ roleLabel }}</div>
        </div>
        <button class="signout" title="退出登录" @click="handleLogout">↪</button>
      </div>
    </aside>

    <main class="main">
      <div class="head">
        <h1>{{ title }}</h1>
        <div class="sub">{{ subtitle }}</div>
      </div>
      <div>
        <slot />
      </div>
    </main>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useQuizStore } from '@/stores/quiz'

const props = defineProps({
  title:    { type: String, default: '' },
  subtitle: { type: String, default: '' },
})

const auth   = useAuthStore()
const quiz   = useQuizStore()
const router = useRouter()
const route  = useRoute()

const NAV = [
  { v: 'Banks',  l: '题库',     ic: '▦', role: null },
  { v: 'Wrong',  l: '错题本',   ic: '✕', role: null },
  { v: 'Stats',  l: '统计',     ic: '▤', role: null },
  { v: 'Plan',   l: '学习计划', ic: '▷', role: null },
  { v: 'Plaza',  l: '题库广场', ic: '◈', role: null },
  { v: 'Admin',  l: '系统设置', ic: '⚙', role: 'admin' },
]

const visibleNav = computed(() =>
  NAV.filter(n => !n.role || auth.user?.role === n.role)
)

const isActive = (routeName) => route.name === routeName

const avatarLetter = computed(() =>
  (auth.user?.username || '?')[0].toUpperCase()
)

const ROLE_LABEL = { admin: '管理员', editor: '编辑', user: '用户' }
const roleLabel = computed(() =>
  ROLE_LABEL[auth.user?.role] || auth.user?.role || ''
)

function go(routeName) {
  quiz.reset()
  router.push({ name: routeName })
}

function handleLogout() {
  quiz.reset()
  auth.logout()
  router.push({ name: 'Login' })
}
</script>
