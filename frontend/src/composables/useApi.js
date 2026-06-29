import { useAuthStore } from '@/stores/auth'

const BASE = '/api/v1'

export async function api(path, { method, body, form, noAuth } = {}) {
  const auth = useAuthStore()
  method = method || (body !== undefined || form ? 'POST' : 'GET')
  const headers = {}
  if (auth.token && !noAuth) headers.Authorization = 'Bearer ' + auth.token
  let payload
  if (form) {
    payload = form
  } else if (body !== undefined) {
    headers['Content-Type'] = 'application/json'
    payload = JSON.stringify(body)
  }
  const r = await fetch(BASE + path, { method, headers, body: payload })
  const data = await r.json().catch(() => ({}))
  if (!r.ok) {
    const msg = data.detail
      ? typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail)
      : '请求失败 ' + r.status
    throw new Error(msg)
  }
  return data
}

export async function downloadFile(path, filename) {
  const auth = useAuthStore()
  const r = await fetch(BASE + path, {
    headers: { Authorization: 'Bearer ' + auth.token },
  })
  if (!r.ok) throw new Error('下载失败 ' + r.status)
  const blob = await r.blob()
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename || 'download'
  a.click()
  URL.revokeObjectURL(url)
}
