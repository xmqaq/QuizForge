<template>
  <AppLayout :title="bank?.title || ''" :subtitle="bank ? bank.question_count + ' 题' : ''">
    <div v-if="loading" style="text-align:center;padding:40px;color:var(--muted)">加载中…</div>

    <template v-else-if="bank">
      <!-- 手动添加表单 -->
      <div v-if="showManualForm" class="card" style="margin-bottom:18px">
        <div style="font-weight:600;margin-bottom:14px">手动添加题目</div>
        <div class="fld">
          <label class="f">题干 *</label>
          <textarea class="in" v-model="mq.content" rows="3" style="resize:vertical"></textarea>
        </div>
        <div class="row">
          <div><label class="f">选项 A *</label><input class="in" v-model="mq.option_a"></div>
          <div><label class="f">选项 B *</label><input class="in" v-model="mq.option_b"></div>
        </div>
        <div class="row">
          <div><label class="f">选项 C *</label><input class="in" v-model="mq.option_c"></div>
          <div><label class="f">选项 D *</label><input class="in" v-model="mq.option_d"></div>
        </div>
        <div class="row" style="margin-top:8px">
          <div>
            <label class="f">正确答案 *</label>
            <select class="in" v-model="mq.correct_answer">
              <option v-for="l in ['A','B','C','D']" :key="l" :value="l">{{ l }}</option>
            </select>
          </div>
          <div>
            <label class="f">难度</label>
            <select class="in" v-model="mq.difficulty">
              <option value="easy">基础</option>
              <option value="medium">进阶</option>
              <option value="hard">综合</option>
            </select>
          </div>
        </div>
        <div class="fld" style="margin-top:8px">
          <label class="f">解析（可选）</label>
          <textarea class="in" v-model="mq.explanation" rows="2" style="resize:vertical"></textarea>
        </div>
        <div style="display:flex;gap:8px;margin-top:4px">
          <button class="btn sm" :disabled="addingManual" @click="addManual">
            {{ addingManual ? '添加中…' : '添加题目' }}
          </button>
          <button class="btn ghost sm" @click="showManualForm = false">取消</button>
        </div>
      </div>

      <!-- Excel 导入表单 -->
      <div v-if="showImportForm" class="card" style="margin-bottom:18px">
        <div style="font-weight:600;font-size:15px;margin-bottom:6px">导入 Excel 题目</div>
        <div style="font-size:13px;color:var(--muted);margin-bottom:14px">
          请使用标准模板填写后上传，支持一次导入最多 500 道题目。
          <a href="#" style="color:var(--accent);margin-left:6px" @click.prevent="downloadTemplate">
            下载模板 ↓
          </a>
        </div>
        <div class="row" style="align-items:flex-end;gap:10px">
          <div style="flex:2">
            <label class="f">选择 Excel 文件</label>
            <input class="in" type="file" ref="xlFileRef" accept=".xlsx,.xls">
          </div>
          <div style="flex:none">
            <label class="f" style="visibility:hidden">操作</label>
            <label style="font-size:13px;display:flex;align-items:center;gap:6px;cursor:pointer">
              <input type="checkbox" v-model="xlAutoApprove"> 自动审核通过
            </label>
          </div>
        </div>
        <div v-if="xlErrors.length" style="margin-top:10px;font-size:13px;color:var(--wrong)">
          <div v-for="err in xlErrors" :key="err">{{ err }}</div>
        </div>
        <div style="display:flex;gap:8px;margin-top:12px">
          <button class="btn sm" :disabled="importing" @click="importXl">
            {{ importing ? '导入中…' : '开始导入' }}
          </button>
          <button class="btn ghost sm" @click="showImportForm = false; xlErrors = []">取消</button>
        </div>
      </div>

      <!-- 操作按钮行 -->
      <div style="display:flex;gap:10px;margin-bottom:20px;flex-wrap:wrap">
        <button class="btn" :disabled="!bank.question_count" @click="startQuiz">开始答题</button>
        <button class="btn ghost" @click="router.push({ name: 'Banks' })">← 返回题库</button>
        <button class="btn ghost" @click="showManualForm = !showManualForm">＋ 手动添加题目</button>
        <button class="btn ghost" @click="showImportForm = !showImportForm">⬆ 导入 Excel</button>
        <button class="btn ghost" :disabled="!bank.question_count" @click="exportXl">⬇ 导出 Excel</button>
      </div>

      <!-- 题库元信息 -->
      <div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin-bottom:16px;margin-top:-8px">
        <span v-if="bank.industry" class="pill">{{ L('industry', bank.industry) }}</span>
        <span class="pill" :class="{ ok: bank.status === 'published' }">{{ L('status', bank.status) }}</span>
        <span v-if="bank.description" style="font-size:13px;color:var(--muted)">{{ bank.description }}</span>
        <span style="font-size:12px;color:var(--muted);margin-left:auto">
          创建于 {{ new Date(bank.created_at).toLocaleDateString('zh-CN') }}
        </span>
      </div>

      <AiGenerator :bank-id="bankId" :bank-title="bank.title" @done="fetchQuestions" />

      <QuestionList
        :items="questions"
        @approve="approveQ"
        @reject="rejectQ"
        @delete="deleteQ"
        @bulk="doBulk"
        @updated="fetchQuestions"
      />
    </template>
  </AppLayout>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppLayout    from '@/components/AppLayout.vue'
import AiGenerator  from '@/components/AiGenerator.vue'
import QuestionList from '@/components/QuestionList.vue'
import { api, downloadFile } from '@/composables/useApi'
import { useToast } from '@/composables/useToast'
import { L }        from '@/utils'

const route  = useRoute()
const router = useRouter()
const { show: toast } = useToast()

const bankId    = computed(() => route.params.id)
const bank      = ref(null)
const questions = ref([])
const loading   = ref(true)

const showManualForm = ref(false)
const addingManual   = ref(false)
const mq = ref({ content:'', option_a:'', option_b:'', option_c:'', option_d:'', correct_answer:'A', difficulty:'medium', explanation:'' })

const showImportForm = ref(false)
const xlFileRef      = ref(null)
const xlAutoApprove  = ref(true)
const importing      = ref(false)
const xlErrors       = ref([])

async function fetchBank() {
  bank.value = await api('/banks/' + bankId.value)
}

async function fetchQuestions() {
  const { items } = await api(`/questions?bank_id=${bankId.value}&size=100`)
  questions.value = items
  if (bank.value) bank.value.question_count = items.length
}

async function approveQ(id) {
  try {
    await api('/questions/' + id + '/approve', { method: 'POST' })
    toast('已通过')
    await fetchQuestions()
  } catch(e) { toast(e.message, true) }
}

async function rejectQ(id) {
  try {
    await api('/questions/' + id + '/reject', { method: 'POST' })
    toast('已拒绝')
    await fetchQuestions()
  } catch(e) { toast(e.message, true) }
}

async function deleteQ(id, preview) {
  if (!confirm(`确定删除题目「${preview}…」？`)) return
  try {
    await api('/questions/' + id, { method: 'DELETE' })
    toast('题目已删除')
    await fetchQuestions()
  } catch(e) { toast(e.message, true) }
}

async function doBulk(action, selectedSet) {
  const ids = [...selectedSet]
  const labels = { approve:'批量通过', reject:'批量拒绝', delete:'批量删除' }
  if (!confirm(`确定${labels[action]}选中的 ${ids.length} 道题目？`)) return
  try {
    const res = await api('/questions/bulk', { body: { question_ids: ids, action } })
    toast(res.detail)
    await fetchQuestions()
  } catch(e) { toast(e.message, true) }
}

async function addManual() {
  const { content, option_a, option_b, option_c, option_d } = mq.value
  if (!content || !option_a || !option_b || !option_c || !option_d)
    return toast('题干和四个选项不能为空', true)
  addingManual.value = true
  try {
    await api('/questions', { body: {
      bank_id:        bankId.value,
      content:        content.trim(),
      option_a:       option_a.trim(),
      option_b:       option_b.trim(),
      option_c:       option_c.trim(),
      option_d:       option_d.trim(),
      correct_answer: mq.value.correct_answer,
      difficulty:     mq.value.difficulty,
      explanation:    mq.value.explanation?.trim() || null,
      status:         'approved',
    }})
    toast('题目已添加')
    showManualForm.value = false
    mq.value = { content:'', option_a:'', option_b:'', option_c:'', option_d:'', correct_answer:'A', difficulty:'medium', explanation:'' }
    await fetchQuestions()
  } catch(e) { toast(e.message, true) }
  finally { addingManual.value = false }
}

async function downloadTemplate() {
  try {
    await downloadFile('/excel/template', 'quizforge_import_template.xlsx')
  } catch(e) { toast('下载失败：' + e.message, true) }
}

async function importXl() {
  const file = xlFileRef.value?.files[0]
  if (!file) return toast('请先选择 Excel 文件', true)
  importing.value = true
  xlErrors.value  = []
  try {
    const fd = new FormData()
    fd.append('file', file)
    const res = await api(`/excel/${bankId.value}/import?auto_approve=${xlAutoApprove.value}`, { form: fd })
    toast(res.detail)
    if (res.errors?.length) {
      xlErrors.value = res.errors
    } else {
      showImportForm.value = false
    }
    await fetchQuestions()
  } catch(e) { toast(e.message, true) }
  finally { importing.value = false }
}

async function exportXl() {
  try {
    await downloadFile(`/excel/${bankId.value}/export`, (bank.value?.title || 'questions') + '.xlsx')
    toast('导出成功')
  } catch(e) { toast(e.message, true) }
}

function startQuiz() {
  router.push({ name: 'Quiz', query: { bankId: bankId.value, title: bank.value.title } })
}

onMounted(async () => {
  loading.value = true
  try {
    await Promise.all([fetchBank(), fetchQuestions()])
  } finally {
    loading.value = false
  }
})
</script>
