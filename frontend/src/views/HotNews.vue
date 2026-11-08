<template>
  <div>
    <div class="page-head">
      <div>
        <div class="page-title">新闻热榜</div>
        <div class="page-sub">
          热度 = 阅读量 × 0.6 + 收藏数 × 40 + 时效加成 · 共 {{ hotList.length }} 条上榜
        </div>
      </div>
      <div class="page-actions">
        <van-button size="small" icon="replay" :loading="loading" @click="loadHot">刷新榜单</van-button>
        <van-button
          size="small"
          type="primary"
          icon="bulb-o"
          :loading="analysisLoading"
          @click="analyze"
        >
          AI 热榜解读
        </van-button>
      </div>
    </div>

    <div class="card" style="margin-bottom: 16px; padding: 14px 16px">
      <div class="toolbar" style="margin-bottom: 0">
        <span
          v-for="item in ranges"
          :key="item.value"
          class="chip"
          :class="{ active: days === item.value }"
          @click="changeDays(item.value)"
        >
          {{ item.label }}
        </span>
        <span class="muted" style="font-size: 11px; margin-left: auto">
          数据缓存 5 分钟 · 新闻变更后自动失效
        </span>
      </div>
    </div>

    <div class="grid-main">
      <div class="card">
        <div class="card-head">
          <div class="card-title">
            <van-icon name="fire-o" />
            {{
              days === 0 ? '全部时间' : `近 ${days} 天`
            }}热榜 TOP {{ hotList.length || 10 }}
          </div>
          <span class="tag warn">实时热度</span>
        </div>

        <div v-if="loading" class="empty-box">
          <van-loading size="22" />
          <div style="margin-top: 10px">正在计算热度…</div>
        </div>

        <div v-else-if="hotList.length">
          <div
            v-for="item in hotList"
            :key="item.id"
            class="rank-item hot-row"
            @click="$router.push(`/manager/news/${item.id}`)"
          >
            <div class="rank-no" :class="`top${item.rank}`">{{ item.rank }}</div>
            <div class="rank-body">
              <div class="rank-title">{{ item.title }}</div>
              <div class="rank-meta">
                <span class="tag">{{ item.category_name || '未分类' }}</span>
                <span><van-icon name="eye-o" /> {{ formatNumber(item.views) }}</span>
                <span><van-icon name="star-o" /> {{ formatNumber(item.favorite_count) }}</span>
                <span>{{ formatDate(item.publish_time, false) }}</span>
                <span>热度 {{ item.score }}</span>
              </div>
              <div class="score-bar">
                <span :style="{ width: `${barWidth(item.score)}%` }"></span>
              </div>
            </div>
          </div>
        </div>

        <EmptyState v-else text="当前时间窗口没有新闻，试试切换到「全部时间」" icon="fire-o" />
      </div>

      <div class="stack">
        <div class="card">
          <div class="card-head">
            <div class="card-title">
              <van-icon name="bulb-o" />
              AI 热榜解读
            </div>
            <span class="tag" :class="analysis ? 'success' : 'muted'">
              {{ analysis ? '已生成' : '待生成' }}
            </span>
          </div>
          <div v-if="analysisLoading" class="empty-box" style="padding: 30px 8px">
            <van-loading size="20" />
            <div style="margin-top: 8px">正在分析热榜话题…</div>
          </div>
          <div v-else-if="analysis" class="markdown" v-html="renderMarkdown(analysis)"></div>
          <template v-else>
            <div class="muted" style="font-size: 12px; line-height: 1.75">
              让 AI 对当前热榜做话题聚类、趋势判断与阅读建议，帮你理解「为什么上榜」。
            </div>
            <van-button
              size="small"
              type="primary"
              style="margin-top: 12px"
              icon="bulb-o"
              :loading="analysisLoading"
              @click="analyze"
            >
              生成热榜解读
            </van-button>
          </template>
        </div>

        <div class="card">
          <div class="card-head">
            <div class="card-title">
              <van-icon name="info-o" />
              热度规则
            </div>
          </div>
          <div class="rule-list">
            <div><b>阅读量</b><span>基础热度，权重 0.6</span></div>
            <div><b>收藏数</b><span>强互动信号，每条 +40</span></div>
            <div><b>发布时间</b><span>30 天内按天数递减加成</span></div>
            <div><b>时间窗口</b><span>窗口内新闻额外 +20</span></div>
          </div>
          <div class="muted" style="font-size: 11px; margin-top: 10px; line-height: 1.6">
            热榜与统计结果都来自数据库实时计算，Redis 只做短时缓存。
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import EmptyState from '@/components/EmptyState.vue'
import { getHotNewsApi } from '@/api/news'
import { getHotAnalysisApi } from '@/api/ai'
import { formatDate, formatNumber, renderMarkdown } from '@/utils/format'

const ranges = [
  { label: '全部时间', value: 0 },
  { label: '近 7 天', value: 7 },
  { label: '近 30 天', value: 30 },
  { label: '近一年', value: 365 }
]

const days = ref(0)
const hotList = ref([])
const loading = ref(false)
const analysis = ref('')
const analysisLoading = ref(false)

const maxScore = computed(() => Math.max(1, ...hotList.value.map((item) => item.score || 0)))

function barWidth(score) {
  return Math.max(4, Math.round(((score || 0) / maxScore.value) * 100))
}

async function loadHot() {
  loading.value = true
  try {
    const res = await getHotNewsApi({ days: days.value, limit: 10 })
    hotList.value = res.data?.list || []
  } catch {
    hotList.value = []
  } finally {
    loading.value = false
  }
}

async function changeDays(value) {
  if (days.value === value) return
  days.value = value
  analysis.value = ''
  await loadHot()
}

async function analyze() {
  analysisLoading.value = true
  try {
    const res = await getHotAnalysisApi({ days: days.value, limit: 10 })
    analysis.value = res.data?.content || '暂无分析内容'
  } catch {
    analysis.value = ''
  } finally {
    analysisLoading.value = false
  }
}

onMounted(loadHot)
</script>

<style scoped>
.hot-row {
  padding: 14px 0;
}

.rule-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.rule-list > div {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  font-size: 11.5px;
}

.rule-list b {
  font-weight: 600;
}

.rule-list span {
  color: var(--sub);
  text-align: right;
}
</style>
