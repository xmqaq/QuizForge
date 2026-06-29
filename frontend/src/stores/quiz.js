import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useQuizStore = defineStore('quiz', () => {
  const session   = ref(null)
  const title     = ref('')
  const questions = ref([])
  const index     = ref(0)
  const locked    = ref(false)
  const correct   = ref(0)
  const deadline  = ref(null)
  const answers   = ref({})
  const qStart    = ref(0)

  let _timer = null
  let _qtimer = null

  function startTimer(onExpire) {
    clearTimer()
    const tick = () => {
      const rem = Math.max(0, Math.round((deadline.value - Date.now()) / 1000))
      if (rem <= 0) { clearTimer(); onExpire() }
    }
    tick()
    _timer = setInterval(tick, 1000)
  }

  function clearTimer() {
    if (_timer) { clearInterval(_timer); _timer = null }
  }

  function startQTimer(onTick) {
    clearQTimer()
    qStart.value = Date.now()
    _qtimer = setInterval(() => {
      onTick(Math.round((Date.now() - qStart.value) / 1000))
    }, 1000)
  }

  function clearQTimer() {
    if (_qtimer) { clearInterval(_qtimer); _qtimer = null }
  }

  function reset() {
    clearTimer()
    clearQTimer()
    session.value   = null
    title.value     = ''
    questions.value = []
    index.value     = 0
    locked.value    = false
    correct.value   = 0
    deadline.value  = null
    answers.value   = {}
    qStart.value    = 0
  }

  const currentQuestion = () => questions.value[index.value] || null
  const isLast = () => index.value >= questions.value.length - 1
  const isFinished = () => index.value >= questions.value.length

  return {
    session, title, questions, index, locked, correct,
    deadline, answers, qStart,
    startTimer, clearTimer, startQTimer, clearQTimer, reset,
    currentQuestion, isLast, isFinished,
  }
})
