<script setup lang="ts">
import { shallowRef, onMounted } from "vue";
import { api } from "@/api/adapters";
import type { Stats } from "@/api/schema";
import { useTask } from "@/composables/useTask";
import LoadState from "@/components/LoadState.vue";
import ReCol from "@/components/ReCol";
import LeadsTable from "./LeadsTable.vue";
const stats = shallowRef<Stats>();
const { busy, error, run } = useTask();
const metrics = [
  ["visits", "访问量"],
  ["visitors", "访客数"],
  ["chats", "对话数"],
  ["leads", "线索数"],
  ["employees", "员工数"],
  ["cards", "名片数"],
  ["overdue_leads", "超时未跟进"],
] as const;
async function load() {
  await run(async () => {
    stats.value = await api.stats();
  });
}
onMounted(load);
</script>
<template>
  <section class="page">
    <div>
      <h1>工作台</h1>
      <p class="muted">查看访问、对话与获客情况，优先处理未跟进线索。</p>
    </div>
    <div class="panel">
      <div class="toolbar">
        <h2>全局数据</h2>
        <el-button :loading="busy" @click="load">刷新数据</el-button>
      </div>
      <LoadState :busy="busy" :error="error" @retry="load" /><template
        v-if="stats && !error"
        ><el-row :gutter="16"
          ><ReCol v-for="[key, label] in metrics" :key="key" :value="6" :xs="12"
            ><div
              :class="[
                'metric',
                key === 'overdue_leads' && stats[key] > 0 ? 'danger-text' : '',
              ]"
            >
              {{ label }}<strong>{{ stats[key] ?? "—" }}</strong>
            </div></ReCol
          ><ReCol :value="6" :xs="12"
            ><div class="metric">
              转化率<strong
                >{{ (stats.conversion_rate * 100).toFixed(1) }}%</strong
              >
            </div></ReCol
          ></el-row
        >
        <h2 class="daily-title">每日趋势</h2>
        <el-table :data="stats.daily" empty-text="当前没有统计数据"
          ><el-table-column prop="date" label="日期" /><el-table-column
            prop="visits"
            label="访问" /><el-table-column
            prop="chats"
            label="对话" /><el-table-column
            prop="leads"
            label="线索" /></el-table
      ></template>
    </div>
    <LeadsTable /><el-alert
      title="本地契约仅提供核心统计与每日趋势。来源分布、员工排行、热门/未命中问题待后续统计接口；本页不生成示例统计。"
      type="info"
      :closable="false"
    />
  </section>
</template>
<style scoped>
.daily-title {
  margin-top: 24px;
}
</style>
