<script setup lang="ts">
import { shallowRef, onMounted, useTemplateRef } from "vue";
import { api } from "@/api/adapters";
import type { Stats } from "@/api/schema";
import { useTask } from "@/composables/useTask";
import LoadState from "@/components/LoadState.vue";
import PageHeader from "@/components/shared/PageHeader.vue";
import AppIcon from "@/components/shared/AppIcon.vue";
import KpiCards from "./KpiCards.vue";
import TrendChart from "./TrendChart.vue";
import LeadPipeline from "./LeadPipeline.vue";
import Shortcuts from "./Shortcuts.vue";
import LeadsTable from "./LeadsTable.vue";
const stats = shallowRef<Stats>();
const { busy, error, run } = useTask();
const pipeline = useTemplateRef<InstanceType<typeof LeadPipeline>>("pipeline");
async function load() {
  await run(async () => {
    stats.value = await api.stats();
  });
}
function refreshAll() {
  void load();
  void pipeline.value?.load();
}
onMounted(load);
</script>
<template>
  <section class="page">
    <PageHeader
      title="工作台"
      desc="近 7 天访问、对话与获客概况；优先处理超时未跟进线索。"
    >
      <el-button :loading="busy" @click="refreshAll"
        ><AppIcon name="refresh" class="btn-ico" />刷新数据</el-button
      >
    </PageHeader>
    <el-alert
      v-if="stats && stats.overdue_leads > 0"
      type="error"
      :closable="false"
      show-icon
      :title="`有 ${stats.overdue_leads} 条新线索超过 24 小时未跟进`"
      description="请在下方全部线索中筛选“新线索”并尽快分配跟进。"
    />
    <LoadState :busy="busy && !stats" :error="error" @retry="load" />
    <KpiCards v-if="stats && !error" :stats="stats" />
    <div class="grid">
      <TrendChart v-if="stats && !error" :daily="stats.daily" class="trend" />
      <LeadPipeline ref="pipeline" />
    </div>
    <div class="grid">
      <section class="panel source" aria-labelledby="source-title">
        <div class="panel-head"><h2 id="source-title">访问来源分布</h2></div>
        <div class="pending-state">
          <strong>统计接口暂未提供来源维度</strong>
          <span
            >当前统计契约只包含总量与每日趋势，不含二维码 / 链接 /
            海报等来源拆分。后端发布来源统计字段后再展示，本页不生成示例数据。</span
          >
        </div>
      </section>
      <Shortcuts />
    </div>
    <LeadsTable />
  </section>
</template>
<style scoped>
.grid {
  display: grid;
  grid-template-columns: minmax(0, 2fr) minmax(0, 1fr);
  gap: var(--ac-space-4);
}
.btn-ico {
  width: 16px;
  height: 16px;
  margin-right: 6px;
}
@media (max-width: 1100px) {
  .grid {
    grid-template-columns: 1fr;
  }
}
</style>
