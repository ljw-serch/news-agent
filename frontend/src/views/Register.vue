<template>
  <div class="auth-page">
    <div class="auth-card">
      <div class="auth-brand">
        <img src="/logo.png" alt="logo" />
        <div>
          <div class="auth-title">创建普通用户账号</div>
          <div class="auth-sub">注册后即可收藏、浏览历史与使用 AI 助手</div>
        </div>
      </div>

      <form @submit.prevent="handleRegister" style="margin-top: 18px">
        <div class="auth-field">
          <label class="form-label">账号</label>
          <input
            v-model.trim="form.username"
            class="input"
            placeholder="2-50 位账号"
            autocomplete="username"
          />
        </div>
        <div class="auth-field">
          <label class="form-label">昵称</label>
          <input v-model.trim="form.nickname" class="input" placeholder="可选，默认同账号" />
        </div>
        <div class="auth-field">
          <label class="form-label">密码</label>
          <input
            v-model="form.password"
            class="input"
            type="password"
            placeholder="至少 3 位"
            autocomplete="new-password"
          />
        </div>
        <div class="auth-field">
          <label class="form-label">确认密码</label>
          <input
            v-model="form.confirm"
            class="input"
            type="password"
            placeholder="再次输入密码"
            autocomplete="new-password"
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
          注 册
        </van-button>
      </form>

      <div class="auth-footer">
        已有账号？
        <router-link to="/login">{{ t('auth.login') }}</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { showToast } from 'vant'
import { useI18n } from 'vue-i18n'
import { registerApi } from '@/api/auth'
import { useUserStore } from '@/store/user'

const { t } = useI18n()
const router = useRouter()
const userStore = useUserStore()

const form = reactive({ username: '', nickname: '', password: '', confirm: '' })
const loading = ref(false)
const errorText = ref('')

async function handleRegister() {
  errorText.value = ''
  if (!form.username || form.username.length < 2) {
    errorText.value = '账号至少 2 个字符'
    return
  }
  if (form.password.length < 3) {
    errorText.value = '密码至少 3 个字符'
    return
  }
  if (form.password !== form.confirm) {
    errorText.value = '两次输入的密码不一致'
    return
  }
  loading.value = true
  try {
    const res = await registerApi({
      username: form.username,
      password: form.password,
      nickname: form.nickname || form.username
    })
    if (res.code === 200 && res.data) {
      userStore.saveLoginData(res.data)
      showToast({ message: '注册成功，已自动登录', position: 'top' })
      router.push('/manager/news')
    }
  } catch (error) {
    errorText.value = error?.message || '注册失败，请稍后重试'
  } finally {
    loading.value = false
  }
}
</script>
