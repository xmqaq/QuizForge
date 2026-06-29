import { inject, provide, ref } from 'vue'

const TOAST_KEY = Symbol('toast')

export function provideToast() {
  const msg = ref('')
  const err = ref(false)
  let timer = null

  const show = (message, isError = false) => {
    msg.value = message
    err.value = isError
    clearTimeout(timer)
    timer = setTimeout(() => { msg.value = '' }, 2600)
  }

  provide(TOAST_KEY, { msg, err, show })
  return { msg, err, show }
}

export function useToast() {
  const toast = inject(TOAST_KEY)
  if (!toast) throw new Error('useToast: 请在 App.vue 中调用 provideToast()')
  return toast
}
