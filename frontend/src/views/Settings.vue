<template>
  <div>
    <div class="page-head">
      <div>
        <div class="page-title">偏好设置</div>
        <div class="page-sub">主题与语言会保存在本机，下次打开自动生效</div>
      </div>
    </div>

    <div class="grid-2">
      <div class="card">
        <div class="card-head">
          <div class="card-title">
            <van-icon name="brush-o" />
            主题定制
          </div>
          <span class="tag">{{ themeStore.theme.label }}</span>
        </div>

        <div class="theme-grid">
          <div
            v-for="item in themeStore.themeList"
            :key="item.key"
            class="theme-card"
            :class="{ active: themeStore.currentTheme === item.key }"
            @click="chooseTheme(item.key)"
          >
            <div class="theme-preview" :style="{ background: item.bg }">
              <div class="theme-preview-bar" :style="{ background: item.card }">
                <span :style="{ background: item.primary }"></span>
                <span :style="{ background: item.border }"></span>
              </div>
              <div class="theme-preview-body">
                <i :style="{ background: item.primary }"></i>
                <div>
                  <b :style="{ background: item.text }"></b>
                  <b :style="{ background: item.border }"></b>
                </div>
              </div>
            </div>
            <div class="theme-name">
              <span>{{ item.label }}</span>
              <van-icon v-if="themeStore.currentTheme === item.key" name="success" />
            </div>
          </div>
        </div>

        <div class="muted" style="font-size: 11.5px; margin-top: 12px; line-height: 1.7">
          主题通过 CSS 变量统一生效，覆盖顶栏、侧边栏、卡片、表格与 Vant 组件。
        </div>
      </div>

      <div class="stack">
        <div class="card">
          <div class="card-head">
            <div class="card-title">
              <van-icon name="font-o" />
              语言设置
            </div>
          </div>
          <div class="form-item">
            <label class="form-label">界面语言</label>
            <select v-model="language" class="select" @change="changeLanguage">
              <option value="zh-CN">简体中文</option>
              <option value="en-US">English</option>
            </select>
          </div>
          <div class="muted" style="font-size: 11.5px; margin-top: 10px; line-height: 1.7">
            导航、页面标题等文案会随语言切换；新闻内容仍保持原文。
          </div>
        </div>

        <div class="card">
          <div class="card-head">
            <div class="card-title">
              <van-icon name="bar-chart-o" />
              系统状态
            </div>
          </div>
          <div class="info-list">
            <div><span>AI 模式</span><b>{{ aiStatus.enabled ? '大模型在线' : '本地规则引擎' }}</b></div>
            <div><span>模型</span><b>{{ aiStatus.model || '—' }}</b></div>
            <div><span>当前主题</span><b>{{ themeStore.theme.label }}</b></div>
            <div><span>当前语言</span><b>{{ language === 'en-US' ? 'English' : '简体中文' }}</b></div>
          </div>
        </div>

        <div class="card">
          <div class="card-head">
            <div class="card-title">
              <van-icon name="setting-o" />
              账户
            </div>
          </div>
          <div class="stack" style="gap: 8px">
            <van-button size="small" block icon="user-o" @click="$router.push('/manager/profile')">
              编辑个人资料
            </van-button>
            <van-button size="small" block icon="lock" @click="$router.push('/manager/password')">
              修改密码
            </van-button>
            <van-button size="small" block icon="revoke" @click="handleLogout">退出登录</van-button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { showToast } from 'vant'
import { useThemeStore } from '@/store/theme'
import { useLanguageStore } from '@/store/language'
import { useUserStore } from '@/store/user'
import { getAIStatusApi } from '@/api/ai'
import { logoutApi } from '@/api/auth'

const router = useRouter()
const { t, locale } = useI18n()
const themeStore = useThemeStore()
const languageStore = useLanguageStore()
const userStore = useUserStore()

const language = ref(languageStore.currentLanguage || 'zh-CN')
const aiStatus = ref({ enabled: false, model: '' })

function chooseTheme(key) {
  themeStore.setTheme(key)
  showToast({ message: `已切换为${themeStore.theme.label}`, position: 'top' })
}

function changeLanguage() {
  languageStore.setLanguage(language.value)
  locale.value = language.value
  document.documentElement.setAttribute('lang', language.value)
  showToast({ message: t('settings.languageChanged'), position: 'top' })
}

async function handleLogout() {
  try {
    await logoutApi()
  } catch {
    // 忽略
  }
  userStore.logout()
  router.push('/login')
}

onMounted(async () => {
  try {
    const res = await getAIStatusApi()
    aiStatus.value = res.data || aiStatus.value
  } catch {
    // 忽略
  }
})
</script>

<style scoped>
.theme-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 12px;
}

.theme-card {
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 8px;
  cursor: pointer;
  transition: 0.18s;
  background: var(--bg);
}

.theme-card:hover {
  border-color: var(--primary);
}

.theme-card.active {
  border-color: var(--primary);
  box-shadow: 0 0 0 3px var(--primary-soft);
}

.theme-preview {
  height: 84px;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid var(--border);
  padding: 7px;
  display: flex;
  flex-direction: column;
  gap: 7px;
}

.theme-preview-bar {
  height: 14px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 0 5px;
}

.theme-preview-bar span {
  height: 4px;
  border-radius: 2px;
}

.theme-preview-bar span:first-child {
  width: 18px;
}

.theme-preview-bar span:last-child {
  width: 32px;
  opacity: 0.5;
}

.theme-preview-body {
  flex: 1;
  display: flex;
  gap: 6px;
  align-items: flex-start;
}

.theme-preview-body i {
  width: 24px;
  height: 100%;
  border-radius: 4px;
  opacity: 0.8;
}

.theme-preview-body div {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 5px;
  padding-top: 2px;
}

.theme-preview-body b {
  display: block;
  height: 5px;
  border-radius: 2px;
  opacity: 0.6;
}

.theme-preview-body b:first-child {
  width: 70%;
}

.theme-preview-body b:last-child {
  width: 45%;
}

.theme-name {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 12px;
  font-weight: 600;
  padding: 8px 3px 2px;
}

.theme-name .van-icon {
  color: var(--primary);
}

.info-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.info-list > div {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  font-size: 12px;
}

.info-list span {
  color: var(--sub);
}

.info-list b {
  font-weight: 600;
  text-align: right;
}
</style>
