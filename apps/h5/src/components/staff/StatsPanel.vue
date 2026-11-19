<script setup lang="ts">
import type { StatsData } from '@/api/generated'
import { computed } from 'vue'
import { cardOnly } from '@/platform/release-mode'
import { deltaValue, weekdayLabel } from '@/utils/format'
// 今日数据来自 stats(range=today)，近7天柱状来自 stats(range=7d)。
// 「较昨日」增量 = today 指标 − yesterday 指标（Asia/Shanghai 日历边界由后端给出）。
// 仅当 today 与 yesterday 两段数据都存在时才显示增量，缺失不编造；0/负数如实显示。
const props = defineProps<{ today: StatsData, week: StatsData }>()
const cur = computed(() => props.today.today ?? { visitors: props.today.visitors, chats: props.today.chats, leads: props.today.leads })
const prev = computed(() => props.today.yesterday)
const visitorsDelta = computed(() => prev.value ? deltaValue(cur.value.visitors ?? 0, prev.value.visitors ?? 0) : null)
const chatsDelta = computed(() => prev.value ? deltaValue(cur.value.chats ?? 0, prev.value.chats ?? 0) : null)
const maxVisits = computed(() => Math.max(1, ...props.week.daily.map(d => d.visits)))
</script>

<template>
  <section class="stats-block">
    <div class="sec-title"><span>今日数据</span><small>较昨日</small></div>
    <div class="panel">
      <div class="stats" :class="{ 'stats-card-only': cardOnly }">
        <div class="stat"><b class="num">{{ cur.visitors ?? 0 }}</b><span>访客<em v-if="visitorsDelta" :class="`d-${visitorsDelta.dir}`">{{ visitorsDelta.text }}</em></span></div>
        <div v-if="!cardOnly" class="stat"><b class="num">{{ cur.chats ?? 0 }}</b><span>对话<em v-if="chatsDelta" :class="`d-${chatsDelta.dir}`">{{ chatsDelta.text }}</em></span></div>
        <div class="stat"><b class="num" :class="{ amber: (cur.leads ?? 0) > 0 }">{{ cur.leads ?? 0 }}</b><span>新线索</span></div>
      </div>
      <div class="chart-wrap">
        <div class="panel-h"><span class="hint">近 7 天访客</span><span class="hint num">共 {{ week.visitors }}</span></div>
        <div v-if="week.daily.length" class="bars" aria-label="近七天访客柱状图">
          <div v-for="(day, index) in week.daily" :key="day.date" class="bar-col">
            <i :class="{ hi: index === week.daily.length - 1 }" :style="{ height: `${Math.max(4, day.visits / maxVisits * 56)}px` }" />
            <span>{{ weekdayLabel(day.date, index === week.daily.length - 1) }}</span>
          </div>
        </div>
        <p v-else class="hint empty-bars">还没有访问数据</p>
      </div>
    </div>
  </section>
</template>

<style scoped>
.sec-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 0 10px;
  font-size: var(--fs-md);
  font-weight: 600;
  color: var(--c-ink);
}
.sec-title small {
  font-size: var(--fs-sm);
  font-weight: 400;
  color: var(--c-text-3);
}
.panel {
  background: var(--c-surface);
  border-radius: var(--r-lg);
  padding: 0 0 14px;
}
.stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
}
.stats-card-only {
  grid-template-columns: repeat(2, 1fr);
}
.stat {
  padding: 14px 0;
  text-align: center;
  position: relative;
}
.stat + .stat::before {
  content: "";
  position: absolute;
  left: 0;
  top: 18px;
  bottom: 18px;
  width: 1px;
  background: var(--c-line);
}
.stat b {
  display: block;
  font-size: var(--fs-xl);
  line-height: 1.2;
  color: var(--c-ink);
  font-weight: 700;
}
.stat b.amber {
  color: var(--c-amber);
}
.stat span {
  font-size: var(--fs-xs);
  color: var(--c-text-3);
}
.stat em {
  font-style: normal;
  font-size: 11px;
  margin-left: 2px;
}
.stat em.d-up {
  color: var(--c-success);
}
.stat em.d-down {
  color: var(--c-danger);
}
.stat em.d-flat {
  color: var(--c-text-3);
}
.chart-wrap {
  padding: 0 16px;
}
.panel-h {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin: 4px 0 0;
}
.hint {
  font-size: var(--fs-xs);
  color: var(--c-text-3);
}
.bars {
  display: flex;
  align-items: flex-end;
  gap: 10px;
  height: 72px;
  margin-top: 8px;
}
.bar-col {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  height: 100%;
  justify-content: flex-end;
}
.bar-col i {
  display: block;
  width: 100%;
  max-width: 22px;
  border-radius: 5px 5px 2px 2px;
  background: var(--c-primary-line);
}
.bar-col i.hi {
  background: var(--c-primary);
}
.bar-col span {
  font-size: 10px;
  color: var(--c-text-3);
}
.empty-bars {
  margin-top: 8px;
}
</style>
