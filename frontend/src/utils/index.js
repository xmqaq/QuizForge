export const esc = (s) =>
  (s ?? '').toString().replace(/[&<>"]/g, (c) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;',
  }[c]))

export const LABEL = {
  status:     { published: '已发布', draft: '草稿', archived: '已归档' },
  qstatus:    { approved: '已通过', pending_review: '待审核', rejected: '已拒绝' },
  difficulty: { easy: '基础', medium: '进阶', hard: '综合' },
  mode:       { random: '随机', sequential: '顺序', wrong_only: '错题', simulation: '模拟' },
  industry:   { it: 'IT', medical: '医疗', finance: '金融', education: '教育', construction: '建筑', language: '语言', other: '其他' },
}

export const L = (type, val) => LABEL[type]?.[val] || val
