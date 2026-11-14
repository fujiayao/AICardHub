<script setup lang="ts">
// Grouped bar chart (inline SVG) with an accessible data table alternative.
import { computed, shallowRef } from "vue";
import type { Stats } from "@/api/schema";
const props = defineProps<{ daily: Stats["daily"] }>();
const showTable = shallowRef(false);
const series = [
  { key: "visits", label: "访问", cls: "s-visits" },
  { key: "chats", label: "对话", cls: "s-chats" },
  { key: "leads", label: "线索", cls: "s-leads" },
] as const;
const W = 640;
const H = 200;
const PAD = 28;
const max = computed(() =>
  Math.max(0, ...props.daily.flatMap((d) => [d.visits, d.chats, d.leads])),
);
const empty = computed(() => max.value === 0);
const bars = computed(() => {
  const n = props.daily.length || 1;
  const slot = (W - PAD * 2) / n;
  const bw = Math.min(14, (slot - 12) / 3);
  const scale = max.value ? (H - PAD * 2) / max.value : 0;
  return props.daily.map((d, i) => ({
    date: d.date.slice(5),
    x: PAD + slot * i + (slot - bw * 3) / 2,
    rects: series.map((s, j) => {
      const h = d[s.key] * scale;
      return { cls: s.cls, x: j * bw, y: H - PAD - h, h, w: bw - 2 };
    }),
    cx: PAD + slot * i + slot / 2,
  }));
});
</script>
<template>
  <section class="panel" aria-labelledby="trend-title">
    <div class="panel-head">
      <div>
        <h2 id="trend-title">近 7 天趋势</h2>
        <p class="muted sub">按 UTC 日期统计访问、对话与线索</p>
      </div>
      <el-button size="small" @click="showTable = !showTable">{{
        showTable ? "查看图表" : "查看数据表"
      }}</el-button>
    </div>
    <ul class="legend" aria-hidden="true">
      <li v-for="s in series" :key="s.key">
        <i :class="s.cls" />{{ s.label }}
      </li>
    </ul>
    <div v-if="!showTable" class="chart">
      <p v-if="empty" class="empty">该时间段内还没有访问、对话或线索记录。</p>
      <svg
        v-else
        :viewBox="`0 0 ${W} ${H}`"
        role="img"
        aria-label="近 7 天访问、对话、线索柱状图，详细数值见数据表"
      >
        <line
          :x1="PAD"
          :x2="W - PAD"
          :y1="H - PAD"
          :y2="H - PAD"
          class="axis"
        />
        <text :x="PAD - 6" :y="PAD + 4" class="tick" text-anchor="end">
          {{ max }}
        </text>
        <g v-for="b in bars" :key="b.date" :transform="`translate(${b.x},0)`">
          <rect
            v-for="r in b.rects"
            :key="r.cls"
            :class="r.cls"
            :x="r.x"
            :y="r.y"
            :width="r.w"
            :height="r.h"
            rx="2"
          />
        </g>
        <text
          v-for="b in bars"
          :key="`t${b.date}`"
          :x="b.cx"
          :y="H - 8"
          class="tick"
          text-anchor="middle"
        >
          {{ b.date }}
        </text>
      </svg>
    </div>
    <div v-else class="table-wrap">
      <el-table :data="daily" size="small" empty-text="当前没有统计数据">
        <el-table-column prop="date" label="日期" min-width="110" />
        <el-table-column prop="visits" label="访问" />
        <el-table-column prop="chats" label="对话" />
        <el-table-column prop="leads" label="线索" />
      </el-table>
    </div>
  </section>
</template>
<style scoped>
.sub {
  margin: 2px 0 0;
  font-size: 12px;
}
.legend {
  display: flex;
  gap: var(--ac-space-4);
  margin: 0 0 var(--ac-space-2);
  padding: 0;
  list-style: none;
  font-size: 12px;
  color: var(--ac-text-muted);
}
.legend i {
  display: inline-block;
  width: 10px;
  height: 10px;
  margin-right: 6px;
  border-radius: 2px;
}
.chart svg {
  width: 100%;
  height: auto;
  display: block;
}
.axis {
  stroke: var(--ac-border-strong);
}
.tick {
  font-size: 11px;
  fill: var(--ac-text-subtle);
}
.s-visits {
  fill: var(--ac-primary);
  background: var(--ac-primary);
}
.s-chats {
  fill: var(--ac-teal);
  background: var(--ac-teal);
}
.s-leads {
  fill: var(--ac-navy-3);
  background: var(--ac-navy-3);
}
.empty {
  margin: 0;
  padding: var(--ac-space-6) var(--ac-space-4);
  text-align: center;
  color: var(--ac-text-muted);
  background: var(--ac-surface-muted);
  border-radius: var(--ac-radius-sm);
}
</style>
