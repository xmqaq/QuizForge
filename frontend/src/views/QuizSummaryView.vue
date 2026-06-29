<template>
  <AppLayout title="成绩单" subtitle="本次成绩">
    <div v-if="loading" style="text-align:center;padding:40px;color:var(--muted)">计算成绩中…</div>

    <div v-else style="max-width:700px">
      <!-- Accuracy -->
      <div style="text-align:center;padding:28px 20px 16px">
        <div style="font-size:12px;color:var(--muted);letter-spacing:1px;margin-bottom:6px">正确率</div>
        <div style="font-family:var(--mono);font-size:72px;font-weight:800;letter-spacing:-3px;line-height:1"
          :style="{ color: acc >= 60 ? 'var(--correct)' : 'var(--wrong)' }">
          {{ acc }}<span style="font-size:28px">%</span>
        </div>
        <div style="font-size:14px;color:var(--muted);margin-top:8px">{{ savedTitle }}</div>
      </div>

      <!-- Stats grid -->
      <div class="result-grid">
        <div class="result-cell">
          <div class="rv" style="color:var(--correct)">{{ fin.correct_count }}</div>
          <div class="rk">答对</div>
        </div>
        <div class="result-cell">
          <div class="rv" style="color:var(--wrong)">{{ wrongCount }}</div>
          <div class="rk">答错</div>
        </div>
        <div class="result-cell">
          <div class="rv" style="color:var(--muted)">{{ skipped }}</div>
          <div class="rk">跳过</div>
        </div>
        <div class="result-cell">
          <div class="rv">{{ fin.answered_count }} / {{ fin.total_questions }}</div>
          <div class="rk">作答 / 总题</div>
        </div>
        <div class="result-cell">
          <div class="rv">{{ avgTime > 0 ? avgTime + 's' : '—' }}</div>
          <div class="rk">平均用时/题</div>
        </div>
        <div class="result-cell">
          <div class="rv" :style="{ color: gradeColor }">{{ grade }}</div>
          <div class="rk">评级</div>
        </div>
      </div>

      <!-- Action buttons -->
      <div style="display:flex;gap:10px;flex-wrap:wrap;margin-bottom:24px">
        <button class="btn" @click="router.push({ name: 'Banks' })">返回题库</button>
        <button v-if="hasWrong" class="btn ghost" @click="retryWrong">复习本次错题</button>
        <button class="btn ghost" @click="retryAgain">再来一次</button>
        <button class="btn ghost" @click="router.push({ name: 'Wrong' })">错题本</button>
      </div>

      <!-- Review rows -->
      <div style="font-weight:600;font-size:15px;margin-bottom:12px">答题明细</div>
      <div class="card" style="padding:4px 16px">
        <div v-for="(q, idx) in savedQuestions" :key="q.id" class="review-item">
          <template v-if="!savedAnswers[q.id] || savedAnswers[q.id].skipped">
            <div class="review-badge sk">—</div>
            <div style="flex:1">
              <div style="font-size:13px;color:var(--muted)">
                {{ String(idx + 1).padStart(2, '0') }}. {{ q.content.substring(0, 50) }}{{ q.content.length > 50 ? '…' : '' }}
              </div>
              <div style="font-size:12px;color:var(--muted);margin-top:2px">已跳过</div>
            </div>
          </template>
          <template v-else>
            <div class="review-badge" :class="savedAnswers[q.id].is_correct ? 'ok' : 'no'">
              {{ savedAnswers[q.id].is_correct ? '✓' : '✕' }}
            </div>
            <div style="flex:1">
              <div style="font-size:13px">
                {{ String(idx + 1).padStart(2, '0') }}. {{ q.content.substring(0, 50) }}{{ q.content.length > 50 ? '…' : '' }}
              </div>
              <div style="font-size:12px;color:var(--muted);margin-top:3px">
                我选：<b :style="{ color: savedAnswers[q.id].is_correct ? 'var(--correct)' : 'var(--wrong)' }">
                  {{ savedAnswers[q.id].answer }}
                </b>
                <template v-if="!savedAnswers[q.id].is_correct">
                  · 正确：<b style="color:var(--correct)">{{ savedAnswers[q.id].correct_answer }}</b>
                </template>
                · 用时 {{ savedAnswers[q.id].time_spent }}s
              </div>
            </div>
          </template>
        </div>
      </div>
    </div>
  </AppLayout>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import AppLayout from '@/components/AppLayout.vue'
import { api } from '@/composables/useApi'
import { useToast } from '@/composables/useToast'
import { useQuizStore } from '@/stores/quiz'

const router = useRouter()
const { show: toast } = useToast()
const quiz = useQuizStore()

const loading = ref(true)
const fin     = ref({ correct_count: 0, answered_count: 0, total_questions: 0 })

// Snapshot state before reset
const savedTitle     = quiz.title
const savedBankId    = quiz.session?.bank_id
const savedMode      = quiz.session?.mode
const savedQuestions = [...(quiz.questions || [])]
const savedAnswers   = { ...quiz.answers }

const acc        = computed(() => fin.value.answered_count === 0 ? 0 : Math.round((fin.value.correct_count / (fin.value.total_questions || 1)) * 100))
const wrongCount = computed(() => (fin.value.answered_count || 0) - (fin.value.correct_count || 0))
const skipped    = computed(() => (fin.value.total_questions || 0) - (fin.value.answered_count || 0))
const hasWrong   = computed(() => Object.values(savedAnswers).some(a => a.is_correct === false))

const avgTime = computed(() => {
  const timings = Object.values(savedAnswers).filter(a => !a.skipped && a.time_spent)
  if (!timings.length) return 0
  return Math.round(timings.reduce((s, a) => s + a.time_spent, 0) / timings.length)
})

const grade = computed(() => {
  const a = acc.value
  return a >= 90 ? '优秀' : a >= 75 ? '良好' : a >= 60 ? '及格' : '待加强'
})

const gradeColor = computed(() => {
  const a = acc.value
  return a >= 90 ? 'var(--correct)' : a >= 60 ? 'var(--ink)' : 'var(--wrong)'
})

function retryAgain() {
  if (!savedBankId) { router.push({ name: 'Banks' }); return }
  router.push({ name: 'Quiz', query: { bankId: savedBankId, title: savedTitle, mode: savedMode } })
}

function retryWrong() {
  if (!savedBankId) { router.push({ name: 'Banks' }); return }
  router.push({ name: 'Quiz', query: { bankId: savedBankId, title: savedTitle, mode: 'wrong_only' } })
}

onMounted(async () => {
  if (!quiz.session?.id) { router.push({ name: 'Banks' }); return }
  try {
    fin.value = await api(`/quiz/sessions/${quiz.session.id}/finish`, { method: 'POST' })
  } catch(e) {
    toast(e.message, true)
  } finally {
    loading.value = false
    quiz.reset()
  }
})
</script>
