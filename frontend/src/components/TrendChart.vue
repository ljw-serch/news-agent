<template>
  <div>
    <div v-if="total === 0" class="trend-empty">
      <van-icon name="calendar-o" />
      <div class="trend-empty-title">当前区间暂无新发布的新闻</div>
      <div class="trend-empty-sub">{{ rangeText }}</div>
      <div v-if="latest" class="trend-empty-sub">数据库最新发布：{{ latest }}</div>
    </div>

    <template v-else>
      <div class="trend-bars">
        <div v-for="point in points" :key="point.date" class="trend-col" :title="tooltip(point)">
          <div
            class="trend-bar"
            :class="{ zero: !point.news_count }"
            :style="{ height: `${heightOf(point.news_count)}%` }"
          ></div>
          <div class="trend-label">{{ shortDate(point.date) }}</div>
        </div>
      </div>
      <div class="row-between" style="margin-top: 10px">
        <div class="trend-legend">
          <span><i></i>每日新发布</span>
          <span>合计 {{ formatNumber(total) }} 条</span>
        </div>
        <span class="tag muted">{{ rangeText }}</span>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { formatNumber } from '@/utils/format'

const props = defineProps({
  points: { type: Array, default: () => [] },
  latest: { type: String, default: '' }
})

const max = computed(() => Math.max(1, ...props.points.map((item) => item.news_count || 0)))
const total = computed(() =>
  props.points.reduce((sum, item) => sum + (item.news_count || 0), 0)
)
const rangeText = computed(() => {
  if (!props.points.length) return ''
  return `${props.points[0].date} ~ ${props.points[props.points.length - 1].date}`
})

function heightOf(value) {
  if (!value) return 0
  return Math.max(6, Math.round((value / max.value) * 100))
}

function shortDate(value) {
  return String(value || '').slice(5)
}

function tooltip(point) {
  return `${point.date}：新增 ${point.news_count} 条，阅读 ${point.view_count} 次`
}
</script>

<style scoped>
.trend-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 150px;
  padding: 22px 10px;
  border: 1px dashed var(--border);
  border-radius: 12px;
  color: var(--sub);
  text-align: center;
}

.trend-empty .van-icon {
  font-size: 30px;
  opacity: 0.5;
  margin-bottom: 8px;
}

.trend-empty-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text);
}

.trend-empty-sub {
  font-size: 11px;
  margin-top: 4px;
}
</style>
