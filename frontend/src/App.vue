<template>
  <RouterView />
  <div :class="['toast', toastMsg ? 'show' : '', toastErr ? 'err' : '']">
    {{ toastMsg }}
  </div>
</template>

<script setup>
import { RouterView } from 'vue-router'
import { provideToast } from '@/composables/useToast'

const { msg: toastMsg, err: toastErr } = provideToast()
</script>
