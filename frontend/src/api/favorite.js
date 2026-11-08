import request from '@/utils/request'

export function checkFavoriteApi(newsId) {
  return request({
    url: '/api/favorite/check',
    method: 'get',
    params: { newsId }
  })
}

export function addFavoriteApi(newsId) {
  return request({ url: '/api/favorite/add', method: 'post', data: { news_id: newsId } })
}

export function removeFavoriteApi(newsId) {
  return request({
    url: '/api/favorite/remove',
    method: 'delete',
    params: { newsId }
  })
}

export function getFavoritePageApi(params) {
  return request({ url: '/api/favorite/list', method: 'get', params })
}

export function clearFavoritesApi() {
  return request({ url: '/api/favorite/clear', method: 'delete' })
}
