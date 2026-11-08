import request from '@/utils/request'

export function addHistoryApi(newsId) {
  return request({
    url: '/api/history/add',
    method: 'post',
    data: { news_id: newsId },
    silent: true
  })
}

export function getHistoryPageApi(params) {
  return request({ url: '/api/history/list', method: 'get', params })
}

export function deleteHistoryApi(historyId) {
  return request({ url: `/api/history/delete/${historyId}`, method: 'delete' })
}

export function clearHistoryApi() {
  return request({ url: '/api/history/clear', method: 'delete' })
}
