<template>
  <div class="card bank" @click="$emit('click', bank)">
    <div style="display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:8px">
      <div style="display:flex;gap:6px;flex-wrap:wrap">
        <span v-if="bank.industry" class="pill"
          style="background:var(--accent-soft);color:var(--accent);border-color:transparent">
          {{ L('industry', bank.industry) }}
        </span>
        <span class="pill" :class="{ ok: bank.status === 'published' }">
          {{ L('status', bank.status) }}
        </span>
      </div>
      <button v-if="showDelete" class="btn ghost sm del-bank"
        style="flex:none;color:var(--wrong);border-color:var(--wrong);padding:3px 8px;font-size:11px"
        @click.stop="$emit('delete', bank)">
        删除
      </button>
    </div>

    <h3 style="margin:0 0 4px;font-size:15px;font-weight:600">{{ bank.title }}</h3>
    <div class="desc">
      <span v-if="bank.description">{{ bank.description }}</span>
      <span v-else style="opacity:.4">暂无描述</span>
    </div>

    <div style="display:flex;align-items:baseline;gap:4px;margin-top:auto;
      padding-top:12px;border-top:1px solid var(--line)">
      <span class="bank-count-big">{{ bank.question_count }}</span>
      <small style="font-size:12px;color:var(--muted)">道题</small>
    </div>
  </div>
</template>

<script setup>
import { L } from '@/utils'

defineProps({
  bank:       { type: Object,  required: true },
  showDelete: { type: Boolean, default: true  },
})
defineEmits(['click', 'delete'])
</script>
