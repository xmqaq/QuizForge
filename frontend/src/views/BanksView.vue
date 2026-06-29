<template>
  <AppLayout title="题库" :subtitle="subtitle">
    <div v-if="showNewForm" class="card" style="margin-bottom:18px">
      <div style="font-weight:600;margin-bottom:12px">新建题库</div>
      <div class="row">
        <div style="flex:2">
          <label class="f">标题 *</label>
          <input class="in" v-model="newForm.title" placeholder="如：英语四级备考">
        </div>
        <div style="flex:2">
          <label class="f">描述（可选）</label>
          <input class="in" v-model="newForm.description">
        </div>
        <div style="flex:1;min-width:110px">
          <label class="f">行业分类</label>
          <select class="in" v-model="newForm.industry">
            <option value="it">IT / 网络安全</option>
            <option value="language">语言考试</option>
            <option value="medical">医疗卫生</option>
            <option value="finance">金融财会</option>
            <option value="education">教育培训</option>
            <option value="construction">建筑工程</option>
            <option value="other">其他</option>
          </select>
        </div>
      </div>
      <div class="row" style="margin-top:12px;justify-content:flex-end">
        <div style="flex:none;display:flex;gap:8px">
          <button class="btn sm" :disabled="creating" @click="createBank">
            {{ creating ? '创建中…' : '创建' }}
          </button>
          <button class="btn ghost sm" @click="showNewForm = false">取消</button>
        </div>
      </div>
    </div>

    <div style="margin-bottom:16px">
      <button class="btn" @click="showNewForm = true">＋ 新建题库</button>
    </div>

    <div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:16px">
      <button v-for="[v, l] in IND_TABS" :key="v"
        class="btn sm" :class="filter === v ? '' : 'ghost'"
        :style="filter === v ? 'background:var(--accent);border-color:var(--accent)' : ''"
        @click="changeFilter(v)">
        {{ l }}
      </button>
    </div>

    <div style="margin-bottom:14px">
      <input class="in" v-model="searchKw" placeholder="搜索题库名称…" style="max-width:280px">
    </div>

    <div v-if="loading" style="text-align:center;padding:40px;color:var(--muted)">加载中…</div>

    <template v-else>
      <div v-if="!items.length && !filter && !searchKw" style="padding:40px 0">
        <div style="max-width:480px;margin:0 auto">
          <div style="font-size:24px;text-align:center;margin-bottom:20px;opacity:.4">▦</div>
          <div style="font-size:16px;font-weight:600;text-align:center;margin-bottom:8px">还没有题库</div>
          <div style="font-size:13px;color:var(--muted);text-align:center;margin-bottom:24px">三步开始你的学习之旅</div>
          <div style="display:flex;flex-direction:column;gap:10px">
            <div v-for="[t, d, isNew] in GUIDE_STEPS" :key="t"
              class="card" style="display:flex;align-items:center;gap:14px;padding:14px 16px">
              <div style="font-weight:600;font-size:14px;min-width:120px">{{ t }}</div>
              <div style="font-size:13px;color:var(--muted);flex:1">{{ d }}</div>
              <button v-if="isNew" class="btn sm" @click="showNewForm = true">新建</button>
            </div>
          </div>
        </div>
      </div>

      <div v-else-if="!filtered.length" class="empty">
        <div class="big">▦</div>没有匹配的题库
      </div>

      <div v-else class="grid cols">
        <BankCard v-for="bank in filtered" :key="bank.id"
          :bank="bank"
          @click="goBank(bank)"
          @delete="deleteBank(bank)" />
      </div>
    </template>
  </AppLayout>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import AppLayout from '@/components/AppLayout.vue'
import BankCard  from '@/components/BankCard.vue'
import { api }   from '@/composables/useApi'
import { useToast } from '@/composables/useToast'

const router = useRouter()
const { show: toast } = useToast()

const items       = ref([])
const loading     = ref(true)
const filter      = ref('')
const searchKw    = ref('')
const showNewForm = ref(false)
const creating    = ref(false)
const newForm     = ref({ title: '', description: '', industry: 'it' })

const IND_TABS = [
  ['', '全部'], ['it', 'IT'], ['medical', '医疗'], ['finance', '金融'],
  ['education', '教育'], ['construction', '建筑'], ['language', '语言'], ['other', '其他'],
]

const GUIDE_STEPS = [
  ['① 新建题库', '按行业分类创建你的专属题库', true],
  ['② AI 生成题目', '输入知识点，AI 自动出题或上传文档生成', false],
  ['③ 开始答题练习', '错题自动记录，智能追踪学习进度', false],
]

const subtitle = computed(() => items.value.length + ' 个题库')

const filtered = computed(() => {
  const kw = searchKw.value.trim().toLowerCase()
  return items.value.filter(b => !kw || b.title.toLowerCase().includes(kw))
})

async function fetchBanks(ind = filter.value) {
  loading.value = true
  try {
    const url = ind ? `/banks?size=100&industry=${ind}` : '/banks?size=100'
    const { items: data } = await api(url)
    items.value = data
  } catch(e) {
    toast(e.message, true)
  } finally {
    loading.value = false
  }
}

async function changeFilter(ind) {
  filter.value = ind
  await fetchBanks(ind)
}

async function createBank() {
  if (!newForm.value.title.trim()) return toast('请填写题库标题', true)
  creating.value = true
  try {
    await api('/banks', { body: {
      title:       newForm.value.title.trim(),
      description: newForm.value.description.trim() || null,
      industry:    newForm.value.industry,
      status:      'published',
    }})
    toast('题库已创建')
    showNewForm.value = false
    newForm.value = { title: '', description: '', industry: 'it' }
    await fetchBanks()
  } catch(e) {
    toast(e.message, true)
  } finally {
    creating.value = false
  }
}

async function deleteBank(bank) {
  if (!confirm(`确定删除题库「${bank.title}」？\n题库内所有题目将一并删除，此操作不可恢复。`)) return
  try {
    await api('/banks/' + bank.id, { method: 'DELETE' })
    toast('题库已删除')
    items.value = items.value.filter(b => b.id !== bank.id)
  } catch(e) {
    toast(e.message, true)
  }
}

function goBank(bank) {
  router.push({ name: 'Bank', params: { id: bank.id } })
}

onMounted(fetchBanks)
</script>
