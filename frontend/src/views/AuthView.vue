<template>
  <div class="auth">
    <div class="card authcard">
      <div class="brand">
        <div class="mark">Q</div>
        <div><b>QuizForge</b><span>智能题库系统</span></div>
      </div>

      <div class="tabs" v-if="allowRegister">
        <button :class="{ on: tab === 'login' }" @click="tab = 'login'">登录</button>
        <button :class="{ on: tab === 'reg'   }" @click="tab = 'reg'"  >注册</button>
      </div>

      <form @submit.prevent="submit">
        <div class="fld" v-if="tab === 'reg'">
          <label class="f">用户名</label>
          <input class="in" v-model="form.username" required minlength="2" placeholder="至少 2 个字符">
        </div>
        <div class="fld">
          <label class="f">邮箱</label>
          <input class="in" v-model="form.email" type="email" required placeholder="you@example.com">
        </div>
        <div class="fld">
          <label class="f">密码</label>
          <input class="in" v-model="form.password" type="password" required minlength="6" placeholder="至少 6 位">
        </div>
        <button class="btn" style="width:100%" type="submit" :disabled="loading">
          {{ loading ? '请稍候…' : (tab === 'reg' ? '创建账号' : '登录') }}
        </button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useToast } from '@/composables/useToast'
import { api } from '@/composables/useApi'

const auth    = useAuthStore()
const router  = useRouter()
const route   = useRoute()
const { show: toast } = useToast()

const tab     = ref('login')
const loading = ref(false)
const allowRegister = ref(true)

const form = ref({ username: '', email: '', password: '' })

onMounted(async () => {
  try {
    const pc = await api('/admin/public-config', { noAuth: true })
    allowRegister.value = pc.allow_register !== false
  } catch { /* 拿不到配置就按允许注册处理 */ }
})

async function submit() {
  loading.value = true
  try {
    if (tab.value === 'reg') {
      await auth.register(form.value.email, form.value.username, form.value.password)
      toast('注册成功，正在登录…')
    }
    await auth.login(form.value.email, form.value.password)
    const redirect = route.query.redirect || '/'
    router.push(redirect)
  } catch (e) {
    toast(e.message, true)
  } finally {
    loading.value = false
  }
}
</script>
