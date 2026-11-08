import { defineStore } from 'pinia'
import {
  getToken,
  getUserInfo,
  removeToken,
  removeUserInfo,
  setToken,
  setUserInfo
} from '@/utils/auth'

export const useUserStore = defineStore('user', {
  state: () => ({
    token: getToken() || '',
    userInfo: getUserInfo()
  }),

  getters: {
    isLogin: (state) => Boolean(state.token),
    isAdmin: (state) => state.userInfo?.role === 'admin',
    displayName: (state) =>
      state.userInfo?.nickname || state.userInfo?.username || '未登录',
    roleLabel: (state) => (state.userInfo?.role === 'admin' ? '管理员' : '普通用户')
  },

  actions: {
    saveLoginData(data) {
      this.token = data.token
      this.userInfo = data.user
      setToken(data.token)
      setUserInfo(data.user)
    },

    updateUser(user) {
      this.userInfo = user
      setUserInfo(user)
    },

    reloadUser() {
      this.userInfo = getUserInfo()
      this.token = getToken() || ''
    },

    logout() {
      this.token = ''
      this.userInfo = null
      removeToken()
      removeUserInfo()
    }
  }
})
