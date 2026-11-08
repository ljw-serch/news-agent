<template>
  <div>
    <div class="page-head">
      <div>
        <div class="page-title">新闻资讯</div>
        <div class="page-sub">
          共 {{ formatNumber(total) }} 篇新闻 · 按发布时间倒序 · 支持分类与关键词检索
        </div>
      </div>
      <div class="page-actions">
        <van-button size="small" icon="fire-o" @click="$router.push('/manager/hot')">
          查看热榜
        </van-button>
        <van-button
          v-if="userStore.isAdmin"
          size="small"
          type="primary"
          icon="plus"
          @click="$router.push('/manager/admin/news')"
        >
          新增新闻
        </van-button>
      </div>
    </div>

    <div class="card" style="margin-bottom: 16px; padding: 14px 16px">
      <div class="toolbar" style="margin-bottom: 12px">
        <div class="search-box" style="flex: 1; min-width: 220px">
          <van-icon name="search" />
          <input
            v-model.trim="keyword"
            placeholder="搜索标题、正文或作者"
            @keyup.enter="handleSearch"
          />
          <van-icon
            v-if="keyword"
            name="clear"
            style="cursor: pointer"
            @click="handleReset"
          />
        </div>
        <van-button size="small" type="primary" icon="search" @click="handleSearch">
          搜索
        </van-button>
      </div>

      <div class="scroll-x" style="flex-wrap: wrap">
        <span class="chip" :class="{ active: activeCategory === 0 }" @click="changeCategory(0)">
          全部
        </span>
        <span
          v-for="item in categories"
          :key="item.id"
          class="chip"
          :class="{ active: activeCategory === item.id }"
          @click="changeCategory(item.id)"
        >
          {{ item.name }}
          <span style="opacity: 0.7">{{ item.news_count }}</span>
        </span>
      </div>
    </div>

    <div v-if="loading" class="news-list">
      <div v-for="i in 4" :key="i" class="news-card" style="cursor: default">
        <div class="news-thumb skeleton"></div>
        <div class="news-body">
          <div class="skeleton" style="height: 18px; width: 70%; margin-bottom: 10px"></div>
          <div class="skeleton" style="height: 12px; width: 90%; margin-bottom: 8px"></div>
          <div class="skeleton" style="height: 12px; width: 50%"></div>
        </div>
      </div>
    </div>

    <div v-else-if="newsList.length" class="news-list">
      <NewsCard v-for="item in newsList" :key="item.id" :news="item" />
    </div>

    <div v-else class="card">
      <EmptyState text="没有找到匹配的新闻，试试其他关键词或分类">
        <van-button size="small" style="margin-top: 12px" @click="handleReset">重置筛选</van-button>
      </EmptyState>
    </div>

    <div v-if="total > pageSize" class="pagination-row">
      <van-pagination
        v-model="page"
        :total-items="total"
        :items-per-page="pageSize"
        :show-page-size="5"
        force-ellipses
        @change="loadNews"
      />
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import NewsCard from '@/components/NewsCard.vue'
import EmptyState from '@/components/EmptyState.vue'
import { getCategoriesApi, getNewsPageApi } from '@/api/news'
import { useUserStore } from '@/store/user'
import { formatNumber } from '@/utils/format'

const userStore = useUserStore()

const categories = ref([])
const activeCategory = ref(0)
const keyword = ref('')
const page = ref(1)
const pageSize = 8
const total = ref(0)
const newsList = ref([])
const loading = ref(false)


async function loadCategories() {
  try {
    const res = await getCategoriesApi()
    categories.value = res.data || []
  } catch {
    categories.value = []
  }
}

async function loadNews() {
  loading.value = true
  try {
    const res = await getNewsPageApi({
      page: page.value,
      page_size: pageSize,
      category_id: activeCategory.value || undefined,
      keywords: keyword.value || undefined
    })
    newsList.value = res.data?.list || []
    total.value = res.data?.total || 0
  } catch {
    newsList.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

function changeCategory(id) {
  if (activeCategory.value === id) return
  activeCategory.value = id
  page.value = 1
  loadNews()
}

function handleSearch() {
  page.value = 1
  loadNews()
}

function handleReset() {
  keyword.value = ''
  activeCategory.value = 0
  page.value = 1
  loadNews()
}

onMounted(async () => {
  await Promise.all([loadCategories(), loadNews()])
})
</script>
