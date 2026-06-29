<template>
  <div>
    <div v-if="items.length"
      style="display:flex;align-items:center;gap:10px;margin-bottom:12px;padding:8px 12px;
        background:var(--paper);border-radius:9px;border:1px solid var(--line)">
      <input type="checkbox" class="q-checkbox"
        :checked="allSelected"
        :indeterminate.prop="someSelected && !allSelected"
        @change="toggleSelectAll">
      <label style="font-size:13px;color:var(--muted);cursor:pointer;flex:1"
        @click="toggleSelectAll">
        全选本页（共 {{ items.length }} 题）
      </label>
      <span v-if="selected.size" style="font-size:12px;color:var(--muted)">
        已选 {{ selected.size }} 题
      </span>
    </div>

    <div v-if="!items.length" class="empty">
      <div class="big">✎</div>这个题库还没有题目，用 AI 生成一批
    </div>

    <div v-for="(q, i) in items" :key="q.id"
      class="card" style="margin-bottom:10px;display:flex;gap:12px;align-items:flex-start">
      <input type="checkbox" class="q-checkbox q-sel" style="margin-top:3px"
        :checked="selected.has(q.id)"
        @change="toggleSelect(q.id, $event.target.checked)">

      <div style="flex:1;min-width:0">
        <div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap;margin-bottom:8px">
          <span class="pill">{{ String(i+1).padStart(2,'0') }}</span>
          <span class="pill" :class="statusClass(q.status)">{{ L('qstatus', q.status) }}</span>
          <span class="pill">{{ L('difficulty', q.difficulty) }}</span>
          <span style="margin-left:auto;display:flex;gap:6px">
            <button class="btn ghost sm" style="font-size:12px" @click="toggleExpand(q.id)">
              {{ expanded.has(q.id) ? '收起' : '展开' }}
            </button>
            <template v-if="q.status === 'pending_review'">
              <button class="btn sm"
                style="background:var(--correct);border:none;font-size:12px"
                @click="$emit('approve', q.id)">通过</button>
              <button class="btn sm"
                style="background:var(--wrong);border:none;font-size:12px"
                @click="$emit('reject', q.id)">拒绝</button>
            </template>
          </span>
        </div>

        <div style="font-weight:500">{{ q.content }}</div>

        <div v-if="expanded.has(q.id)" style="margin-top:10px">
          <div v-for="letter in ['A','B','C','D']" :key="letter"
            :style="{
              padding:'7px 10px', marginBottom:'5px', borderRadius:'8px', fontSize:'13px',
              background: q.correct_answer === letter ? 'var(--correct-soft)' : 'var(--paper)',
              border: `1px solid ${q.correct_answer === letter ? 'var(--correct)' : 'var(--line)'}`,
            }">
            <b>{{ letter }}.</b> {{ q['option_' + letter.toLowerCase()] }}
            <span v-if="q.correct_answer === letter"
              style="color:var(--correct);margin-left:6px;font-size:12px">✓ 正确答案</span>
          </div>

          <div v-if="q.explanation" class="explain" style="margin-top:8px;font-size:13px">
            {{ q.explanation }}
          </div>

          <!-- 编辑表单 -->
          <div v-if="editingId === q.id"
            style="margin-top:12px;padding-top:10px;border-top:1px solid var(--line)">
            <div class="fld">
              <label class="f">题干</label>
              <textarea class="in" v-model="editForm.content" rows="3" style="resize:vertical"></textarea>
            </div>
            <div class="row">
              <div v-for="l in ['A','B','C','D']" :key="l">
                <label class="f">选项 {{ l }}</label>
                <input class="in" v-model="editForm['option_' + l.toLowerCase()]">
              </div>
            </div>
            <div class="row" style="margin-top:8px">
              <div>
                <label class="f">正确答案</label>
                <select class="in" v-model="editForm.correct_answer">
                  <option v-for="l in ['A','B','C','D']" :key="l" :value="l">{{ l }}</option>
                </select>
              </div>
              <div>
                <label class="f">难度</label>
                <select class="in" v-model="editForm.difficulty">
                  <option value="easy">基础</option>
                  <option value="medium">进阶</option>
                  <option value="hard">综合</option>
                </select>
              </div>
            </div>
            <div class="fld" style="margin-top:8px">
              <label class="f">解析（可选）</label>
              <textarea class="in" v-model="editForm.explanation" rows="2" style="resize:vertical"></textarea>
            </div>
            <div style="display:flex;gap:8px;margin-top:8px">
              <button class="btn sm" :disabled="saving" @click="saveEdit(q.id)">
                {{ saving ? '保存中…' : '保存' }}
              </button>
              <button class="btn ghost sm" @click="editingId = null">取消</button>
            </div>
          </div>

          <div v-else
            style="display:flex;gap:8px;margin-top:12px;padding-top:10px;border-top:1px solid var(--line)">
            <button class="btn ghost sm" style="font-size:12px" @click="startEdit(q)">✎ 编辑</button>
            <button class="btn sm"
              style="background:var(--wrong);border:none;font-size:12px;margin-left:auto"
              @click="$emit('delete', q.id, q.content.substring(0,20))">删除此题</button>
          </div>
        </div>
      </div>
    </div>

    <div class="bulk-bar" :class="{ show: selected.size > 0 }">
      <div class="cnt">已选 <span style="color:#A5B4FC">{{ selected.size }}</span> 题</div>
      <button class="bulk-btn" @click="$emit('bulk', 'approve', selected)">✓ 批量通过</button>
      <button class="bulk-btn" @click="$emit('bulk', 'reject',  selected)">✕ 批量拒绝</button>
      <button class="bulk-btn danger" @click="$emit('bulk', 'delete',  selected)">🗑 批量删除</button>
      <button class="bulk-btn" style="background:none;border:none;opacity:.6" @click="clearSelection">取消选择</button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { api } from '@/composables/useApi'
import { useToast } from '@/composables/useToast'
import { L } from '@/utils'

const props = defineProps({
  items: { type: Array, default: () => [] },
})
const emit = defineEmits(['approve', 'reject', 'delete', 'bulk', 'updated'])

const { show: toast } = useToast()

const expanded  = ref(new Set())
const selected  = ref(new Set())
const editingId = ref(null)
const saving    = ref(false)
const editForm  = ref({})

const allSelected  = computed(() => props.items.length > 0 && props.items.every(q => selected.value.has(q.id)))
const someSelected = computed(() => selected.value.size > 0)

function toggleExpand(id) {
  const s = new Set(expanded.value)
  s.has(id) ? s.delete(id) : s.add(id)
  expanded.value = s
}

function toggleSelect(id, checked) {
  const s = new Set(selected.value)
  checked ? s.add(id) : s.delete(id)
  selected.value = s
}

function toggleSelectAll() {
  if (allSelected.value) {
    selected.value = new Set()
  } else {
    selected.value = new Set(props.items.map(q => q.id))
  }
}

function clearSelection() {
  selected.value = new Set()
}

function statusClass(status) {
  if (status === 'approved') return 'ok'
  if (status === 'pending_review') return 'warn'
  return ''
}

function startEdit(q) {
  editingId.value = q.id
  editForm.value = {
    content:        q.content,
    option_a:       q.option_a,
    option_b:       q.option_b,
    option_c:       q.option_c,
    option_d:       q.option_d,
    correct_answer: q.correct_answer,
    difficulty:     q.difficulty,
    explanation:    q.explanation || '',
  }
}

async function saveEdit(id) {
  if (!editForm.value.content?.trim()) return toast('题干不能为空', true)
  saving.value = true
  try {
    await api('/questions/' + id, { method: 'PUT', body: {
      ...editForm.value,
      explanation: editForm.value.explanation?.trim() || null,
    }})
    toast('题目已保存')
    editingId.value = null
    emit('updated')
  } catch(e) {
    toast(e.message, true)
  } finally {
    saving.value = false
  }
}

watch(() => props.items, () => {
  expanded.value  = new Set()
  selected.value  = new Set()
  editingId.value = null
})
</script>
