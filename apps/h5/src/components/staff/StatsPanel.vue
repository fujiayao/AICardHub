<script setup lang="ts">
import type { StatsData } from '@/api/generated'
defineProps<{ stats: StatsData }>()

</script>

<template><section class="panel stack"><h2>近 7 天数据</h2><div class="metrics"><div><strong class="num">{{ stats.visitors }}</strong><p>访客</p></div><div><strong class="num">{{ stats.chats }}</strong><p>对话</p></div><div><strong class="num amber">{{ stats.leads }}</strong><p>线索</p></div></div><p class="muted small">访问 {{ stats.visits }} 次 · 转化率 {{ (stats.conversion_rate * 100).toFixed(1) }}%</p><div v-if="stats.daily.length" class="chart" aria-label="近七天访问统计"><div v-for="day in stats.daily" :key="day.date" class="day"><span class="small num">{{ day.visits }}</span><div class="bar" :style="{ height: `${Math.max(3, day.visits / Math.max(1, ...stats.daily.map(d => d.visits)) * 80)}px` }" /><span class="small">{{ day.date.slice(5) }}</span></div></div><p v-else class="muted">还没有访问数据</p></section></template>
<style scoped>.metrics{display:grid;grid-template-columns:repeat(3,1fr);text-align:center}.metrics strong{font-size:var(--fs-xl);color:var(--c-ink)}.metrics .amber{color:var(--c-amber)}.metrics p{font-size:var(--fs-xs);color:var(--c-text-2)}.chart{display:flex;align-items:flex-end;gap:10px;height:130px}.day{flex:1;text-align:center;display:grid;justify-items:center;gap:4px}.bar{width:20px;background:var(--c-primary);border-radius:var(--r-sm)}</style>
