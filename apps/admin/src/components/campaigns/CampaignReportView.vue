<script setup lang="ts">
import { computed } from "vue";
import type { CampaignReport } from "@/api/schema";
import { sourceName } from "./campaignMeta";

const props = defineProps<{ report: CampaignReport }>();
// Server totals; visitors are de-duplicated across sources (union) and must
// never be recomputed from source_breakdown.
const kpis = computed(() => [
  { key: "visits", label: "访问次数", value: props.report.visits },
  { key: "visitors", label: "访客数", value: props.report.visitors },
  { key: "chats", label: "有效对话", value: props.report.chats },
  { key: "leads", label: "线索", value: props.report.leads },
]);
</script>
<template>
  <div>
    <ul class="kpis" aria-label="活动核心指标">
      <li v-for="k in kpis" :key="k.key" class="kpi">
        <span class="kpi-label">{{ k.label }}</span>
        <strong class="kpi-value">{{ k.value.toLocaleString("zh-CN") }}</strong>
      </li>
    </ul>
    <h2 class="section-title">来源拆分</h2>
    <el-empty
      v-if="!report.source_breakdown.length"
      description="该活动暂无来源数据"
      :image-size="80"
    />
    <div
      v-else
      class="table-wrap"
      role="region"
      aria-label="来源拆分表"
      tabindex="0"
    >
      <el-table :data="report.source_breakdown" row-key="source">
        <el-table-column label="来源" min-width="130">
          <template #default="{ row }">{{ sourceName(row) }}</template>
        </el-table-column>
        <el-table-column label="访问次数" min-width="100" align="right">
          <template #default="{ row }">{{ row.visits ?? 0 }}</template>
        </el-table-column>
        <el-table-column label="访客数" min-width="90" align="right">
          <template #default="{ row }">{{ row.visitors ?? 0 }}</template>
        </el-table-column>
        <el-table-column label="有效对话" min-width="100" align="right">
          <template #default="{ row }">{{ row.chats ?? 0 }}</template>
        </el-table-column>
        <el-table-column label="线索" min-width="80" align="right">
          <template #default="{ row }">{{ row.leads ?? 0 }}</template>
        </el-table-column>
      </el-table>
    </div>
    <p class="note">
      同一访客可能经多个来源进入，各来源访客数之和可能大于总访客数。
    </p>
  </div>
</template>
<style scoped>
.kpis {
  list-style: none;
  padding: 0;
  margin: 0 0 var(--ac-space-4);
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: var(--ac-space-3);
}
.kpi {
  background: var(--ac-surface-muted);
  border: 1px solid var(--ac-border);
  border-left: 3px solid var(--ac-teal);
  border-radius: var(--ac-radius);
  padding: var(--ac-space-3) var(--ac-space-4);
  display: flex;
  flex-direction: column;
  gap: var(--ac-space-1);
}
.kpi-label {
  color: var(--ac-text-muted);
  font-size: 13px;
}
.kpi-value {
  color: var(--ac-navy);
  font-size: 26px;
  font-variant-numeric: tabular-nums;
}
.section-title {
  font-size: 15px;
  margin: 0 0 var(--ac-space-2);
  color: var(--ac-text);
}
.table-wrap {
  overflow-x: auto;
  max-width: 100%;
}
.table-wrap:focus-visible {
  outline: 2px solid var(--ac-focus);
  outline-offset: 2px;
}
.note {
  margin: var(--ac-space-2) 0 0;
  font-size: 12px;
  color: var(--ac-text-subtle);
}
</style>
