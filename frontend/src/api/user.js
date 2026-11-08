import request from '@/utils/request'

export function getMeApi() {
  return request({ url: '/api/user/me', method: 'get' })
}

export function updateMeApi(data) {
  return request({ url: '/api/user/me', method: 'put', data })
}

export function updatePasswordApi(data) {
  return request({ url: '/api/user/password', method: 'put', data })
}

export function getUserPageApi(params) {
  return request({ url: '/api/user/list', method: 'get', params })
}

export function createUserApi(data) {
  return request({ url: '/api/user', method: 'post', data })
}

export function updateUserApi(userId, data) {
  return request({ url: `/api/user/${userId}`, method: 'put', data })
}

export function deleteUserApi(userId) {
  return request({ url: `/api/user/${userId}`, method: 'delete' })
}
