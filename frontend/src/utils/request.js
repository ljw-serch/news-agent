import axios from 'axios'
import { showToast } from 'vant'
import router from '@/router'
import { getToken, logout } from './auth'

const service = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '',
  timeout: 60000
})

service.interceptors.request.use(
  (config) => {
    const token = getToken()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

function handleUnauthorized() {
  logout()
  const current = router.currentRoute.value
  if (current.path !== '/login') {
    router.push({ path: '/login', query: { redirect: current.fullPath } })
  }
}

service.interceptors.response.use(
  (response) => {
    const data = response.data
    if (data && typeof data.code !== 'undefined' && data.code !== 200) {
      if (!response.config.silent) {
        showToast({ message: data.message || '请求失败', position: 'top' })
      }
      if (data.code === 401) {
        handleUnauthorized()
      }
      return Promise.reject(data)
    }
    return data
  },
  (error) => {
    const silent = error.config?.silent
    if (error.response) {
      const status = error.response.status
      if (status === 401) {
        if (!silent) showToast({ message: '登录已失效，请重新登录', position: 'top' })
        handleUnauthorized()
      } else if (!silent) {
        showToast({
          message: error.response.data?.message || `请求失败（${status}）`,
          position: 'top'
        })
      }
    } else if (!silent) {
      showToast({ message: '网络异常，请确认后端服务已启动', position: 'top' })
    }
    return Promise.reject(error)
  }
)

export default service
