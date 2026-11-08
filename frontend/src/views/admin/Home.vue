<template>
  <div>
    <div class="page-head">
      <div>
        <div class="page-title">{{ greeting }}，{{ userStore.displayName }}</div>
        <div class="page-sub">
          欢迎使用 AI 新闻资讯平台 · 当前身份：{{ userStore.roleLabel }} · {{ todayText }}
        </div>
      </div>
      <div class="page-actions">
        <van-button size="small" icon="replay" :loading="loading" @click="loadAll">
          刷新数据
        </van-button>
      </div>
    </div>

    <div class="stat-grid" style="margin-bottom: 16px">
      <StatCard
        v-for="item in statCards"
        :key="item.label"
        :label="item.label"
        :value="item.value"
        :icon="item.icon"
        :hint="item.hint"
        :color="item.color"
      />
    </div>

    <div class="grid-main">
      <div class="stack">
        <div class="card">
          <div class="card-head">
            <div class="card-title">
              <van-icon name="bar-chart-o" />
              新闻发布趋势
            </div>
            <div class="scroll-x">
              <span
                v-for="day in [7, 14, 30]"
                :key="day"
                class="chip"
                :class="{ active: trendDays === day }"
                @click="changeTrend(day)"
              >
                近 {{ day }} 天
              </span>
            </div>
          </div>
          <TrendChart v-if="trendPoints.length" :points="trendPoints" :latest="overview.latest_publish_time" />
          <div v-else class="empty-box" style="padding: 32px 10px">
            <van-icon name="bar-chart-o" />
            <div>暂无趋势数据</div>
          </div>
        </div>

        <div class="card">
          <div class="card-head">
            <div class="card-title">
              <van-icon name="notes-o" />
              最新发布
            </div>
            <span class="card-link" @click="$router.push('/manager/news')">查看全部 →</span>
          </div>
          <div v-if="latestNews.length" class="news-list">
            <NewsCard v-for="item in latestNews" :key="item.id" :news="item" />
          </div>
          <EmptyState v-else text="还没有新闻，管理员可在新闻管理中新增" />
        </div>
      </div>

      <div class="stack">
        <div class="card">
          <div class="card-head">
            <div class="card-title">
              <van-icon name="fire-o" />
              实时热榜
            </div>
            <span class="card-link" @click="$router.push('/manager/hot')">完整榜单 →</span>
          </div>
          <div v-if="hotNews.length">
            <div
              v-for="item in hotNews"
              :key="item.id"
              class="rank-item"
              @click="$router.push(`/manager/news/${item.id}`)"
            >
              <div class="rank-no" :class="`top${item.rank}`">{{ item.rank }}</div>
              <div class="rank-body">
                <div class="rank-title">{{ item.title }}</div>
                <div class="rank-meta">
                  <span>{{ item.category_name || '未分类' }}</span>
                  <span><van-icon name="eye-o" /> {{ formatNumber(item.views) }}</span>
                  <span>{{ formatDate(item.publish_time, false) }}</span>
                </div>
              </div>
            </div>
          </div>
          <EmptyState v-else text="暂无热榜数据" icon="fire-o" />
        </div>


        <div class="card">
          <div class="card-head">
            <div class="card-title">
              <van-icon name="info-o" />
              数据说明
            </div>
          </div>
          <div class="data-meta">
            <div><span>最新发布</span><b>{{ overview.latest_publish_time || '—' }}</b></div>
            <div><span>数据起始</span><b>{{ overview.coverage_start || '—' }}</b></div>
            <div><span>已生成摘要</span><b>{{ formatNumber(overview.total_summaries) }} 条</b></div>
            <div><span>统计口径</span><b>按发布时间实时统计</b></div>
          </div>
          <div class="muted" style="font-size: 11px; margin-top: 10px; line-height: 1.6">
            若「今日新增」为 0，说明数据库当日确实没有新发布新闻，可通过管理员「新增新闻」补充。
          </div>
        </div>
      </div>
    </div>

  
  </div>
</template>
<!-- <style scoped>
 .stat-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
}
.stat-grid > * {
  height: 100%;
} 
 </style> -->

<script setup>
import { computed, onMounted, ref } from 'vue'
import StatCard from '@/components/StatCard.vue'
import TrendChart from '@/components/TrendChart.vue'
import NewsCard from '@/components/NewsCard.vue'
import EmptyState from '@/components/EmptyState.vue'
import { useUserStore } from '@/store/user'
import { getOverviewApi, getTrendApi } from '@/api/stats'
import { getHotNewsApi, getNewsPageApi } from '@/api/news'
import { getAIStatusApi } from '@/api/ai'
import { formatDate, formatNumber, renderMarkdown } from '@/utils/format'

const userStore = useUserStore()

const loading = ref(false)
const overview = ref({})
const trendPoints = ref([])
const trendDays = ref(7)
const hotNews = ref([])
const latestNews = ref([])
const aiStatus = ref({ enabled: false, mode: 'local' })


const todayText = new Date().toLocaleDateString('zh-CN', {
  year: 'numeric',
  month: 'long',
  day: 'numeric',
  weekday: 'long'
})

const greeting = computed(() => {
  const hour = new Date().getHours()
  if (hour < 6) return '夜深了'
  if (hour < 12) return '早上好'
  if (hour < 14) return '中午好'
  if (hour < 18) return '下午好'
  return '晚上好'
})

const statCards = computed(() => {
  const data = overview.value || {}
  const cards = [
    {
      label: '新闻总量',
      value: formatNumber(data.total_news),
      icon: 'notes-o',
      hint: `覆盖 ${data.total_categories || 0} 个分类`
    },
    {
      label: '今日新发布',
      value: formatNumber(data.today_news),
      icon: 'add-o',
      hint: '按发布时间统计',
      color: '#10b981'
    },
    {
      label: '近 7 天新增',
      value: formatNumber(data.week_news),
      icon: 'clock-o',
      hint: `近 30 天 ${formatNumber(data.month_news)} 条`,
      color: '#f59e0b'
    },
    {
      label: '累计阅读',
      value: formatNumber(data.total_views),
      icon: 'eye-o',
      hint: `今日新增阅读 ${formatNumber(data.today_views)}`,
      color: '#8b5cf6'
    },
    {
      label: '注册用户',
      value: formatNumber(data.total_users),
      icon: 'friends-o',
      hint: `正常 ${formatNumber(data.active_users)} 人`,
        color: '#0ea5e9'
      },
      {
        label: '累计收藏',
        value: formatNumber(data.total_favorites),
        icon: 'star-o',
        hint: `AI 摘要 ${formatNumber(data.total_summaries)} 条`,
        color: '#ec4899'
      },
    
  
      {
        label: '累计收藏',
        value: formatNumber(data.total_favorites),
        icon: 'star-o',
        hint: '全站用户收藏总量',
        color: '#ec4899'
      },
      {
        label: 'AI 摘要',
        value: formatNumber(data.total_summaries),
        icon: 'bulb-o',
        hint: '已生成摘要的新闻数',
        color: '#14b8a6'
      }

]
  return cards
})

async function loadAll() {
  loading.value = true
  const [overviewRes, trendRes, hotRes, newsRes, statusRes] = await Promise.allSettled([
    getOverviewApi(),
    getTrendApi(trendDays.value),
    getHotNewsApi({ days: 0, limit: 8 }),
    getNewsPageApi({ page: 1, page_size: 5 }),
    getAIStatusApi()
  ])

  if (overviewRes.status === 'fulfilled') overview.value = overviewRes.value.data || {}
  if (trendRes.status === 'fulfilled') trendPoints.value = trendRes.value.data?.points || []
  if (hotRes.status === 'fulfilled') hotNews.value = hotRes.value.data?.list || []
  if (newsRes.status === 'fulfilled') latestNews.value = newsRes.value.data?.list || []
  if (statusRes.status === 'fulfilled') aiStatus.value = statusRes.value.data || aiStatus.value

  loading.value = false
}

async function changeTrend(days) {
  trendDays.value = days
  try {
    const res = await getTrendApi(days)
    trendPoints.value = res.data?.points || []
  } catch {
    // 错误提示已由请求拦截器处理
  }
}


onMounted(loadAll)
</script>

<style scoped>
.quick-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.quick-item {
  display: flex;
  flex-direction: column;
  gap: 3px;
  padding: 11px 12px;
  border-radius: 10px;
  background: var(--bg);
  border: 1px solid var(--border);
  cursor: pointer;
  transition: 0.18s;
}

.quick-item:hover {
  border-color: var(--primary);
  background: var(--primary-soft);
}

.quick-item .van-icon {
  color: var(--primary);
  font-size: 17px;
}

.quick-item span {
  font-size: 12.5px;
  font-weight: 600;
}

.quick-item small {
  font-size: 10.5px;
  color: var(--sub);
}

.data-meta {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.data-meta > div {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  font-size: 11.5px;
}

.data-meta span {
  color: var(--sub);
}

.data-meta b {
  font-weight: 600;
  text-align: right;
}

.popup-card {
  background: var(--card);
  padding: 22px;
  max-height: 86vh;
  overflow-y: auto;
}

:deep(.stat-grid) {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
}
:deep(.stat-grid) > * {
  height: 100%;
}


</style>
