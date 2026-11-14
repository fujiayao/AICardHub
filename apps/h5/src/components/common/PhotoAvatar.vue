<script setup lang="ts">
defineProps<{ src?: string | null, name?: string, size?: number }>()
</script>
<template><span class="avatar" :style="{ width: `${size || 48}px`, height: `${size || 48}px` }"><img v-if="src" :src="src" :alt="`${name || ''}头像`"><span v-else aria-hidden="true">{{ name?.slice(0, 1) || '人' }}</span></span></template>
<style scoped>.avatar{display:inline-flex;align-items:center;justify-content:center;border-radius:var(--r-pill);background:var(--c-ink-2);color:var(--c-surface);overflow:hidden;flex-shrink:0;font-size:var(--fs-lg)}img{width:100%;height:100%;object-fit:cover}</style>
