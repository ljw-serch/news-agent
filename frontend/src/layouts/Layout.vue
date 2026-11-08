<template>
  <div class="layout">
    <header class="layout-header">
      <div class="mobile-menu-btn" @click="drawerOpen = true">
        <van-icon name="wap-nav" />
      </div>

      <div class="brand" @click="go(homePath)">
        <img src="/logo.png" alt="logo" />
        <div>
          <div class="brand-title">AI 新闻资讯平台</div>
          <div class="brand-sub">News Intelligence Console</div>
        </div>
      </div>

      <div class="header-right">
        <span class="role-pill">
          <van-icon :name="isAdmin ? 'shield-o' : 'user-o'" />
          {{ roleLabel }}
        </span>
        <div class="user-chip" @click.stop="menuOpen = !menuOpen">
          <div class="user-avatar">
            <img v-if="userInfo?.avatar" :src="userInfo.avatar" alt="avatar" />
            <span v-else>{{ initials(displayName) }}</span>
          </div>
          <span class="user-name">{{ displayName }}</span>
          <van-icon class="user-caret" name="arrow-down" />
        </div>
      </div>
    </header>

    <div v-if="menuOpen" class="menu-mask" @click="menuOpen = false"></div>
    <div v-if="menuOpen" class="user-menu" @click.stop>
      <div class="user-menu-head">
        <div class="user-avatar" style="width: 38px; height: 38px">
          <img v-if="userInfo?.avatar" :src="userInfo.avatar" alt="avatar" />
          <span v-else>{{ initials(displayName) }}</span>
        </div>
        <div>
          <div class="user-menu-name">{{ displayName }}</div>
          <div class="user-menu-role">{{ roleLabel }} · {{ userInfo?.username }}</div>
        </div>
      </div>
      <div class="user-menu-divider"></div>
      <template v-if="!isAdmin">
        <div class="user-menu-item" @click="handleMenu('/manager/profile')">
          <van-icon name="user-o" /> 个人资料
        </div>
        <div class="user-menu-item" @click="handleMenu('/manager/password')">
          <van-icon name="lock" /> 修改密码
        </div>
        <div class="user-menu-item" @click="handleMenu('/manager/settings')">
          <van-icon name="setting-o" /> 偏好设置
        </div>
      </template>
      <template v-else>
        <div class="user-menu-item" @click="handleMenu('/manager/admin/home')">
          <van-icon name="edit" /> 数据总览
        </div>
        <div class="user-menu-item" @click="handleMenu('/manager/admin/news')">
          <van-icon name="edit" /> 新闻管理
        </div>
        <div class="user-menu-item" @click="handleMenu('/manager/admin/users')">
          <van-icon name="friends-o" /> 用户管理
        </div>
      </template>
      <div class="user-menu-divider"></div>
      <div class="user-menu-item danger" @click="handleLogout">
        <van-icon name="revoke" /> 退出登录
      </div>
    </div>

    <div class="layout-body">
      <aside class="layout-aside">
        <NavList :groups="navGroups" @select="go" />
      </aside>

      <main class="layout-main">
        <router-view />
      </main>
    </div>

    <van-popup
      v-model:show="drawerOpen"
      position="left"
      :style="{ width: '250px', height: '100%' }"
      class="mobile-drawer"
    >
      <div class="drawer-brand">
        <img src="/logo.png" alt="logo" />
        <div>
          <div class="brand-title" style="font-size: 16px">AI 新闻资讯</div>
          <div class="brand-sub">Intelligence Console</div>
        </div>
      </div>
      <NavList :groups="navGroups" @select="go" />
    </van-popup>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import NavList from '@/components/NavList.vue'
import { useUserStore } from '@/store/user'
import { getMeApi } from '@/api/user'
import { logoutApi } from '@/api/auth'
import { initials } from '@/utils/format'

const router = useRouter()
const { t } = useI18n()
const userStore = useUserStore()

const menuOpen = ref(false)
const drawerOpen = ref(false)

const userInfo = computed(() => userStore.userInfo)
const isAdmin = computed(() => userStore.isAdmin)
const roleLabel = computed(() => (isAdmin.value ? '管理员' : '普通用户'))
const displayName = computed(() => userStore.displayName)
const homePath = computed(() => (isAdmin.value ? '/manager/admin/news' : '/manager/news'))

const navGroups = computed(() => {
  // 管理员：保留「新闻管理」「用户管理」「数据总览」三个页面
  if (isAdmin.value) {
    return [
      {
        label: t('nav.adminGroup'),
        items: [
          { label: t('nav.home'), icon: 'home-o', path: '/manager/admin/home' },
          { label: t('nav.adminNews'), icon: 'edit', path: '/manager/admin/news' },
          { label: t('nav.adminUsers'), icon: 'friends-o', path: '/manager/admin/users' }
        ]
      }
    ]
  }

  // 普通用户：保留新闻浏览、热榜、AI 助手、收藏、历史与账户设置
  return [
    {
      label: t('nav.contentGroup'),
      items: [
        { label: t('nav.news'), icon: 'notes-o', path: '/manager/news' },
        { label: t('nav.hot'), icon: 'fire-o', path: '/manager/hot' },
        { label: t('nav.aiChat'), icon: 'chat-o', path: '/manager/ai-chat' }

      ]
    },
    {
      label: '我的内容',
      items: [
        { label: t('nav.favorite'), icon: 'star-o', path: '/manager/favorite' },
        { label: t('nav.history'), icon: 'clock-o', path: '/manager/history' }
      ]
    },
    {
      label: t('nav.accountGroup'),
      items: [
        { label: t('nav.profile'), icon: 'user-o', path: '/manager/profile' },
        { label: t('nav.password'), icon: 'lock', path: '/manager/password' },
        { label: t('nav.settings'), icon: 'setting-o', path: '/manager/settings' }
      ]
    }
  ]
})

function go(path) {
  menuOpen.value = false
  drawerOpen.value = false
  if (router.currentRoute.value.path !== path) {
    router.push(path)
  }
}

function handleMenu(path) {
  menuOpen.value = false
  go(path)
}

async function handleLogout() {
  menuOpen.value = false
  try {
    await logoutApi()
  } catch {
    // 忽略登出接口异常，前端清理即可
  }
  userStore.logout()
  router.push('/login')
}

onMounted(async () => {
  if (!userStore.token) return
  try {
    const res = await getMeApi()
    if (res.code === 200 && res.data) {
      userStore.updateUser(res.data)
      // 角色刚刷新时修正落地页：管理员只能停留在两个管理页
      const role = res.data.role
      const current = router.currentRoute.value.path
      if (role === 'admin' && !current.startsWith('/manager/admin')) {
        router.replace('/manager/admin/news')
      } else if (role !== 'admin' && current.startsWith('/manager/admin')) {
        router.replace('/manager/news')
      }
    }
  } catch {
    // 401 已由 request 拦截器处理
  }
})
</script>

<style scoped>
.menu-mask {
  position: fixed;
  inset: 0;
  z-index: 50;
  background: rgba(10, 20, 40, 0.06);
}

.user-menu {
  top: 58px;
}

.user-menu-head {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px 10px;
}

.user-menu-name {
  font-size: 13px;
  font-weight: 700;
}

.user-menu-role {
  font-size: 11px;
  color: var(--sub);
  margin-top: 2px;
}

.mobile-drawer {
  padding: 18px 12px;
  background: var(--card);
}

.drawer-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 10px 18px;
  border-bottom: 1px solid var(--border);
  margin-bottom: 14px;
}

.drawer-brand img {
  width: 34px;
  height: 34px;
}

@media (max-width: 640px) {
  .brand-title {
    font-size: 15px;
  }
}
</style>
