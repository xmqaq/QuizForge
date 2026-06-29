<template>
  <AppLayout :title="bankId" subtitle="BANK">
    <div class="empty"><div class="big">▦</div>题库详情（阶段二实现）</div>
  </AppLayout>
</template>
<script setup>
import { useRoute } from 'vue-router'
import AppLayout from '@/components/AppLayout.vue'
const bankId = useRoute().params.id
</script>
