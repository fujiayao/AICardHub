<script setup lang="ts">
import type { StatsData } from '@/api/generated'
defineProps<{ stats: StatsData }>()
</script>

<template><section class="panel stack"><h2>近 7 天数据</h2><div class="metrics"><div class="metric"><strong class="num">{{ stats.visitors }}</strong><p>访客</p></div><div class="metric"><strong class="num">{{ stats.chats }}</strong><p>对话</p></div><div class="metric"><strong class="num lead">{{ stats.leads }}</strong><p>线索</p></div></div><p class="muted small summary">访问 {{ stats.visits }} 次 · 转化率 {{ (stats.conversion_rate * 100).toFixed(1) }}%</p><div v-if="stats.daily.length" class="chart" aria-label="近七天访问统计"><div v-for="day in stats.daily" :key="day.date" class="day"><span class="small num count">{{ day.visits }}</span><div class="bar" :style="{ height: `${Math.max(4, day.visits / Math.max(1, ...stats.daily.map(d => d.visits)) * 72)}px` }" /><span class="small date">{{ day.date.slice(5) }}</span></div></div><p v-else class="empty-inline">还没有访问数据</p></section></template>
<style scoped>
.metrics{display:grid;grid-template-columns:repeat(3,1fr);gap:var(--sp-2)}
.metric{text-align:center;padding:var(--sp-3) 0;background:var(--c-bg);border-radius:var(--r-md)}
.metric strong{display:block;font-size:var(--fs-xl);color:var(--c-ink);line-height:1.1}
.metric .lead{color:var(--c-primary)}
.metric p{font-size:var(--fs-xs);color:var(--c-text-2);margin-top:4px}
.summary{margin-top:var(--sp-3)}
.chart{display:flex;align-items:flex-end;gap:var(--sp-2);height:120px;margin-top:var(--sp-3);padding-top:var(--sp-2)}
.day{flex:1;text-align:center;display:grid;justify-items:center;gap:4px;align-content:end}
.count{color:var(--c-text-2)}
.date{color:var(--c-text-3)}
.bar{width:100%;max-width:22px;background:var(--c-primary);border-radius:var(--r-sm) var(--r-sm) 0 0}
</style>
