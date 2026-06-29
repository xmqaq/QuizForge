<template>
  <AppLayout title="系统设置" subtitle="ADMIN">
    <div class="settings-layout">
      <!-- 左侧导航 -->
      <div class="settings-nav">
        <button v-for="tab in TABS" :key="tab.v"
          class="settings-nav-item" :class="{ on: activeTab === tab.v }"
          @click="activeTab = tab.v">
          <span class="sic">{{ tab.ic }}</span>{{ tab.l }}
        </button>
      </div>

      <!-- 右侧内容 -->
      <div class="settings-content">

        <!-- AI 模型管理 -->
        <template v-if="activeTab === 'providers'">
          <div v-if="providersLoading" style="text-align:center;padding:40px;color:var(--muted)">加载中…</div>
          <template v-else>
            <div v-for="p in providers" :key="p.id"
              class="provider-card"
              :class="{ 'active-provider': p.id === activeId, 'has-key': p.has_key && p.id !== activeId }">
              <div class="provider-header">
                <div class="provider-logo">{{ ICONS[p.id] || '🤖' }}</div>
                <div class="provider-info">
                  <div class="provider-name">{{ p.name }}</div>
                  <div class="provider-status">
                    <span v-if="p.has_key" class="tag-verified">✓ 已配置</span>
                    <span v-else class="tag-unset">未配置</span>
                    <span v-if="p.id === activeId" class="tag-verified"
                      style="background:var(--accent-soft);color:var(--accent);border-color:var(--accent);margin-left:4px">
                      ● 使用中
                    </span>
                  </div>
                </div>
                <div class="provider-actions">
                  <button v-if="p.has_key && p.id !== activeId"
                    class="btn ghost sm" style="font-size:12px"
                    @click="setActive(p.id)">设为默认</button>
                  <button class="btn ghost sm" style="font-size:12px"
                    @click="toggleExpand(p.id)">
                    {{ expandedProviders.has(p.id) ? '收起 ▴' : '配置 ▾' }}
                  </button>
                </div>
              </div>

              <!-- 展开配置区 -->
              <div class="provider-body" :class="{ open: expandedProviders.has(p.id) }">
                <div v-if="p.id === 'custom' || p.id.startsWith('custom_')">
                  <label class="f">Base URL</label>
                  <input class="in" :id="'purl_' + p.id" :placeholder="'https://api.example.com/v1'"
                    :value="p.base_url || ''">
                </div>
                <div>
                  <label class="f">API Key</label>
                  <div style="display:flex;gap:6px">
                    <input class="in" type="password" :id="'pkey_' + p.id" style="flex:1"
                      :placeholder="p.has_key ? '留空=不修改' : '输入 API Key'">
                    <button class="btn ghost sm" style="flex:none;white-space:nowrap"
                      @click="toggleKeyVis(p.id)">
                      {{ keyVisible.has(p.id) ? '隐藏' : '显示' }}
                    </button>
                  </div>
                  <div v-if="p.has_key" style="font-size:12px;color:var(--muted);margin-top:4px">
                    当前：{{ p.api_key_masked }}
                  </div>
                </div>
                <div style="display:flex;gap:8px;align-items:flex-end">
                  <div style="flex:1">
                    <label class="f">使用模型</label>
                    <input class="in" :id="'pmodel_' + p.id" :value="p.model || ''"
                      :placeholder="p.default_model || ''">
                  </div>
                  <button class="btn ghost sm" style="flex:none;white-space:nowrap;align-self:flex-end"
                    @click="fetchModels(p.id)">
                    {{ fetchingModels.has(p.id) ? '拉取中…' : '拉取模型列表' }}
                  </button>
                </div>
                <div v-if="modelLists[p.id]?.length">
                  <label class="f">从列表选择</label>
                  <select class="in" @change="e => fillModel(p.id, e.target.value)">
                    <option value="">— 选择模型 —</option>
                    <option v-for="m in modelLists[p.id]" :key="m" :value="m">{{ m }}</option>
                  </select>
                </div>
                <div style="display:flex;gap:8px;margin-top:4px">
                  <button class="btn sm" @click="saveProvider(p.id)">
                    {{ savingProviders.has(p.id) ? '保存中…' : '保存' }}
                  </button>
                  <button class="btn ghost sm" @click="verifyProvider(p.id)">
                    {{ verifyingProviders.has(p.id) ? '验证中…' : '验证 Key' }}
                  </button>
                  <button v-if="p.id.startsWith('custom_')" class="btn ghost sm"
                    style="color:var(--wrong);border-color:var(--wrong);margin-left:auto"
                    @click="deleteProvider(p.id)">删除</button>
                </div>
                <div v-if="verifyResults[p.id]" style="font-size:12px;margin-top:4px"
                  :style="{ color: verifyResults[p.id].valid ? 'var(--correct)' : 'var(--wrong)' }">
                  {{ verifyResults[p.id].valid ? '✓ ' : '✕ ' }}{{ verifyResults[p.id].detail }}
                </div>
              </div>
            </div>

            <!-- 添加自定义 -->
            <button class="btn ghost" style="width:100%;margin-top:8px"
              @click="showCustomForm = !showCustomForm">
              ＋ 添加自定义模型商（OpenAI 兼容）
            </button>
            <div v-if="showCustomForm" class="section-card" style="margin-top:10px">
              <h3>新增自定义模型商</h3>
              <div class="row">
                <div><label class="f">名称</label>
                  <input class="in" v-model="customForm.name" placeholder="我的 API"></div>
                <div><label class="f">Base URL</label>
                  <input class="in" v-model="customForm.base_url" placeholder="https://api.example.com/v1"></div>
              </div>
              <div class="row" style="margin-top:10px">
                <div><label class="f">API Key</label>
                  <input class="in" type="password" v-model="customForm.api_key"></div>
                <div><label class="f">默认模型</label>
                  <input class="in" v-model="customForm.model" placeholder="gpt-4o"></div>
              </div>
              <div style="display:flex;gap:8px;margin-top:12px">
                <button class="btn sm" @click="addCustomProvider">添加</button>
                <button class="btn ghost sm" @click="showCustomForm = false">取消</button>
              </div>
            </div>
          </template>
        </template>

        <!-- 用户管理 -->
        <template v-else-if="activeTab === 'users'">
          <div v-if="usersLoading" style="text-align:center;padding:40px;color:var(--muted)">加载中…</div>
          <div v-else class="section-card" style="padding:0;overflow:hidden">
            <table class="admin-table">
              <thead>
                <tr><th>用户</th><th>角色</th><th>状态</th><th>注册时间</th><th>操作</th></tr>
              </thead>
              <tbody>
                <tr v-for="u in users" :key="u.id">
                  <td>
                    <div style="display:flex;align-items:center;gap:10px">
                      <div style="width:30px;height:30px;border-radius:50%;
                        background:var(--accent-soft);display:grid;place-items:center;
                        font-size:12px;font-weight:700;color:var(--accent);flex:none">
                        {{ (u.username || '?')[0].toUpperCase() }}
                      </div>
                      <div>
                        <div style="font-weight:500">{{ u.username }}</div>
                        <div style="font-size:12px;color:var(--muted)">{{ u.email }}</div>
                      </div>
                    </div>
                  </td>
                  <td>
                    <select class="in" :value="u.role" style="padding:5px 8px;font-size:12px;width:90px"
                      :disabled="u.id === currentUserId"
                      @change="updateRole(u.id, $event.target.value)">
                      <option value="user">用户</option>
                      <option value="editor">编辑</option>
                      <option value="admin">管理员</option>
                    </select>
                  </td>
                  <td><span class="pill" :class="u.is_active ? 'ok' : 'warn'">
                    {{ u.is_active ? '正常' : '已停用' }}
                  </span></td>
                  <td style="color:var(--muted)">
                    {{ new Date(u.created_at).toLocaleDateString('zh-CN') }}
                  </td>
                  <td>
                    <button v-if="u.id !== currentUserId" class="btn ghost sm" style="font-size:12px"
                      @click="toggleUser(u)">{{ u.is_active ? '停用' : '启用' }}</button>
                    <span v-else style="font-size:12px;color:var(--muted)">当前账号</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </template>

        <!-- 站点设置 -->
        <template v-else-if="activeTab === 'site'">
          <div v-if="siteLoading" style="text-align:center;padding:40px;color:var(--muted)">加载中…</div>
          <div v-else class="section-card">
            <h3>站点设置</h3>
            <div class="fld">
              <label class="f">站点名称</label>
              <input class="in" v-model="siteCfg.site_name">
            </div>
            <div class="fld" style="display:flex;align-items:center;gap:10px">
              <input type="checkbox" id="allow_reg" v-model="siteCfg.allow_register"
                style="width:16px;height:16px">
              <label for="allow_reg" style="font-size:14px;cursor:pointer">允许新用户注册</label>
            </div>
            <button class="btn" :disabled="savingSite" @click="saveSite">
              {{ savingSite ? '保存中…' : '保存站点设置' }}
            </button>
          </div>
        </template>

      </div>
    </div>
  </AppLayout>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import AppLayout from '@/components/AppLayout.vue'
import { api } from '@/composables/useApi'
import { useToast } from '@/composables/useToast'
import { useAuthStore } from '@/stores/auth'

const { show: toast } = useToast()
const auth = useAuthStore()

const currentUserId = auth.user?.id

const TABS = [
  { v: 'providers', l: 'AI 模型管理', ic: '🤖' },
  { v: 'users',     l: '用户管理',   ic: '👥' },
  { v: 'site',      l: '站点设置',   ic: '🌐' },
]

const ICONS = {
  deepseek: '🔮', qwen: '☁️', minimax: '🌊', zhipu: '🧠',
  kimi: '🌙', baichuan: '🏔', lingyiwanwu: '✨', groq: '⚡', custom: '🔧',
}

const activeTab = ref('providers')

// ── Providers ──────────────────────────────
const providers          = ref([])
const activeId           = ref('')
const providersLoading   = ref(true)
const expandedProviders  = ref(new Set())
const keyVisible         = ref(new Set())
const fetchingModels     = ref(new Set())
const savingProviders    = ref(new Set())
const verifyingProviders = ref(new Set())
const modelLists         = ref({})
const verifyResults      = ref({})
const showCustomForm     = ref(false)
const customForm         = ref({ name: '', base_url: '', api_key: '', model: '' })

async function loadProviders() {
  providersLoading.value = true
  try {
    const [cfg, list] = await Promise.all([
      api('/admin/site-config'),
      api('/admin/providers'),
    ])
    activeId.value  = cfg.active_provider || 'deepseek'
    providers.value = list
  } finally {
    providersLoading.value = false
  }
}

function toggleExpand(id) {
  const s = new Set(expandedProviders.value)
  s.has(id) ? s.delete(id) : s.add(id)
  expandedProviders.value = s
}

function toggleKeyVis(id) {
  const el = document.getElementById('pkey_' + id)
  const s  = new Set(keyVisible.value)
  if (s.has(id)) {
    s.delete(id)
    if (el) el.type = 'password'
  } else {
    s.add(id)
    if (el) el.type = 'text'
  }
  keyVisible.value = s
}

function fillModel(pid, val) {
  const el = document.getElementById('pmodel_' + pid)
  if (el && val) el.value = val
}

function getFieldVal(pid, field) {
  return document.getElementById(field + '_' + pid)?.value?.trim() || ''
}

async function fetchModels(pid) {
  const s = new Set(fetchingModels.value); s.add(pid); fetchingModels.value = s
  try {
    const body = {}
    const key   = getFieldVal(pid, 'pkey')
    const url   = getFieldVal(pid, 'purl')
    const model = getFieldVal(pid, 'pmodel')
    if (key)   body.api_key  = key
    if (url)   body.base_url = url
    if (model) body.model    = model
    const { models } = await api(`/admin/providers/${pid}/fetch-models`, {
      method: 'POST', body: Object.keys(body).length ? body : undefined,
    })
    modelLists.value = { ...modelLists.value, [pid]: models }
    toast(`获取到 ${models.length} 个模型`)
  } catch(e) { toast(e.message, true) }
  finally { const s = new Set(fetchingModels.value); s.delete(pid); fetchingModels.value = s }
}

async function saveProvider(pid) {
  const s = new Set(savingProviders.value); s.add(pid); savingProviders.value = s
  try {
    const body = {}
    const key   = getFieldVal(pid, 'pkey')
    const url   = getFieldVal(pid, 'purl')
    const model = getFieldVal(pid, 'pmodel')
    if (key)   body.api_key  = key
    if (url)   body.base_url = url
    if (model) body.model    = model
    await api(`/admin/providers/${pid}`, { method: 'PUT', body })
    toast('配置已保存')
    await loadProviders()
  } catch(e) { toast(e.message, true) }
  finally { const s = new Set(savingProviders.value); s.delete(pid); savingProviders.value = s }
}

async function verifyProvider(pid) {
  const s = new Set(verifyingProviders.value); s.add(pid); verifyingProviders.value = s
  verifyResults.value = { ...verifyResults.value, [pid]: null }
  try {
    const body = {}
    const key   = getFieldVal(pid, 'pkey')
    const url   = getFieldVal(pid, 'purl')
    const model = getFieldVal(pid, 'pmodel')
    if (key)   body.api_key  = key
    if (url)   body.base_url = url
    if (model) body.model    = model
    const res = await api(`/admin/providers/${pid}/verify`, {
      method: 'POST', body: Object.keys(body).length ? body : undefined,
    })
    verifyResults.value = { ...verifyResults.value, [pid]: res }
  } catch(e) {
    verifyResults.value = { ...verifyResults.value, [pid]: { valid: false, detail: e.message } }
  }
  finally { const s = new Set(verifyingProviders.value); s.delete(pid); verifyingProviders.value = s }
}

async function setActive(pid) {
  try {
    await api('/admin/site-config', { method: 'PUT', body: { active_provider: pid } })
    toast('已切换默认模型')
    await loadProviders()
  } catch(e) { toast(e.message, true) }
}

async function deleteProvider(pid) {
  if (!confirm('确定删除该自定义模型商？')) return
  try {
    await api(`/admin/providers/${pid}`, { method: 'DELETE' })
    toast('已删除')
    await loadProviders()
  } catch(e) { toast(e.message, true) }
}

async function addCustomProvider() {
  const { name, base_url, api_key, model } = customForm.value
  if (!name || !base_url || !api_key || !model) return toast('所有字段均为必填', true)
  try {
    await api('/admin/providers/custom', { body: { name, base_url, api_key, model } })
    toast('已添加自定义模型商')
    showCustomForm.value = false
    customForm.value = { name: '', base_url: '', api_key: '', model: '' }
    await loadProviders()
  } catch(e) { toast(e.message, true) }
}

// ── Users ──────────────────────────────────
const users        = ref([])
const usersLoading = ref(false)

async function loadUsers() {
  usersLoading.value = true
  try { users.value = await api('/users') }
  finally { usersLoading.value = false }
}

async function updateRole(uid, role) {
  try {
    await api('/users/' + uid, { method: 'PUT', body: { role } })
    toast('角色已更新')
  } catch(e) { toast(e.message, true) }
}

async function toggleUser(u) {
  const active = u.is_active
  if (!confirm(`确定${active ? '停用' : '启用'}该用户？`)) return
  try {
    await api('/users/' + u.id, {
      method: active ? 'DELETE' : 'PUT',
      body:   active ? undefined : { is_active: true },
    })
    toast(active ? '已停用' : '已启用')
    await loadUsers()
  } catch(e) { toast(e.message, true) }
}

// ── Site ───────────────────────────────────
const siteCfg    = ref({ site_name: '', allow_register: true })
const siteLoading = ref(false)
const savingSite  = ref(false)

async function loadSite() {
  siteLoading.value = true
  try { siteCfg.value = await api('/admin/site-config') }
  finally { siteLoading.value = false }
}

async function saveSite() {
  savingSite.value = true
  try {
    await api('/admin/site-config', { method: 'PUT', body: siteCfg.value })
    toast('站点设置已保存')
  } catch(e) { toast(e.message, true) }
  finally { savingSite.value = false }
}

// ── Tab 切换时懒加载 ────────────────────────
watch(activeTab, (tab) => {
  if (tab === 'providers' && !providers.value.length) loadProviders()
  if (tab === 'users') loadUsers()
  if (tab === 'site') loadSite()
})

onMounted(loadProviders)
</script>
