<template>
  <AppLayout title="学习统计" subtitle="OVERVIEW">

    <div v-if="loading" style="text-align:center;padding:40px;color:var(--muted)">加载中…</div>

    <template v-else>
      <!-- 概览 5 格 -->
      <div class="grid cols" style="margin-bottom:24px">
        <div class="card stat">
          <div class="v">{{ overview.sessions }}</div>
          <div class="k">答题会话</div>
        </div>
        <div class="card stat">
          <div class="v">{{ overview.total_answers }}</div>
          <div class="k">累计作答</div>
        </div>
        <div class="card stat">
          <div class="v" :style="{ color: accPct >= 60 ? 'var(--correct)' : 'var(--ink)' }">
            {{ accPct }}%
          </div>
          <div class="k">总正确率</div>
          <div class="bar"><i :style="{ width: accPct + '%' }"></i></div>
        </div>
        <div class="card stat">
          <div class="v" style="color:var(--wrong)">{{ overview.wrong_unmastered }}</div>
          <div class="k">待复习错题</div>
        </div>
        <div class="card stat">
          <div class="v">{{ overview.banks_created }}</div>
          <div class="k">我创建的题库</div>
        </div>
      </div>

      <!-- 各题库表现 -->
      <div style="font-weight:700;margin-bottom:12px;font-size:15px">各题库表现</div>
      <div v-if="!bankDetails.length" class="empty" style="padding:30px 20px">暂无答题记录</div>
      <div v-else>
        <div v-for="d in bankDetails" :key="d.bank_id"
          class="card" style="margin-bottom:8px;padding:14px 16px">
          <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px">
            <span style="font-weight:500;font-size:14px">{{ d.title }}</span>
            <span class="pill" :class="Math.round(d.my_accuracy * 100) >= 60 ? 'ok' : 'warn'">
              {{ Math.round(d.my_accuracy * 100) }}% 正确率
            </span>
          </div>
          <div style="font-size:12px;color:var(--muted)">
            已作答 {{ d.my_answered }} 题 · 答对 {{ d.my_correct }} 题 · 题库共 {{ d.question_count }} 题
          </div>
          <div class="bar" style="margin-top:8px">
            <i :style="{
              width: Math.round(d.my_accuracy * 100) + '%',
              background: Math.round(d.my_accuracy * 100) >= 60 ? 'var(--correct)' : 'var(--wrong)',
            }"></i>
          </div>
        </div>
      </div>

      <!-- 近期答题记录 -->
      <div style="font-weight:600;font-size:15px;margin:24px 0 12px">近期答题记录</div>
      <div v-if="sessions.length" class="card" style="padding:0;overflow:hidden">
        <table class="admin-table">
          <thead>
            <tr>
              <th>题库</th>
              <th>模式</th>
              <th>得分</th>
              <th>时间</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="s in sessions" :key="s.id">
              <td>{{ bankMap[s.bank_id] || '未知题库' }}</td>
              <td><span class="pill">{{ L('mode', s.mode) }}</span></td>
              <td>
                <span style="font-family:var(--mono);font-weight:700"
                  :style="{ color: pct(s) >= 60 ? 'var(--correct)' : 'var(--wrong)' }">
                  {{ pct(s) }}%
                </span>
                <span style="font-size:12px;color:var(--muted)">
                  {{ s.correct_count }}/{{ s.total_questions }}
                </span>
              </td>
              <td style="color:var(--muted)">
                {{ new Date(s.started_at).toLocaleDateString('zh-CN') }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <div v-else class="empty" style="padding:20px">暂无答题记录</div>
    </template>
  </AppLayout>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import AppLayout from '@/components/AppLayout.vue'
import { api } from '@/composables/useApi'
import { useToast } from '@/composables/useToast'
import { L } from '@/utils'

const { show: toast } = useToast()

const loading     = ref(true)
const overview    = ref({})
const bankDetails = ref([])
const sessions    = ref([])
const bankMap     = ref({})

const accPct = computed(() => Math.round((overview.value.accuracy || 0) * 100))
const pct    = (s) => s.total_questions
  ? Math.round(s.correct_count / s.total_questions * 100) : 0

onMounted(async () => {
  try {
    const [ovr, { items: myBanks }, { items: sess }] = await Promise.all([
      api('/stats/overview'),
      api('/banks?size=50'),
      api('/quiz/sessions?size=10').catch(() => ({ items: [] })),
    ])
    overview.value = ovr
    sessions.value = sess
    bankMap.value  = Object.fromEntries(myBanks.map(b => [b.id, b.title]))

    const details = await Promise.all(
      myBanks.map(b => api('/stats/bank/' + b.id).catch(() => null))
    )
    bankDetails.value = details.filter(d => d && d.my_answered > 0)
  } catch(e) {
    toast(e.message, true)
  } finally {
    loading.value = false
  }
})
</script>
