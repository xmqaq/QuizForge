<template>
  <AppLayout title="学习计划" :subtitle="plans.length + ' 个计划'">

    <!-- 新建计划表单 -->
    <div v-if="showForm" class="card" style="margin-bottom:18px">
      <div style="font-weight:600;margin-bottom:12px">新建学习计划</div>
      <div class="row">
        <div style="flex:2">
          <label class="f">选择题库 *</label>
          <select class="in" v-model="form.bank_id">
            <option value="">请选择…</option>
            <option v-for="b in banks" :key="b.id" :value="b.id">{{ b.title }}</option>
          </select>
        </div>
        <div>
          <label class="f">目标完成日期 *</label>
          <input class="in" type="date" v-model="form.target_date" :min="today">
        </div>
      </div>
      <div class="row" style="margin-top:10px">
        <div>
          <label class="f">每日新题数</label>
          <input class="in" type="number" v-model.number="form.daily_new" min="1" max="100">
        </div>
        <div>
          <label class="f">每日复习数</label>
          <input class="in" type="number" v-model.number="form.daily_review" min="0" max="100">
        </div>
      </div>
      <div style="display:flex;gap:8px;margin-top:12px;justify-content:flex-end">
        <button class="btn sm" :disabled="creating" @click="createPlan">
          {{ creating ? '创建中…' : '创建' }}
        </button>
        <button class="btn ghost sm" @click="showForm = false">取消</button>
      </div>
    </div>

    <div style="margin-bottom:16px">
      <button class="btn" @click="showForm = true">＋ 新建学习计划</button>
    </div>

    <div v-if="loading" style="text-align:center;padding:40px;color:var(--muted)">加载中…</div>

    <div v-else-if="!plans.length" class="empty">
      <div class="big">▷</div>还没有学习计划，创建一个开始有计划地学习
    </div>

    <div v-else>
      <div v-for="p in plans" :key="p.id" class="card" style="margin-bottom:10px">
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px">
          <span style="font-weight:500;font-size:14px">
            {{ bankMap[p.bank_id] || '未知题库' }}
          </span>
          <span class="pill" :class="p.is_active ? 'ok' : ''">
            {{ p.is_active ? (daysLeft(p) > 0 ? daysLeft(p) + ' 天后到期' : '已到期') : '已停用' }}
          </span>
        </div>
        <div style="font-size:13px;color:var(--muted);margin-bottom:10px">
          目标日期：{{ p.target_date }} ·
          每日新题：{{ p.daily_new_questions }} 道 ·
          每日复习：{{ p.daily_review_questions }} 道
        </div>
        <div style="display:flex;gap:8px">
          <button class="btn ghost sm"
            @click="router.push({ name: 'Bank', params: { id: p.bank_id } })">
            去练习
          </button>
          <button class="btn ghost sm"
            style="color:var(--wrong);border-color:var(--wrong);margin-left:auto"
            @click="deletePlan(p.id)">删除计划</button>
        </div>
      </div>
    </div>
  </AppLayout>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import AppLayout from '@/components/AppLayout.vue'
import { api } from '@/composables/useApi'
import { useToast } from '@/composables/useToast'

const router = useRouter()
const { show: toast } = useToast()

const plans    = ref([])
const banks    = ref([])
const bankMap  = ref({})
const loading  = ref(true)
const showForm = ref(false)
const creating = ref(false)
const today    = new Date().toISOString().split('T')[0]

const form = ref({ bank_id: '', target_date: '', daily_new: 10, daily_review: 5 })

function daysLeft(p) {
  return Math.max(0, Math.ceil((new Date(p.target_date) - new Date()) / 86400000))
}

async function fetchAll() {
  loading.value = true
  try {
    const [{ items: pl }, { items: bk }] = await Promise.all([
      api('/study-plans?size=50').catch(() => ({ items: [] })),
      api('/banks?size=100').catch(() => ({ items: [] })),
    ])
    plans.value   = pl
    banks.value   = bk
    bankMap.value = Object.fromEntries(bk.map(b => [b.id, b.title]))
  } finally {
    loading.value = false
  }
}

async function createPlan() {
  if (!form.value.bank_id)     return toast('请选择题库', true)
  if (!form.value.target_date) return toast('请选择目标日期', true)
  creating.value = true
  try {
    await api('/study-plans', { body: {
      bank_id:                form.value.bank_id,
      target_date:            form.value.target_date,
      daily_new_questions:    form.value.daily_new,
      daily_review_questions: form.value.daily_review,
    }})
    toast('学习计划已创建')
    showForm.value = false
    form.value = { bank_id: '', target_date: '', daily_new: 10, daily_review: 5 }
    await fetchAll()
  } catch(e) { toast(e.message, true) }
  finally { creating.value = false }
}

async function deletePlan(id) {
  if (!confirm('确定删除这个学习计划？')) return
  try {
    await api('/study-plans/' + id, { method: 'DELETE' })
    toast('计划已删除')
    await fetchAll()
  } catch(e) { toast(e.message, true) }
}

onMounted(fetchAll)
</script>
