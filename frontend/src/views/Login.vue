<template>
  <div class="auth-page">
    <div class="auth-card">
      <div class="auth-brand">
        <img src="/logo.png" alt="logo" />
        <div>
          <div class="auth-title">{{ t('auth.loginTitle') }}</div>
          <div class="auth-sub">{{ t('auth.loginSub') }}</div>
        </div>
      </div>

      <div class="auth-hello">登录后即可查看数据总览、AI 摘要、热榜与发布统计。</div>

      <form @submit.prevent="handleLogin">
        <div class="auth-field">
          <label class="form-label">账号</label>
          <input
            v-model.trim="form.username"
            class="input"
            placeholder="请输入账号"
            autocomplete="username"
          />
        </div>
        <div class="auth-field">
          <label class="form-label">密码</label>
          <input
            v-model="form.password"
            class="input"
            type="password"
            placeholder="请输入密码"
            autocomplete="current-password"
          />
        </div>

        <div v-if="errorText" class="form-error" style="margin-bottom: 8px">
          {{ errorText }}
        </div>

        <van-button
          type="primary"
          block
          round
          size="large"
          native-type="submit"
          :loading="loading"
          style="margin-top: 12px"
        >
          登 录
        </van-button>
      </form>

      <div class="auth-footer">
        还没有账号？
        <router-link to="/register">{{ t('auth.register') }}</router-link>
      </div>

    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showToast } from 'vant'
import { useI18n } from 'vue-i18n'
import { loginApi } from '@/api/auth'
import { useUserStore } from '@/store/user'

const { t } = useI18n()
const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const form = reactive({ username: '', password: '' })
const loading = ref(false)
const errorText = ref('')

async function handleLogin() {
  errorText.value = ''
  if (!form.username || !form.password) {
    errorText.value = '请输入账号和密码'
    return
  }
  loading.value = true
  try {
    const res = await loginApi({ username: form.username, password: form.password })
    if (res.code === 200 && res.data) {
      userStore.saveLoginData(res.data)
      showToast({ message: '登录成功', position: 'top' })
      // 管理员与普通用户进入完全不同的页面集合
      if (res.data.user.role === 'admin') {
        router.push('/manager/admin/news')
      } else {
        const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : ''
        const target = redirect.startsWith('/manager/') && !redirect.startsWith('/manager/admin')
          ? redirect
          : '/manager/news'
        router.push(target)
      }
    }
  } catch (error) {
    errorText.value = error?.message || '登录失败，请检查账号密码'
  } finally {
    loading.value = false
  }
}
</script>
