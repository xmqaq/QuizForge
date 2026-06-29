<template>
  <AppLayout title="题库广场" :subtitle="total + ' 个公开题库'">

    <!-- 搜索 + 排序 -->
    <div style="display:flex;gap:10px;align-items:center;margin-bottom:14px;flex-wrap:wrap">
      <input class="in" v-model="searchKw" placeholder="搜索题库名称…"
        style="max-width:260px;flex:1" @input="onSearch">
      <div style="display:flex;gap:6px;flex:none">
        <button class="btn sm" :class="sort !== 'hot' ? 'ghost' : ''"
          @click="sort = 'hot'; page = 1; fetchPlaza()">🔥 热度</button>
        <button class="btn sm" :class="sort !== 'new' ? 'ghost' : ''"
          @click="sort = 'new'; page = 1; fetchPlaza()">🆕 最新</button>
      </div>
    </div>

    <!-- 行业筛选 -->
    <div style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:16px">
      <button v-for="[v, l] in IND_TABS" :key="v"
        class="btn sm" :class="industry !== v ? 'ghost' : ''"
        @click="industry = v; page = 1; fetchPlaza()">{{ l }}</button>
    </div>

    <div v-if="loading" style="text-align:center;padding:40px;color:var(--muted)">加载中…</div>

    <template v-else>
      <div v-if="!items.length" class="empty" style="grid-column:1/-1">
        <div class="big">◈</div>暂无符合条件的公开题库
      </div>
      <div v-else class="grid cols">
        <div v-for="b in items" :key="b.id"
          class="card bank" style="cursor:pointer" @click="goBank(b)">
          <div style="display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:10px">
            <span v-if="b.industry" class="pill"
              :style="{ background: IND_COLORS[b.industry]?.[0], color: IND_COLORS[b.industry]?.[1], border: 'none' }">
              {{ L('industry', b.industry) }}
            </span>
            <span v-else></span>
            <span style="font-size:12px;color:var(--muted);font-family:var(--mono)">
              {{ b.question_count }} 题
            </span>
          </div>
          <h3 style="margin:0 0 6px;font-size:15px;font-weight:600;line-height:1.4">{{ b.title }}</h3>
          <div style="font-size:13px;color:var(--muted);min-height:18px;margin-bottom:14px">
            <span v-if="b.description">{{ b.description }}</span>
            <span v-else style="opacity:.4">暂无描述</span>
          </div>
          <div style="border-top:1px solid var(--line);padding-top:10px;
            display:flex;align-items:center;justify-content:space-between">
            <span class="bank-count-big" style="font-size:22px">
              {{ b.question_count }}<small> 道题</small>
            </span>
            <button class="btn sm" style="font-size:12px" @click.stop="startPractice(b)">
              开始练习
            </button>
          </div>
        </div>
      </div>

      <!-- 分页 -->
      <div v-if="totalPages > 1"
        style="display:flex;align-items:center;justify-content:center;gap:10px;margin-top:20px">
        <button class="btn ghost sm" :disabled="page <= 1"
          @click="page--; fetchPlaza()">← 上一页</button>
        <span style="font-size:13px;color:var(--muted)">
          {{ page }} / {{ totalPages }} 页 · 共 {{ total }} 个题库
        </span>
        <button class="btn ghost sm" :disabled="page >= totalPages"
          @click="page++; fetchPlaza()">下一页 →</button>
      </div>
    </template>
  </AppLayout>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import AppLayout from '@/components/AppLayout.vue'
import { api } from '@/composables/useApi'
import { useToast } from '@/composables/useToast'
import { useAuthStore } from '@/stores/auth'
import { L } from '@/utils'

const router = useRouter()
const auth   = useAuthStore()
const { show: toast } = useToast()

const items    = ref([])
const total    = ref(0)
const page     = ref(1)
const sort     = ref('hot')
const industry = ref('')
const searchKw = ref('')
const loading  = ref(true)

const PAGE_SIZE  = 18
const totalPages = computed(() => Math.ceil(total.value / PAGE_SIZE))

const IND_TABS = [
  ['', '全部'], ['it', 'IT'], ['medical', '医疗'], ['finance', '金融'],
  ['education', '教育'], ['construction', '建筑'], ['language', '语言'], ['other', '其他'],
]

const IND_COLORS = {
  it:           ['#E9ECFF', '#2F4BFF'],
  medical:      ['#E4F4ED', '#1E9E6A'],
  finance:      ['#FFF3E0', '#B26A00'],
  education:    ['#E8F5E9', '#2E7D32'],
  construction: ['#FBE9EA', '#C62828'],
  language:     ['#F3E5F5', '#6A1B9A'],
  other:        ['#F4F5F7', '#6B7280'],
}

let searchTimer = null
function onSearch() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => { page.value = 1; fetchPlaza() }, 400)
}

async function fetchPlaza() {
  loading.value = true
  try {
    const params = new URLSearchParams({
      page: String(page.value), size: String(PAGE_SIZE), sort: sort.value,
    })
    if (industry.value) params.set('industry', industry.value)
    if (searchKw.value.trim()) params.set('search', searchKw.value.trim())
    const res = await api('/banks/public?' + params, { noAuth: true })
    items.value = res.items
    total.value = res.total
  } catch(e) {
    toast(e.message, true)
  } finally {
    loading.value = false
  }
}

function goBank(b) {
  if (!auth.isLoggedIn) return toast('请先登录后再查看题库详情', true)
  router.push({ name: 'Bank', params: { id: b.id } })
}

function startPractice(b) {
  if (!auth.isLoggedIn) return toast('请先登录后再开始练习', true)
  router.push({ name: 'Quiz', query: { bankId: b.id, title: b.title, mode: 'random' } })
}

onMounted(fetchPlaza)
</script>
