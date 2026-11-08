<template>
  <div class="stat-card">
    <div class="stat-icon" :style="iconStyle">
      <van-icon :name="icon" />
    </div>
    <div class="stat-value">{{ value }}</div>
    <div class="stat-label">{{ label }}</div>
    <div v-if="hint" class="stat-hint">{{ hint }}</div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  label: { type: String, default: '' },
  value: { type: [String, Number], default: 0 },
  icon: { type: String, default: 'chart-trending-o' },
  hint: { type: String, default: '' },
  color: { type: String, default: '' }
})

const iconStyle = computed(() =>
  props.color
    ? {
        color: props.color,
        background: `${props.color}1f`
      }
    : {}
)
</script>
