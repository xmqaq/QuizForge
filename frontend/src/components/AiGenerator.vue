<template>
  <div class="card" style="margin-bottom:24px">
    <div style="font-weight:700;font-size:15px;margin-bottom:3px">⚡ AI 出题</div>
    <div style="font-size:12px;color:var(--muted);margin-bottom:14px">
      选择或输入知识点，AI 生成覆盖完整的选择题
    </div>

    <div class="row" style="align-items:flex-end;gap:10px">
      <div style="flex:3">
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:6px">
          <label class="f" style="margin:0">知识点 / 主题</label>
          <button style="font-size:12px;padding:3px 10px;border-radius:99px;border:1px solid var(--line);
            background:var(--card);color:var(--accent);cursor:pointer"
            :disabled="suggesting" @click="suggestTopics">
            {{ suggesting ? '推荐中…' : '✨ AI 推荐' }}
          </button>
        </div>
        <input class="in" v-model="topic" :placeholder="placeholder">
      </div>
      <div style="min-width:88px">
        <label class="f">难度</label>
        <select class="in" v-model="difficulty">
          <option value="easy">基础</option>
          <option value="medium">进阶</option>
          <option value="hard">综合</option>
        </select>
      </div>
      <div style="min-width:72px">
        <label class="f">数量</label>
        <input class="in" v-model.number="count" type="number" min="1" max="100">
      </div>
    </div>

    <div v-if="suggestedTopics.length"
      style="margin-top:10px;padding:10px;background:var(--paper);border-radius:9px">
      <div style="font-size:12px;color:var(--muted);margin-bottom:8px">
        点击勾选知识点（可多选），自动填入上方输入框：
      </div>
      <div style="display:flex;gap:6px;flex-wrap:wrap">
        <button v-for="t in suggestedTopics" :key="t"
          class="topic-tag" :class="{ on: selectedTopics.has(t) }"
          @click="toggleTopic(t)">
          {{ t }}
        </button>
      </div>
    </div>

    <div style="display:flex;align-items:center;margin-top:12px">
      <label style="font-size:13px;color:var(--muted);flex:1;display:flex;align-items:center;gap:6px">
        <input type="checkbox" v-model="autoApprove"> 自动审核通过
      </label>
      <button class="btn" :disabled="generating" @click="runAI">生成题目</button>
    </div>

    <div style="border-top:1px dashed var(--line);margin:20px 0"></div>

    <div style="font-weight:700;font-size:15px;margin-bottom:3px">📄 上传知识文档出题</div>
    <div style="font-size:12px;color:var(--muted);margin-bottom:12px">
      AI 将读取文档内容作为知识来源，据此生成选择题（支持 PDF / Word / TXT / MD）
    </div>

    <input class="in" type="file" ref="fileInput" accept=".pdf,.docx,.txt,.md"
      style="margin-bottom:10px">
    <div class="row" style="align-items:flex-end;gap:10px">
      <div style="min-width:88px">
        <label class="f">难度</label>
        <select class="in" v-model="fileDifficulty">
          <option value="easy">基础</option>
          <option value="medium">进阶</option>
          <option value="hard">综合</option>
        </select>
      </div>
      <div style="min-width:72px">
        <label class="f">生成数量</label>
        <input class="in" v-model.number="fileCount" type="number" min="1" max="100">
      </div>
      <div style="flex:none">
        <label class="f" style="visibility:hidden">操作</label>
        <button class="btn ghost" :disabled="generating" @click="runAIFile">
          上传并生成题目
        </button>
      </div>
    </div>

    <div v-if="showProgress" style="margin-top:16px">
      <div class="progress" style="margin-bottom:8px">
        <i :style="{ width: progressPct + '%', transition: 'width .6s ease-out' }"></i>
      </div>
      <div style="font-size:13px;color:var(--muted)">{{ progressMsg }}</div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { api } from '@/composables/useApi'
import { useToast } from '@/composables/useToast'

const props = defineProps({
  bankId:    { type: String, required: true },
  bankTitle: { type: String, default: '' },
})
const emit = defineEmits(['done'])

const { show: toast } = useToast()

const topic       = ref('')
const difficulty  = ref('medium')
const count       = ref(10)
const autoApprove = ref(true)

const fileInput      = ref(null)
const fileDifficulty = ref('medium')
const fileCount      = ref(10)

const suggesting      = ref(false)
const suggestedTopics = ref([])
const selectedTopics  = ref(new Set())

const generating   = ref(false)
const showProgress = ref(false)
const progressPct  = ref(0)
const progressMsg  = ref('')

const TOPIC_MAP = [
  [["英语四级","CET4","四级"], "如：阅读理解技巧、完形填空、翻译技巧"],
  [["英语六级","CET6","六级"], "如：长篇阅读、听力理解、写作论证结构"],
  [["雅思","IELTS"], "如：Task 2 议论文写作、阅读匹配题、听力填空"],
  [["托福","TOEFL"], "如：综合写作、阅读细节题、学术词汇"],
  [["网络安全","信息安全","安全"], "如：SQL 注入原理与防御、XSS 攻击、密码学基础"],
  [["CTF"], "如：Web 漏洞利用、逆向工程基础、密码学题型"],
  [["软考"], "如：计算机网络基础、数据结构与算法、操作系统原理"],
  [["CISP","CISSP"], "如：信息安全管理、风险评估方法、密码技术应用"],
  [["医","执业","护士","药师"], "如：内科疾病诊断、药物作用机制、临床检验解读"],
  [["建筑","一建","二建","注册建筑"], "如：建筑结构力学、施工质量控制、工程造价管理"],
  [["会计","CPA","税务"], "如：资产负债表编制、会计分录、税务处理"],
  [["法律","法考","司法"], "如：合同法基本原则、侵权责任认定、诉讼程序"],
  [["驾","驾照","驾驶"], "如：交通标志识别、行车安全规范、违规处罚规定"],
  [["教师","教资"], "如：教育学基本理论、课堂管理策略、教学设计方法"],
  [["习近平","党政","思政","政治"], "如：新时代中国特色社会主义、五大发展理念、党的建设"],
]

const placeholder = computed(() => {
  const t = props.bankTitle
  for (const [keys, hint] of TOPIC_MAP) {
    if (keys.some(k => t.includes(k))) return hint
  }
  return `如：${t}核心概念、重点考点、常见题型`
})

function toggleTopic(t) {
  const s = new Set(selectedTopics.value)
  s.has(t) ? s.delete(t) : s.add(t)
  selectedTopics.value = s
  topic.value = [...s].join('、')
}

async function suggestTopics() {
  suggesting.value = true
  try {
    const res = await api('/ai/suggest-topics', { body: { bank_title: props.bankTitle } })
    suggestedTopics.value = res.topics || []
    selectedTopics.value  = new Set()
    toast(`已推荐 ${res.topics.length} 个知识点，可多选`)
  } catch(e) {
    toast('推荐失败：' + e.message, true)
  } finally {
    suggesting.value = false
  }
}

const STAGE_CONFIG = {
  parsing_file: { text: ()      => '📄 正在解析文档内容…',               useReal: false, cap: 20 },
  ai_thinking:  { text: (t)     => `⚡ AI 正在生成 ${t} 道题目，请稍候…`, useReal: false, cap: 60 },
  saving:       { text: (t, g)  => `💾 正在保存… 已完成 ${g} / ${t} 题`,  useReal: true,  cap: 99 },
}

async function pollGenerate(taskId) {
  let fake = 0
  let cap  = 30

  const fakeTick = setInterval(() => {
    if (fake < cap) {
      fake += (cap - fake) * 0.06
      progressPct.value = Math.min(fake, cap)
    }
  }, 250)

  progressMsg.value = '⏳ 提交任务，等待队列…'

  try {
    for (let i = 0; i < 80; i++) {
      await new Promise(r => setTimeout(r, 1500))
      let st
      try { st = await api('/ai/task/' + taskId) } catch { continue }

      const generated = st.generated || 0
      const total     = st.total || 0
      const stage     = st.stage || (st.status === 'processing' ? 'ai_thinking' : st.status)

      if (st.status === 'queued') {
        progressMsg.value = '⏳ 排队等待中，即将开始…'
        continue
      }

      if (st.status === 'processing') {
        const cfg = STAGE_CONFIG[stage]
        if (cfg) {
          cap = cfg.cap
          if (cfg.useReal && total > 0) {
            const pct = 50 + (generated / total) * 49
            fake = Math.max(fake, pct)
            progressPct.value = fake
            progressMsg.value = cfg.text(total, generated)
          } else {
            progressMsg.value = cfg.text(total, generated)
          }
        } else {
          progressMsg.value = total > 0
            ? `⚡ 生成中… 已完成 ${generated} / ${total} 题`
            : '⚡ AI 正在生成题目，请稍候…'
        }
        continue
      }

      if (st.status === 'done') {
        clearInterval(fakeTick)
        progressPct.value = 100
        progressMsg.value = `✓ 生成完成，共 ${generated} 道题`
        toast(`✓ 成功生成 ${generated} 道题目`)
        setTimeout(() => emit('done'), 800)
        return
      }

      if (st.status === 'failed') {
        clearInterval(fakeTick)
        throw new Error(st.error_message || '生成失败，请重试')
      }
    }
    clearInterval(fakeTick)
    progressMsg.value = '⏱ 生成耗时较长，题目在后台继续生成，请稍后刷新查看'
    toast('生成耗时较长，请稍后刷新题库查看')
  } catch(e) {
    clearInterval(fakeTick)
    progressMsg.value = '✕ ' + e.message
    throw e
  }
}

async function runAI() {
  if (generating.value) return
  if (!topic.value.trim()) return toast('请填写或选择知识点主题', true)
  generating.value  = true
  showProgress.value = true
  progressPct.value  = 0
  progressMsg.value  = '⏳ 提交任务…'
  try {
    const { task_id } = await api('/ai/generate', { body: {
      bank_id:      props.bankId,
      topic:        topic.value.trim(),
      difficulty:   difficulty.value,
      count:        count.value,
      auto_approve: autoApprove.value,
    }})
    await pollGenerate(task_id)
  } catch(e) {
    toast(e.message, true)
    progressMsg.value = '✕ ' + e.message
  } finally {
    generating.value = false
  }
}

async function runAIFile() {
  if (generating.value) return
  const file = fileInput.value?.files[0]
  if (!file) return toast('请先选择文件', true)
  generating.value  = true
  showProgress.value = true
  progressPct.value  = 0
  progressMsg.value  = '⏳ 上传并解析文件…'
  try {
    const fd = new FormData()
    fd.append('bank_id',      props.bankId)
    fd.append('difficulty',   fileDifficulty.value)
    fd.append('count',        String(fileCount.value))
    fd.append('auto_approve', String(autoApprove.value))
    fd.append('file', file)
    const { task_id } = await api('/ai/generate-from-file', { form: fd })
    await pollGenerate(task_id)
  } catch(e) {
    toast(e.message, true)
    progressMsg.value = '✕ ' + e.message
  } finally {
    generating.value = false
  }
}
</script>
