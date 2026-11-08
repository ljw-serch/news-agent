import { marked } from 'marked'
import DOMPurify from 'dompurify'

marked.setOptions({ breaks: true, gfm: true })

export function cleanAIText(text) {
  if (!text) return ''
  return String(text)
    .replace(/\s*:?cite\[[^\]]*\]/gi, '')
    .replace(/\s*\[citation[^\]]*\]/gi, '')
    .trim()
}

export function renderMarkdown(text) {
  if (!text) return ''
  try {
    return DOMPurify.sanitize(marked.parse(cleanAIText(text)))
  } catch {
    return String(text)
  }
}

export function stripMarkdown(text) {
  if (!text) return ''
  return cleanAIText(text)
    .replace(/```[\s\S]*?```/g, ' ')
    .replace(/[#>*`~-]/g, ' ')
    .replace(/\[(.*?)\]\(.*?\)/g, '$1')
    .replace(/\s+/g, ' ')
    .trim()
}

export function formatDate(value, withTime = true) {
  if (!value) return '—'
  const date = value instanceof Date ? value : new Date(value)
  if (Number.isNaN(date.getTime())) return String(value)
  const pad = (n) => String(n).padStart(2, '0')
  const base = `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`
  return withTime ? `${base} ${pad(date.getHours())}:${pad(date.getMinutes())}` : base
}

export function formatRelative(value) {
  if (!value) return '—'
  const date = value instanceof Date ? value : new Date(value)
  if (Number.isNaN(date.getTime())) return String(value)
  const diff = Date.now() - date.getTime()
  const minute = 60 * 1000
  const hour = 60 * minute
  const day = 24 * hour
  if (diff < minute) return '刚刚'
  if (diff < hour) return `${Math.floor(diff / minute)} 分钟前`
  if (diff < day) return `${Math.floor(diff / hour)} 小时前`
  if (diff < 7 * day) return `${Math.floor(diff / day)} 天前`
  return formatDate(date, false)
}

export function formatNumber(value) {
  const number = Number(value || 0)
  return number.toLocaleString('zh-CN')
}

export function truncate(text, length = 80) {
  const value = stripMarkdown(text)
  return value.length > length ? `${value.slice(0, length)}…` : value
}

export function initials(name) {
  const value = String(name || '?').trim()
  return value.slice(0, 1).toUpperCase()
}

export function roleText(role) {
  return role === 'admin' ? '管理员' : '普通用户'
}
