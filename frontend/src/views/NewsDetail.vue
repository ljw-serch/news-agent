<template>
  <div>
    <div class="page-head">
      <div style="display: flex; align-items: center; gap: 10px">
        <van-button size="small" icon="arrow-left" @click="$router.back()">返回</van-button>
        <div>
          <div class="page-title">新闻详情</div>
          <div class="page-sub">阅读、收藏，并让 AI 帮你提炼重点</div>
        </div>
      </div>
      <div class="page-actions">
        <van-button
          size="small"
          :icon="detail.is_favorite ? 'star' : 'star-o'"
          :type="detail.is_favorite ? 'warning' : 'default'"
          @click="toggleFavorite"
        >
          {{ detail.is_favorite ? '已收藏' : '收藏' }}
        </van-button>
        <template v-if="userStore.isAdmin">
          <van-button size="small" icon="edit" @click="editNews">编辑</van-button>
          <van-button size="small" type="danger" icon="delete-o" @click="removeNews">
            删除
          </van-button>
        </template>
      </div>
    </div>

    <div v-if="loading" class="card">
      <div class="skeleton" style="height: 28px; width: 70%; margin-bottom: 14px"></div>
      <div class="skeleton" style="height: 16px; width: 100%; margin-bottom: 10px"></div>
      <div class="skeleton" style="height: 16px; width: 92%; margin-bottom: 10px"></div>
      <div class="skeleton" style="height: 300px; width: 100%; margin-top: 20px"></div>
    </div>

    <div v-else-if="detail.id" class="article-layout">
      <article class="article">
        <div style="margin-bottom: 12px; display: flex; gap: 8px; flex-wrap: wrap">
          <span v-if="detail.category_name" class="tag">{{ detail.category_name }}</span>
          <span v-if="detail.summary" class="tag success">AI 已摘要</span>
          <span class="tag muted">ID {{ detail.id }}</span>
        </div>

        <h1 class="article-title">{{ detail.title }}</h1>
        <div class="article-meta">
          <span>{{ detail.author || '平台编辑' }}</span>
          <span class="dot"></span>
          <span>{{ formatDate(detail.publish_time) }}</span>
          <span class="dot"></span>
          <span><van-icon name="eye-o" /> {{ formatNumber(detail.views) }} 阅读</span>
          <span class="dot"></span>
          <span><van-icon name="star-o" /> {{ formatNumber(detail.favorite_count) }} 收藏</span>
        </div>

        <img
          v-if="detail.image && !coverError"
          class="article-cover"
          :src="detail.image"
          :alt="detail.title"
          @error="coverError = true"
        />

        <div class="article-content">
          <p v-for="(paragraph, index) in contentParagraphs" :key="index">
            {{ paragraph }}
          </p>
        </div>

        <div class="article-toolbar">
          <van-button
            size="small"
            :icon="detail.is_favorite ? 'star' : 'star-o'"
            :type="detail.is_favorite ? 'warning' : 'default'"
            @click="toggleFavorite"
          >
            {{ detail.is_favorite ? '取消收藏' : '收藏这篇新闻' }}
          </van-button>
          <van-button size="small" icon="chat-o" @click="$router.push('/manager/ai-chat')">
            继续问 AI
          </van-button>
          <van-button size="small" icon="arrow-left" @click="$router.back()">返回列表</van-button>
        </div>
      </article>

      <aside class="stack">
        <div class="card">
          <div class="card-head">
            <div class="card-title">
              <van-icon name="bulb-o" />
              AI 摘要
            </div>
            <span class="tag" :class="detail.summary ? 'success' : 'muted'">
              {{ detail.summary ? '已生成' : '未生成' }}
            </span>
          </div>

          <div v-if="summaryLoading" class="empty-box" style="padding: 26px 8px">
            <van-loading size="20" />
            <div style="margin-top: 8px">正在阅读并提炼重点…</div>
          </div>

          <template v-else-if="detail.summary">
            <div class="markdown" v-html="renderMarkdown(detail.summary)"></div>
            <div v-if="detail.highlight" class="summary-highlight">
              <van-icon name="certificate" />
              <span>{{ detail.highlight }}</span>
            </div>
            <div class="row-between" style="margin-top: 12px">
              <span class="muted" style="font-size: 11px">
                {{ detail.summary_time ? formatDate(detail.summary_time) : '' }}
              </span>
              <van-button size="mini" :loading="summaryLoading" @click="generateSummary">
                重新生成
              </van-button>
            </div>
          </template>

          <template v-else>
            <div class="muted" style="font-size: 12px; line-height: 1.7">
              让 AI 阅读全文，生成 100-180 字摘要、关键信息与一句话看点。
            </div>
            <van-button
              size="small"
              type="primary"
              style="margin-top: 12px"
              icon="bulb-o"
              :loading="summaryLoading"
              @click="generateSummary"
            >
              生成 AI 摘要
            </van-button>
          </template>
        </div>

        <div class="card" v-if="detail.related?.length">
          <div class="card-head">
            <div class="card-title">
              <van-icon name="notes-o" />
              相关推荐
            </div>
          </div>
          <div
            v-for="item in detail.related"
            :key="item.id"
            class="related-item"
            @click="goRelated(item.id)"
          >
            <div class="related-title">{{ item.title }}</div>
            <div class="related-meta">
              {{ item.category_name || '未分类' }} · {{ formatDate(item.publish_time, false) }}
            </div>
          </div>
        </div>
      </aside>
    </div>

    <div v-else class="card">
      <EmptyState text="新闻不存在或已被删除" icon="warning-o">
        <van-button size="small" style="margin-top: 12px" @click="$router.push('/manager/news')">
          返回新闻列表
        </van-button>
      </EmptyState>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showConfirmDialog, showToast } from 'vant'
import EmptyState from '@/components/EmptyState.vue'
import { useUserStore } from '@/store/user'
import { deleteNewsApi, generateNewsSummaryApi, getNewsDetailApi } from '@/api/news'
import { addFavoriteApi, removeFavoriteApi } from '@/api/favorite'
import { addHistoryApi } from '@/api/history'
import { formatDate, formatNumber, renderMarkdown } from '@/utils/format'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const detail = ref({})
const loading = ref(false)
const summaryLoading = ref(false)
const coverError = ref(false)

const newsId = computed(() => Number(route.params.id))

const contentParagraphs = computed(() => {
  const content = detail.value.content || ''
  return content
    .split(/\n+/)
    .map((item) => item.trim())
    .filter(Boolean)
})

async function loadDetail() {
  loading.value = true
  detail.value = {}
  coverError.value = false
  try {
    const res = await getNewsDetailApi(newsId.value)
    detail.value = res.data || {}
    if (detail.value.id) {
      addHistoryApi(detail.value.id).catch(() => {})
    }
  } catch {
    detail.value = {}
  } finally {
    loading.value = false
  }
}

async function toggleFavorite() {
  if (!userStore.isLogin) {
    router.push({ path: '/login', query: { redirect: route.fullPath } })
    return
  }
  try {
    if (detail.value.is_favorite) {
      await removeFavoriteApi(detail.value.id)
      detail.value.is_favorite = false
      detail.value.favorite_count = Math.max((detail.value.favorite_count || 1) - 1, 0)
      showToast({ message: '已取消收藏', position: 'top' })
    } else {
      await addFavoriteApi(detail.value.id)
      detail.value.is_favorite = true
      detail.value.favorite_count = (detail.value.favorite_count || 0) + 1
      showToast({ message: '收藏成功', position: 'top' })
    }
  } catch {
    // 拦截器已提示
  }
}

async function generateSummary() {
  summaryLoading.value = true
  try {
    const res = await generateNewsSummaryApi(detail.value.id, true)
    detail.value.summary = res.data?.summary
    detail.value.highlight = res.data?.highlight
    detail.value.summary_time = res.data?.summary_time
    showToast({ message: 'AI 摘要已生成', position: 'top' })
  } catch {
    // 拦截器已提示
  } finally {
    summaryLoading.value = false
  }
}

function editNews() {
  router.push(`/manager/admin/news?edit=${detail.value.id}`)
}

async function removeNews() {
  try {
    await showConfirmDialog({
      title: '删除新闻',
      message: `确认删除《${detail.value.title}》？该操作不可恢复。`,
      confirmButtonText: '确认删除',
      confirmButtonColor: '#ee0a24'
    })
  } catch {
    return
  }
  try {
    await deleteNewsApi(detail.value.id)
    showToast({ message: '新闻已删除', position: 'top' })
    router.push('/manager/admin/news')
  } catch {
    // 拦截器已提示
  }
}

function goRelated(id) {
  router.push(`/manager/news/${id}`)
}

watch(newsId, () => {
  if (newsId.value) loadDetail()
})

onMounted(loadDetail)
</script>

<style scoped>
.summary-highlight {
  display: flex;
  align-items: flex-start;
  gap: 7px;
  margin-top: 12px;
  padding: 9px 11px;
  border-radius: 9px;
  background: var(--primary-soft);
  color: var(--primary);
  font-size: 12px;
  line-height: 1.6;
}

.related-item {
  padding: 9px 0;
  border-bottom: 1px dashed var(--border);
  cursor: pointer;
}

.related-item:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

.related-item:hover .related-title {
  color: var(--primary);
}

.related-title {
  font-size: 12.5px;
  font-weight: 600;
  line-height: 1.5;
  transition: 0.16s;
}

.related-meta {
  font-size: 10.5px;
  color: var(--sub);
  margin-top: 3px;
}
</style>
