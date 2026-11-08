import request from '@/utils/request'
import { getToken } from '@/utils/auth'

export function getAIStatusApi() {
  return request({ url: '/api/ai/status', method: 'get', silent: true })
}

export function chatApi(data) {
  return request({
    url: '/api/ai/chat',
    method: 'post',
    data,
    timeout: 120000
  })
}

export function getChatHistoryApi(params) {
  return request({ url: '/api/ai/history', method: 'get', params })
}

export function clearChatHistoryApi() {
  return request({ url: '/api/ai/history', method: 'delete' })
}

export function getDigestApi(data) {
  return request({
    url: '/api/ai/digest',
    method: 'post',
    data,
    timeout: 120000
  })
}

export function getHotAnalysisApi(data) {
  return request({
    url: '/api/ai/hot-analysis',
    method: 'post',
    data,
    timeout: 120000
  })
}

export function summarizeApi(data) {
  return request({
    url: '/api/ai/summary',
    method: 'post',
    data,
    timeout: 120000
  })
}

/**
 * SSE 流式对话。onEvent(evt) 每收到一条 data 回调一次。
 */
export async function chatStreamApi(data, onEvent) {
  const baseURL = import.meta.env.VITE_API_BASE_URL || ''
  const token = getToken()
  const response = await fetch(`${baseURL}/api/ai/chat/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'text/event-stream',
      ...(token ? { Authorization: `Bearer ${token}` } : {})
    },
    body: JSON.stringify(data)
  })

  if (response.status === 401) {
    throw new Error('登录已失效，请重新登录')
  }
  if (!response.ok || !response.body) {
    throw new Error(`流式接口请求失败（${response.status}）`)
  }

  const contentType = response.headers.get('content-type') || ''
  if (!contentType.includes('text/event-stream')) {
    const payload = await response.json().catch(() => null)
    throw new Error(payload?.message || '流式接口返回异常')
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder('utf-8')
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const chunks = buffer.split('\n\n')
    buffer = chunks.pop() || ''

    for (const chunk of chunks) {
      const line = chunk
        .split('\n')
        .map((item) => item.trim())
        .find((item) => item.startsWith('data:'))
      if (!line) continue
      const raw = line.slice(5).trim()
      if (!raw || raw === '[DONE]') continue
      try {
        onEvent(JSON.parse(raw))
      } catch {
        // 半包或脏数据，跳过
      }
    }
  }
}
