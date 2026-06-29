<template>
  <AppLayout :title="quiz.title ? '答题 · ' + quiz.title : '答题'" :subtitle="modeLabel">
    <div v-if="loading" style="text-align:center;padding:40px;color:var(--muted)">加载中…</div>

    <div v-else-if="q" class="quiz-layout">
      <!-- Question card -->
      <div class="card" style="max-width:640px">
        <div class="qmeta">
          <span class="n">第 {{ pad(quiz.index + 1) }} / {{ pad(quiz.questions.length) }} 题</span>
          <span style="display:flex;gap:8px;align-items:center">
            <span class="qtimer" :class="{ slow: qTimerSec > 30 }">{{ qTimerSec }}s</span>
            <span v-if="quiz.deadline" class="pill"
              :style="globalRem <= 30 ? 'color:var(--wrong)' : ''">
              ⏱ {{ formatTime(globalRem) }}
            </span>
            <span class="pill">{{ L('difficulty', q.difficulty) }}</span>
          </span>
        </div>

        <div class="progress">
          <i :style="{ width: ((quiz.index + 1) / quiz.questions.length * 100) + '%' }"></i>
        </div>

        <p class="stem">{{ q.content }}</p>

        <div v-for="letter in ['A','B','C','D']" :key="letter"
          class="opt" :class="optClass(letter)"
          @click="pickAnswer(letter)">
          <div class="bubble">{{ letter }}</div>
          <div class="txt">{{ q['option_' + letter.toLowerCase()] }}</div>
        </div>

        <!-- After-answer section -->
        <div v-if="answered">
          <div class="explain" :class="lastResult.is_correct ? 'r' : 'w'" style="margin-top:14px">
            <b>{{ lastResult.is_correct ? '✓ 回答正确' : '✕ 回答错误' }}</b> · 正确答案 {{ lastResult.correct_answer }}
            <div v-if="q.explanation" style="margin-top:6px;font-size:13px">{{ q.explanation }}</div>
          </div>
          <div style="display:flex;align-items:center;justify-content:space-between;margin-top:12px">
            <div style="flex:1;margin-right:12px">
              <div style="font-size:11px;color:var(--muted);margin-bottom:4px">1.5s 后自动跳转</div>
              <div class="auto-next"><i ref="autoBarRef" style="width:0%"></i></div>
            </div>
            <button class="btn sm" @click="advance">{{ quiz.isLast() ? '查看成绩' : '下一题 →' }}</button>
          </div>
        </div>

        <!-- Skip / Quit -->
        <div v-else style="margin-top:20px;padding-top:16px;border-top:1px solid var(--line);
          display:flex;align-items:center;justify-content:space-between">
          <button class="btn ghost sm" @click="doSkip">{{ quiz.isLast() ? '直接交卷' : '跳过此题' }}</button>
          <button class="btn ghost sm"
            style="color:var(--wrong);border-color:var(--wrong)" @click="doQuit">放弃答题</button>
        </div>
      </div>

      <!-- OMR panel -->
      <div class="quiz-panel">
        <h4>答题卡</h4>
        <div class="omr-grid">
          <div v-for="(oq, idx) in quiz.questions" :key="oq.id"
            class="omr-cell" :class="omrClass(oq.id, idx)"
            @click="jumpTo(idx)">
            {{ String(idx + 1).padStart(2, '0') }}
          </div>
        </div>
        <div class="omr-legend">
          <span><span class="omr-dot" style="background:var(--correct-soft);border:1.5px solid var(--correct)"></span>答对</span>
          <span><span class="omr-dot" style="background:var(--wrong-soft);border:1.5px solid var(--wrong)"></span>答错</span>
          <span><span class="omr-dot" style="background:var(--paper);border:1.5px solid var(--muted)"></span>跳过</span>
          <span><span class="omr-dot" style="border:1.5px solid var(--line)"></span>未答</span>
        </div>
        <div style="margin-top:14px;padding-top:12px;border-top:1px solid var(--line)">
          <div style="font-size:12px;color:var(--muted);margin-bottom:4px">已完成</div>
          <div style="font-family:var(--mono);font-size:18px;font-weight:700">
            {{ doneCount }}<span style="font-size:12px;color:var(--muted);font-weight:400"> / {{ quiz.questions.length }}</span>
          </div>
        </div>
      </div>
    </div>
  </AppLayout>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppLayout from '@/components/AppLayout.vue'
import { api } from '@/composables/useApi'
import { useToast } from '@/composables/useToast'
import { useQuizStore } from '@/stores/quiz'
import { L } from '@/utils'

const route  = useRoute()
const router = useRouter()
const { show: toast } = useToast()
const quiz = useQuizStore()

const loading      = ref(true)
const answered     = ref(false)
const pickedLetter = ref(null)
const lastResult   = ref(null)
const qTimerSec    = ref(0)
const globalRem    = ref(0)
const autoBarRef   = ref(null)

let autoTimer         = null
let keyHandler        = null
let globalRemInterval = null

const q         = computed(() => quiz.currentQuestion())
const doneCount = computed(() => Object.keys(quiz.answers).length)
const modeLabel = computed(() => ({
  random: '随机练习', sequential: '顺序练习', wrong_only: '错题模式', simulation: '模拟考试',
}[quiz.session?.mode] || ''))

function pad(n) { return String(n).padStart(2, '0') }
function formatTime(sec) {
  return `${String(Math.floor(sec / 60)).padStart(2, '0')}:${String(sec % 60).padStart(2, '0')}`
}

function omrClass(qid, idx) {
  const a = quiz.answers[qid]
  if (idx === quiz.index) return 'cur'
  if (!a) return ''
  if (a.skipped) return 'skp'
  return a.is_correct ? 'hit' : 'mis'
}

function optClass(letter) {
  if (!answered.value) return pickedLetter.value === letter ? 'pick' : ''
  const cls = ['locked']
  if (letter === lastResult.value?.correct_answer) cls.push('correct')
  else if (letter === pickedLetter.value) cls.push('bad')
  return cls.join(' ')
}

function jumpTo(idx) {
  if (answered.value) return
  clearAutoTimer()
  quiz.clearQTimer()
  quiz.index = idx
  quiz.locked = false
  resetQuestion()
}

function resetQuestion() {
  answered.value     = false
  pickedLetter.value = null
  lastResult.value   = null
  qTimerSec.value    = 0
  quiz.startQTimer((sec) => { qTimerSec.value = sec })
  setupKeyHandler()
}

function clearAutoTimer() {
  if (autoTimer) { clearTimeout(autoTimer); autoTimer = null }
}

function removeKeyHandler() {
  if (keyHandler) { document.removeEventListener('keydown', keyHandler); keyHandler = null }
}

function setupKeyHandler() {
  removeKeyHandler()
  keyHandler = (e) => {
    if (answered.value) {
      if (e.key === ' ' || e.key === 'Enter') { e.preventDefault(); advance() }
      return
    }
    const k = e.key.toUpperCase()
    if (['A', 'B', 'C', 'D'].includes(k)) pickAnswer(k)
  }
  document.addEventListener('keydown', keyHandler)
}

async function pickAnswer(letter) {
  if (quiz.locked || answered.value) return
  pickedLetter.value = letter
  quiz.locked = true
  quiz.clearQTimer()
  const timeSpent = Math.round((Date.now() - quiz.qStart) / 1000)

  let res
  try {
    res = await api(`/quiz/sessions/${quiz.session.id}/answer`, {
      body: { question_id: q.value.id, user_answer: letter, time_spent_seconds: timeSpent },
    })
  } catch(e) {
    toast(e.message, true)
    quiz.locked = false
    quiz.startQTimer((sec) => { qTimerSec.value = sec })
    return
  }

  if (res.is_correct) quiz.correct++
  quiz.answers = {
    ...quiz.answers,
    [q.value.id]: {
      answer: letter, correct_answer: res.correct_answer,
      is_correct: res.is_correct, time_spent: timeSpent,
      content: q.value.content, skipped: false,
    },
  }
  lastResult.value = res
  answered.value   = true

  nextTick(() => {
    if (autoBarRef.value) {
      autoBarRef.value.style.transition = 'width 1.5s linear'
      requestAnimationFrame(() => { if (autoBarRef.value) autoBarRef.value.style.width = '100%' })
    }
  })

  autoTimer = setTimeout(() => advance(), 1500)
}

function advance() {
  clearAutoTimer()
  removeKeyHandler()
  quiz.index++
  quiz.locked = false
  if (quiz.isFinished()) {
    router.push({ name: 'Summary' })
  } else {
    resetQuestion()
  }
}

function doSkip() {
  clearAutoTimer()
  quiz.clearQTimer()
  removeKeyHandler()
  if (quiz.isLast()) {
    quiz.index = quiz.questions.length
    router.push({ name: 'Summary' })
  } else {
    if (!quiz.answers[q.value.id]) {
      quiz.answers = { ...quiz.answers, [q.value.id]: { skipped: true, answer: null, is_correct: null } }
    }
    quiz.index++
    quiz.locked = false
    resetQuestion()
  }
}

function doQuit() {
  if (!confirm('确定放弃本次答题？')) return
  clearAutoTimer()
  removeKeyHandler()
  if (globalRemInterval) { clearInterval(globalRemInterval); globalRemInterval = null }
  quiz.reset()
  router.push({ name: 'Banks' })
}

function startGlobalTimer() {
  if (!quiz.deadline) return
  globalRem.value = Math.max(0, Math.round((quiz.deadline - Date.now()) / 1000))
  quiz.startTimer(() => {
    toast('时间到，自动交卷')
    clearAutoTimer()
    removeKeyHandler()
    quiz.index = quiz.questions.length
    router.push({ name: 'Summary' })
  })
  globalRemInterval = setInterval(() => {
    globalRem.value = Math.max(0, Math.round((quiz.deadline - Date.now()) / 1000))
  }, 1000)
}

onMounted(async () => {
  // Resume existing in-progress session
  if (quiz.session && quiz.questions.length && !quiz.isFinished()) {
    loading.value = false
    resetQuestion()
    startGlobalTimer()
    return
  }

  const { bankId, title, mode, count, limit } = route.query
  if (!bankId) { router.push({ name: 'Banks' }); return }

  quiz.reset()
  try {
    const sess = await api('/quiz/sessions', {
      body: {
        bank_id:            bankId,
        mode:               mode || 'random',
        total_questions:    count ? Number(count) : null,
        time_limit_seconds: limit ? Number(limit) : null,
      },
    })
    quiz.session   = sess
    quiz.title     = title || ''
    if (limit) quiz.deadline = Date.now() + Number(limit) * 1000

    const qs = await api(`/quiz/sessions/${sess.id}/questions`)
    quiz.questions = qs
    quiz.index     = 0

    loading.value = false
    resetQuestion()
    startGlobalTimer()
  } catch(e) {
    const msg = e.message.includes('没有可用题目') && mode === 'wrong_only'
      ? '您在该题库还没有错题，先去练习积累一下吧'
      : e.message
    toast(msg, true)
    router.push({ name: 'Banks' })
  }
})

onUnmounted(() => {
  removeKeyHandler()
  clearAutoTimer()
  if (globalRemInterval) { clearInterval(globalRemInterval); globalRemInterval = null }
})
</script>
