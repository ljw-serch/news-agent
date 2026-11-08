<template>
  <div>
    <div class="page-head">
      <div>
        <div class="page-title">我的收藏</div>
        <div class="page-sub">共 {{ formatNumber(total) }} 条收藏 · 收藏内容会从数据库实时读取</div>
      </div>
      <div class="page-actions">
        <van-button size="small" icon="delete-o" :disabled="!total" @click="clearAll">
          清空收藏
        </van-button>
        <van-button size="small" type="primary" icon="notes-o" @click="$router.push('/manager/news')">
          去逛逛
        </van-button>
      </div>
    </div>

    <div v-if="loading" class="card">
      <div class="skeleton" style="height: 80px; margin-bottom: 12px"></div>
      <div class="skeleton" style="height: 80px"></div>
    </div>

    <div v-else-if="favorites.length" class="card" style="padding: 6px 16px">
      <div v-for="item in favorites" :key="item.favorite_id" class="saved-item">
        <div class="saved-main" @click="$router.push(`/manager/news/${item.news.id}`)">
          <img
            v-if="item.news.image"
            class="saved-thumb"
            :src="item.news.image"
            :alt="item.news.title"
            loading="lazy"
            @error="onImageError"
          />
          <div v-else class="saved-thumb saved-fallback">
            {{ (item.news.category_name || '新').slice(0, 1) }}
          </div>
          <div class="saved-body">
            <div class="saved-title">{{ item.news.title }}</div>
            <div class="saved-desc">{{ item.news.description }}</div>
            <div class="saved-meta">
              <span class="tag">{{ item.news.category_name || '未分类' }}</span>
              <span>收藏于 {{ formatDate(item.favorite_time) }}</span>
              <span><van-icon name="eye-o" /> {{ formatNumber(item.news.views) }}</span>
            </div>
          </div>
        </div>
        <van-button size="mini" type="danger" plain @click="removeOne(item)">取消收藏</van-button>
      </div>
    </div>

    <div v-else class="card">
      <EmptyState text="还没有收藏任何新闻，去新闻列表看看吧" icon="star-o">
        <van-button size="small" style="margin-top: 12px" @click="$router.push('/manager/news')">
          浏览新闻
        </van-button>
      </EmptyState>
    </div>

    <div v-if="total > pageSize" class="pagination-row">
      <van-pagination
        v-model="page"
        :total-items="total"
        :items-per-page="pageSize"
        :show-page-size="5"
        force-ellipses
        @change="loadFavorites"
      />
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { showConfirmDialog, showToast } from 'vant'
import EmptyState from '@/components/EmptyState.vue'
import { clearFavoritesApi, getFavoritePageApi, removeFavoriteApi } from '@/api/favorite'
import { formatDate, formatNumber } from '@/utils/format'

const favorites = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = 8
const loading = ref(false)

function onImageError(event) {
  if (event?.target) event.target.style.visibility = 'hidden'
}

async function loadFavorites() {
  loading.value = true
  try {
    const res = await getFavoritePageApi({ page: page.value, page_size: pageSize })
    favorites.value = res.data?.list || []
    total.value = res.data?.total || 0
  } catch {
    favorites.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

async function removeOne(item) {
  try {
    await removeFavoriteApi(item.news.id)
    showToast({ message: '已取消收藏', position: 'top' })
    await loadFavorites()
  } catch {
    // 拦截器已提示
  }
}

async function clearAll() {
  try {
    await showConfirmDialog({
      title: '清空收藏',
      message: '确认清空全部收藏记录？',
      confirmButtonText: '清空'
    })
  } catch {
    return
  }
  try {
    await clearFavoritesApi()
    showToast({ message: '收藏已清空', position: 'top' })
    page.value = 1
    await loadFavorites()
  } catch {
    // 拦截器已提示
  }
}

onMounted(loadFavorites)
</script>

<style scoped>
.saved-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 13px 0;
  border-bottom: 1px dashed var(--border);
}

.saved-item:last-child {
  border-bottom: none;
}

.saved-main {
  display: flex;
  gap: 12px;
  flex: 1;
  min-width: 0;
  cursor: pointer;
}

.saved-thumb {
  width: 92px;
  height: 66px;
  border-radius: 8px;
  object-fit: cover;
  flex-shrink: 0;
  background: var(--primary-soft);
}

.saved-fallback {
  display: grid;
  place-items: center;
  color: var(--primary);
  font-size: 24px;
  font-weight: 800;
}

.saved-body {
  min-width: 0;
  flex: 1;
}

.saved-title {
  font-size: 13.5px;
  font-weight: 700;
  line-height: 1.45;
  margin-bottom: 4px;
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.saved-main:hover .saved-title {
  color: var(--primary);
}

.saved-desc {
  font-size: 11.5px;
  color: var(--sub);
  line-height: 1.55;
  margin-bottom: 5px;
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.saved-meta {
  display: flex;
  gap: 9px;
  flex-wrap: wrap;
  font-size: 10.5px;
  color: var(--sub);
  align-items: center;
}

@media (max-width: 640px) {
  .saved-item {
    align-items: flex-start;
    flex-wrap: wrap;
  }

  .saved-thumb {
    width: 72px;
    height: 56px;
  }
}
</style>
