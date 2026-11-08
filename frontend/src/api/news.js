import request from '@/utils/request'

export function getCategoriesApi() {
  return request({ url: '/api/news/categories', method: 'get' })
}

export function getNewsPageApi(params) {
  return request({ url: '/api/news/list', method: 'get', params })
}


export function getHotNewsApi(params) {
  return request({ url: '/api/news/hot', method: 'get', params })
}

export function getNewsDetailApi(id) {
  return request({ url: `/api/news/${id}`, method: 'get' })
}

export function searchNewsApi(params) {
  return request({ url: '/api/news/search', method: 'get', params })
}

export function createNewsApi(data) {
  return request({ url: '/api/news', method: 'post', data, timeout: 90000 })
}

export function updateNewsApi(id, data) {
  return request({ url: `/api/news/${id}`, method: 'put', data, timeout: 90000 })
}

export function deleteNewsApi(id) {
  return request({ url: `/api/news/${id}`, method: 'delete' })
}

export function getNewsSummaryApi(id) {
  return request({ url: `/api/news/${id}/summary`, method: 'get' })
}

export function generateNewsSummaryApi(id, force = false) {
  return request({
    url: `/api/news/${id}/summary`,
    method: 'post',
    params: { force },
    timeout: 120000
  })
}

export function batchSummaryApi(params) {
  return request({
    url: '/api/news/summaries/batch',
    method: 'post',
    params,
    timeout: 300000
  })
}
