<script setup lang="ts">
// Pipeline counts come from admin_lead_list totals per status filter (real data).
import { onMounted, shallowRef } from "vue";
import { api } from "@/api/adapters";
import { useTask } from "@/composables/useTask";
import LoadState from "@/components/LoadState.vue";
const stages = [
  { status: "new", label: "新线索" },
  { status: "contacted", label: "已联系" },
  { status: "converted", label: "已转化" },
  { status: "invalid", label: "无效" },
] as const;
const counts = shallowRef<Record<string, number>>({});
const { busy, error, run } = useTask();
async function load() {
  await run(async () => {
    const totals = await Promise.all(
      stages.map((s) => api.leads({ page: 1, page_size: 1, status: s.status })),
    );
    counts.value = Object.fromEntries(
      stages.map((s, i) => [s.status, totals[i].total]),
    );
  });
}
defineExpose({ load });
onMounted(load);
</script>
<template>
  <section class="panel" aria-labelledby="pipeline-title">
    <div class="panel-head">
      <div>
        <h2 id="pipeline-title">线索漏斗</h2>
        <p class="muted sub">全部线索按跟进状态分布</p>
      </div>
    </div>
    <LoadState :busy="busy" :error="error" @retry="load" />
    <ol v-if="!busy && !error" class="stages">
      <li v-for="s in stages" :key="s.status" :class="['stage', s.status]">
        <span class="name">{{ s.label }}</span>
        <strong>{{ counts[s.status] ?? "—" }}</strong>
      </li>
    </ol>
  </section>
</template>
<style scoped>
.sub {
  margin: 2px 0 0;
  font-size: 12px;
}
.stages {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: var(--ac-space-2);
}
.stage {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--ac-space-3) var(--ac-space-4);
  border-radius: var(--ac-radius-sm);
  background: var(--ac-surface-muted);
  border-left: 3px solid var(--ac-border-strong);
}
.stage.new {
  border-left-color: var(--ac-primary);
}
.stage.contacted {
  border-left-color: var(--ac-teal);
}
.stage.converted {
  border-left-color: var(--ac-success);
}
.name {
  font-size: 14px;
  color: var(--ac-text-muted);
}
strong {
  font-size: 18px;
  font-variant-numeric: tabular-nums;
}
</style>
