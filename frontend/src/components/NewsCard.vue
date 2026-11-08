<template>
  <div class="news-card" @click="goDetail">
    <img
      v-if="news.image && !imageError"
      class="news-thumb"
      :src="news.image"
      :alt="news.title"
      loading="lazy"
      @error="imageError = true"
    />
    <div v-else class="news-thumb news-thumb-fallback">
      <span>{{ categoryInitial }}</span>
    </div>

    <div class="news-body">
      <div class="news-title">{{ news.title }}</div>
      <div v-if="news.highlight" class="news-highlight">
        <van-icon name="bulb-o" />
        <span>{{ news.highlight }}</span>
      </div>
      <div v-else class="news-desc">{{ news.description || '' }}</div>
      <div class="news-meta">
        <span v-if="news.category_name" class="tag">{{ news.category_name }}</span>
        <span v-if="news.summary" class="tag success">AI 摘要</span>
        <span>{{ news.author || '平台编辑' }}</span>
        <span class="dot"></span>
        <span>{{ formatDate(news.publish_time, false) }}</span>
        <span class="dot"></span>
        <span><van-icon name="eye-o" /> {{ formatNumber(news.views) }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { formatDate, formatNumber } from '@/utils/format'

const props = defineProps({
  news: {
    type: Object,
    required: true
  }
})

const router = useRouter()
const imageError = ref(false)

const categoryInitial = computed(() => (props.news.category_name || '新').slice(0, 1))

watch(
  () => props.news.image,
  () => {
    imageError.value = false
  }
)

function goDetail() {
  router.push(`/manager/news/${props.news.id}`)
}
</script>

<style scoped>
.news-thumb-fallback {
  display: grid;
  place-items: center;
  color: var(--primary);
  font-size: 30px;
  font-weight: 800;
  background: linear-gradient(135deg, var(--primary-soft), var(--bg));
}

.news-highlight {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  font-size: 12.5px;
  color: var(--primary);
  background: var(--primary-soft);
  border-radius: 8px;
  padding: 6px 9px;
  margin-bottom: 8px;
  line-height: 1.55;
}

.news-highlight .van-icon {
  margin-top: 2px;
  flex-shrink: 0;
}
</style>
