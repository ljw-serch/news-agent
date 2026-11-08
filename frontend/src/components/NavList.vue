<template>
  <nav class="nav-list">
    <div v-for="group in groups" :key="group.label" class="nav-group">
      <div class="nav-label">{{ group.label }}</div>
      <div
        v-for="item in group.items"
        :key="item.path"
        class="nav-item"
        :class="{ active: isActive(item.path) }"
        @click="$emit('select', item.path)"
      >
        <van-icon :name="item.icon" />
        <span>{{ item.label }}</span>
        <span v-if="item.badge" class="nav-badge">{{ item.badge }}</span>
      </div>
    </div>
  </nav>
</template>

<script setup>
import { useRoute } from 'vue-router'

defineProps({
  groups: {
    type: Array,
    default: () => []
  }
})

defineEmits(['select'])

const route = useRoute()

function isActive(path) {
  const current = route.path
  if (path === '/manager/home') return current === path
  return current === path || current.startsWith(`${path}/`)
}
</script>
