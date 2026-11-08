import { storeToRefs } from 'pinia'
import { useUserStore } from '@/store/user'

/**
 * 供页面 setup 使用：
 * const { userInfo } = useUser()
 */
export function useUser() {
  const store = useUserStore()
  const { userInfo } = storeToRefs(store)

  return {
    userInfo,
    saveLoginData: store.saveLoginData,
    updateUser: store.updateUser,
    reloadUser: store.reloadUser,
    logout: store.logout
  }
}
