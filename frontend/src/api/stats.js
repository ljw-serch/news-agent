import request from '@/utils/request'

export function getOverviewApi() {
  return request({ url: '/api/stats/overview', method: 'get' })
}

export function getTrendApi(days = 7) {
  return request({ url: '/api/stats/trend', method: 'get', params: { days } })
}

export function getCategoryStatsApi() {
  return request({ url: '/api/stats/categories', method: 'get' })
}

export function getAuthorStatsApi(limit = 10) {
  return request({ url: '/api/stats/authors', method: 'get', params: { limit } })
}

export function getPublishRangeApi(params) {
  return request({ url: '/api/stats/publish-range', method: 'get', params })
}
