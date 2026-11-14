<script setup lang="ts">
import { computed } from "vue";
import type { Stats } from "@/api/schema";
const props = defineProps<{ stats: Stats }>();
type Tone = "primary" | "teal" | "neutral" | "danger";
const cards = computed(() => {
  const s = props.stats;
  const rate = `${(s.conversion_rate * 100).toFixed(1)}%`;
  return [
    {
      label: "访问量",
      value: s.visits,
      hint: "近 7 天名片访问次数",
      tone: "primary" as Tone,
    },
    {
      label: "独立访客",
      value: s.visitors,
      hint: "近 7 天去重访客",
      tone: "primary" as Tone,
    },
    {
      label: "AI 对话",
      value: s.chats,
      hint: "近 7 天会话数，不含测试",
      tone: "teal" as Tone,
    },
    {
      label: "新增线索",
      value: s.leads,
      hint: "近 7 天留资",
      tone: "primary" as Tone,
    },
    {
      label: "留资转化率",
      value: rate,
      hint: "近 7 天线索 ÷ 独立访客",
      tone: "teal" as Tone,
    },
    {
      label: "员工",
      value: s.employees,
      hint: "当前员工总数",
      tone: "neutral" as Tone,
    },
    {
      label: "名片",
      value: s.cards,
      hint: "当前名片总数",
      tone: "neutral" as Tone,
    },
    {
      label: "超时未跟进",
      value: s.overdue_leads,
      hint: "状态为新线索且超过 24 小时",
      tone: (s.overdue_leads > 0 ? "danger" : "neutral") as Tone,
    },
  ];
});
</script>
<template>
  <ul class="kpis" aria-label="核心指标">
    <li v-for="c in cards" :key="c.label" :class="['kpi', c.tone]">
      <span class="label">{{ c.label }}</span>
      <strong class="value">{{ c.value }}</strong>
      <span class="hint">{{ c.hint }}</span>
    </li>
  </ul>
</template>
<style scoped>
.kpis {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: var(--ac-space-3);
}
.kpi {
  display: grid;
  gap: var(--ac-space-1);
  padding: var(--ac-space-4);
  background: var(--ac-surface);
  border: 1px solid var(--ac-border);
  border-top: 3px solid var(--ac-border-strong);
  border-radius: var(--ac-radius);
  box-shadow: var(--ac-shadow);
  min-width: 0;
}
.kpi.primary {
  border-top-color: var(--ac-primary);
}
.kpi.teal {
  border-top-color: var(--ac-teal);
}
.kpi.danger {
  border-top-color: var(--ac-danger);
  background: var(--ac-danger-soft);
}
.label {
  font-size: 13px;
  color: var(--ac-text-muted);
}
.value {
  font-size: 28px;
  line-height: 1.2;
  font-weight: 650;
  font-variant-numeric: tabular-nums;
}
.danger .value {
  color: var(--ac-danger);
}
.hint {
  font-size: 12px;
  color: var(--ac-text-subtle);
}
@media (max-width: 1100px) {
  .kpis {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
@media (max-width: 760px) {
  .kpi {
    padding: var(--ac-space-3);
  }
  .value {
    font-size: 22px;
  }
}
</style>
