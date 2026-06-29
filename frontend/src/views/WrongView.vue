<template>
  <AppLayout title="错题本" :subtitle="total + ' 题'">

    <!-- 筛选栏 -->
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:16px;flex-wrap:wrap">
      <select class="in" v-model="selectedBank" style="max-width:220px"
        @change="page = 1; fetchWrong()">
        <option value="">全部题库</option>
        <option v-for="b in banks" :key="b.id" :value="b.id">{{ b.title }}</option>
      </select>
      <span style="font-size:13px;color:var(--muted)">按题库筛选</span>
    </div>

    <!-- 加载中 -->
    <div v-if="loading" style="text-align:center;padding:40px;color:var(--muted)">加载中…</div>

    <!-- 空状态 -->
    <div v-else-if="!items.length" class="empty">
      <div class="big">✓</div>错题本是空的，继续保持
    </div>

    <!-- 错题列表 -->
    <template v-else>
      <div v-for="w in items" :key="w.question_id" class="card" style="margin-bottom:10px">
        <!-- 标签行 -->
        <div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap;margin-bottom:8px">
          <span class="pill" :class="w.is_mastered ? 'ok' : 'warn'">
            {{ w.is_mastered ? '已掌握' : '待复习' }}
          </span>
          <span class="pill">错 {{ w.wrong_count }} 次</span>
          <span class="pill">正确答案 {{ w.question.correct_answer }}</span>
          <button class="btn ghost sm" style="margin-left:auto;font-size:12px"
            @click="toggleOpts(w.question_id)">
            {{ expandedOpts.has(w.question_id) ? '收起选项' : '展开选项' }}
          </button>
        </div>

        <!-- 题干 -->
        <div style="font-weight:500;margin-bottom:8px">{{ w.question.content }}</div>

        <!-- 选项（展开后显示） -->
        <div v-if="expandedOpts.has(w.question_id)" style="margin-bottom:8px">
          <div v-for="letter in ['A','B','C','D']" :key="letter"
            :style="{
              display:'flex', alignItems:'flex-start', gap:'8px',
              padding:'7px 10px', marginBottom:'5px', borderRadius:'8px', fontSize:'13px',
              background: w.question.correct_answer === letter ? 'var(--correct-soft)' : 'var(--paper)',
              border: `1px solid ${w.question.correct_answer === letter ? 'var(--correct)' : 'var(--line)'}`,
            }">
            <span :style="{
              flexShrink:0, width:'20px', height:'20px', borderRadius:'50%',
              display:'grid', placeItems:'center', fontSize:'11px', fontWeight:700,
              background: w.question.correct_answer === letter ? 'var(--correct)' : 'var(--line)',
              color: w.question.correct_answer === letter ? '#fff' : 'var(--muted)',
            }">{{ letter }}</span>
            <span :style="{ flex:1, color: w.question.correct_answer === letter ? 'var(--correct)' : 'var(--ink)' }">
              {{ w.question['option_' + letter.toLowerCase()] }}
              <span v-if="w.question.correct_answer === letter"
                style="font-size:11px;margin-left:4px;opacity:.7">✓ 正确答案</span>
            </span>
          </div>
        </div>

        <!-- 解析 -->
        <div v-if="w.question.explanation" class="explain"
          style="margin-bottom:10px;font-size:13px">
          {{ w.question.explanation }}
        </div>

        <!-- 操作按钮 -->
        <div style="display:flex;gap:8px;margin-top:6px">
          <button v-if="!w.is_mastered" class="btn ghost sm"
            @click="markMastered(w.question_id)">标记已掌握</button>
          <button class="btn ghost sm"
            style="color:var(--wrong);border-color:var(--wrong)"
            @click="removeWrong(w.question_id)">从错题本移除</button>
        </div>
      </div>

      <!-- 分页 -->
      <div v-if="totalPages > 1"
        style="display:flex;align-items:center;justify-content:center;gap:10px;margin-top:16px">
        <button class="btn ghost sm" :disabled="page <= 1" @click="page--; fetchWrong()">← 上一页</button>
        <span style="font-size:13px;color:var(--muted)">
          {{ page }} / {{ totalPages }} 页 · 共 {{ total }} 条
        </span>
        <button class="btn ghost sm" :disabled="page >= totalPages" @click="page++; fetchWrong()">下一页 →</button>
      </div>
    </template>
  </AppLayout>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import AppLayout from '@/components/AppLayout.vue'
import { api } from '@/composables/useApi'
import { useToast } from '@/composables/useToast'

const { show: toast } = useToast()

const items        = ref([])
const total        = ref(0)
const page         = ref(1)
const selectedBank = ref('')
const banks        = ref([])
const loading      = ref(true)
const expandedOpts = ref(new Set())

const PAGE_SIZE  = 10
const totalPages = computed(() => Math.ceil(total.value / PAGE_SIZE))

async function fetchWrong() {
  loading.value = true
  try {
    const params = `/wrong?page=${page.value}&size=${PAGE_SIZE}` +
      (selectedBank.value ? `&bank_id=${selectedBank.value}` : '')
    const res = await api(params)
    items.value = res.items
    total.value = res.total
    expandedOpts.value = new Set()
  } catch(e) {
    toast(e.message, true)
  } finally {
    loading.value = false
  }
}

async function fetchBanks() {
  try {
    const { items: b } = await api('/banks?size=50')
    banks.value = b
  } catch {}
}

function toggleOpts(id) {
  const s = new Set(expandedOpts.value)
  s.has(id) ? s.delete(id) : s.add(id)
  expandedOpts.value = s
}

async function markMastered(id) {
  try {
    await api(`/wrong/${id}/master`, { method: 'POST' })
    toast('已标记已掌握')
    await fetchWrong()
  } catch(e) { toast(e.message, true) }
}

async function removeWrong(id) {
  if (!confirm('确定从错题本移除？移除后将不再出现在错题练习中。')) return
  try {
    await api(`/wrong/${id}`, { method: 'DELETE' })
    toast('已从错题本移除')
    await fetchWrong()
  } catch(e) { toast(e.message, true) }
}

onMounted(async () => {
  await Promise.all([fetchWrong(), fetchBanks()])
})
</script>
