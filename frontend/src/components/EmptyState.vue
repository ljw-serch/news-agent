<template>
  <div class="empty-box">
    <van-icon :name="icon" />
    <div>{{ text }}</div>
    <slot />
  </div>
</template>

<script setup>
defineProps({
  text: { type: String, default: '暂无数据' },
  icon: { type: String, default: 'notes-o' }
})
</script>
