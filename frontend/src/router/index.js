import { createRouter, createWebHistory } from 'vue-router'
import { showToast } from 'vant'
import { getToken, getUserInfo } from '@/utils/auth'

function defaultPathFor(role) {
  return role === 'admin' ? '/manager/admin/news' : '/manager/news'
}

const routes = [
  {
    path: '/',
    redirect: () => defaultPathFor(getUserInfo()?.role)
  },
  {
    path: '/manager',
    component: () => import('@/layouts/Layout.vue'),
    redirect: () => defaultPathFor(getUserInfo()?.role),
    children: [
      // ------- 普通用户页面 -------
      {
        path: 'news',
        name: 'NewsList',
        component: () => import('@/views/NewsList.vue'),
        meta: { title: '新闻资讯', requiresUser: true }
      },
      {
        path: 'news/:id',
        name: 'NewsDetail',
        component: () => import('@/views/NewsDetail.vue'),
        meta: { title: '新闻详情', requiresUser: true }
      },
      {
        path: 'hot',
        name: 'HotNews',
        component: () => import('@/views/HotNews.vue'),
        meta: { title: '新闻热榜', requiresUser: true }
      },
      {
        path: 'ai-chat',
        name: 'AIChat',
        component: () => import('@/views/AIChat.vue'),
        meta: { title: 'AI 智能助手', requiresUser: true }
      },
      {
        path: 'favorite',
        name: 'Favorite',
        component: () => import('@/views/Favorite.vue'),
        meta: { title: '我的收藏', requiresUser: true }
      },
      {
        path: 'history',
        name: 'History',
        component: () => import('@/views/History.vue'),
        meta: { title: '浏览历史', requiresUser: true }
      },
      {
        path: 'settings',
        name: 'Settings',
        component: () => import('@/views/Settings.vue'),
        meta: { title: '偏好设置', requiresUser: true }
      },
      {
        path: 'profile',
        name: 'Profile',
        component: () => import('@/views/Profile.vue'),
        meta: { title: '个人资料', requiresUser: true }
      },
      {
        path: 'password',
        name: 'Password',
        component: () => import('@/views/Password.vue'),
        meta: { title: '修改密码', requiresUser: true }
      },

      // ------- 管理员页面：严格只有这三个 -------
      {
        path: 'admin/home',
        name: 'AdminHome',
        component: () => import('@/views/admin/Home.vue'),
        meta: { title: '数据总览', requiresAdmin: true }
      },
      {
        path: 'admin/news',
        name: 'AdminNews',
        component: () => import('@/views/admin/NewsManage.vue'),
        meta: { title: '新闻管理', requiresAdmin: true }
      },
      {
        path: 'admin/users',
        name: 'AdminUsers',
        component: () => import('@/views/admin/UserManage.vue'),
        meta: { title: '用户管理', requiresAdmin: true }
      }
    ]
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { title: '登录', public: true }
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/Register.vue'),
    meta: { title: '注册', public: true }
  },

  // 兼容旧版路径（最终仍由角色守卫决定落地页）
  { path: '/home', redirect: '/manager/news' },
  { path: '/aichat', redirect: '/manager/ai-chat' },
  { path: '/category', redirect: '/manager/news' },
  { path: '/my', redirect: '/manager/news' },
  { path: '/favorite', redirect: '/manager/favorite' },
  { path: '/history', redirect: '/manager/history' },
  { path: '/profile', redirect: '/manager/profile' },
  { path: '/settings', redirect: '/manager/settings' },
  { path: '/news/detail/:id', redirect: (to) => `/manager/news/${to.params.id}` }
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
  scrollBehavior() {
    return { top: 0 }
  }
})

router.beforeEach((to) => {
  const token = getToken()
  const user = getUserInfo()

  document.title = to.meta.title ? `${to.meta.title} · AI 新闻资讯平台` : 'AI 新闻资讯平台'

  if (to.meta.public) {
    if (token) return { path: defaultPathFor(user?.role) }
    return true
  }

  if (!token) {
    return { path: '/login', query: { redirect: to.fullPath } }
  }

  // 管理员只能访问「新闻管理」「用户管理」
  if (to.meta.requiresAdmin && user?.role !== 'admin') {
    showToast({ message: '该页面仅管理员可访问', position: 'top' })
    return { path: '/manager/news' }
  }

  // 普通用户不能进入管理员页面；管理员也不能进入用户页面
  if (to.meta.requiresUser && user?.role === 'admin') {
    return { path: '/manager/admin/news' }
  }

  return true
})

export default router
