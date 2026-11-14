<script setup lang="ts">
import { computed } from 'vue'
// 无照片身份徽章：姓名首字，深蓝底白字圆角方形；不使用人像剪影。
const props = defineProps<{ name?: string | null, size?: number, tone?: 'ink' | 'light' }>()
const initials = computed(() => {
  const name = (props.name || '').trim()
  if (!name) return ''
  if (/^\p{Script=Han}/u.test(name)) return name.slice(0, 1)
  return name.split(/\s+/).map(word => word[0] ?? '').join('').slice(0, 2).toUpperCase()
})
const box = computed(() => `${props.size || 56}px`)
const font = computed(() => `${Math.round((props.size || 56) * 0.42)}px`)
</script>
<template>
 <span class="mark" :class="tone || 'ink'" :style="{ width: box, height: box, fontSize: font }" aria-hidden="true">
  <span v-if="initials">{{ initials }}</span>
  <span v-else class="icon i-lucide-id-card" />
 </span>
</template>
<style scoped>
.mark{display:inline-grid;place-items:center;flex-shrink:0;border-radius:28%;font-weight:600;letter-spacing:.02em;line-height:1}
.ink{background:var(--c-ink-2);color:var(--c-surface);box-shadow:inset 0 0 0 1px var(--c-on-ink-line)}
.light{background:var(--c-primary-soft);color:var(--c-ink)}
.mark .icon{width:45%;height:45%}
</style>
