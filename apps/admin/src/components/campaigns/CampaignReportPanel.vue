<script setup lang="ts">
import { computed, onMounted, ref, shallowRef, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { api } from "@/api/adapters";
import type { Campaign, CampaignReport } from "@/api/schema";
import { useTask } from "@/composables/useTask";
import LoadState from "@/components/LoadState.vue";
import PageHeader from "@/components/shared/PageHeader.vue";
import { formatTime, sourceLabels, statusLabels } from "./campaignMeta";

const route = useRoute();
const router = useRouter();
const list = useTask();
const campaigns = ref<Campaign[]>([]);
const selected = shallowRef<number | null>(null);
const report = ref<CampaignReport | null>(null);
let requestSeq = 0;

const current = computed(
  () => campaigns.value.find((c) => c.id === selected.value) ?? null,
);
const kpis = computed(() => {
  const r = report.value;
  if (!r) return [];
  // Totals come straight from the server; visitors are de-duplicated across
  // sources, so they must never be recomputed from source_breakdown.
  return [
    { key: "visits", label: "访问次数", value: r.visits },
    { key: "visitors", label: "访客数", value: r.visitors },
    { key: "chats", label: "有效对话", value: r.chats },
    { key: "leads", label: "线索", value: r.leads },
  ];
});

function queryId(): number | null {
  const raw = route.query.campaign_id;
  const value = Array.isArray(raw) ? raw[0] : raw;
  const id = Number(value);
  return value && Number.isInteger(id) && id > 0 ? id : null;
}

async function loadCampaigns() {
  await list.run(async () => {
    const page = await api.campaigns({ page: 1, page_size: 100 });
    campaigns.value = page.items;
  });
  const wanted = queryId();
  if (wanted !== null) selected.value = wanted;
  else if (!selected.value && campaigns.value.length)
    selected.value = campaigns.value[0].id;
}

// Own loader (not useTask) so switching campaigns mid-request is never dropped;
// stale responses are discarded by sequence number.
const rep = { busy: shallowRef(false), error: shallowRef("") };
async function loadReport() {
  const id = selected.value;
  const seq = ++requestSeq;
  report.value = null;
  rep.error.value = "";
  if (id === null) {
    rep.busy.value = false;
    return;
  }
  rep.busy.value = true;
  try {
    const data = await api.campaignReport(id);
    if (seq === requestSeq) report.value = data;
  } catch (e) {
    if (seq === requestSeq)
      rep.error.value = e instanceof Error ? e.message : "报表加载失败，请重试";
  } finally {
    if (seq === requestSeq) rep.busy.value = false;
  }
}
type SourceRow = CampaignReport["source_breakdown"][number];
const sourceName = (row: SourceRow) => sourceLabels[row.source] ?? row.source;

watch(selected, (id) => {
  if (id !== queryId())
    void router.replace({
      query: { ...route.query, campaign_id: id === null ? undefined : String(id) },
    });
  void loadReport();
});
watch(
  () => route.query.campaign_id,
  () => {
    const id = queryId();
    if (id !== null && id !== selected.value) selected.value = id;
  },
);

onMounted(loadCampaigns);
</script>
<template>
  <section class="page">
    <PageHeader
      title="活动报表"
      desc="按活动汇总访问、访客、有效对话与线索。总数由服务端去重统计，不等于各来源简单相加。"
    />
    <div class="panel">
      <div class="toolbar">
        <label class="picker-label" for="campaign-picker">选择活动</label>
        <el-select
          id="campaign-picker"
          v-model="selected"
          placeholder="请选择活动"
          filterable
          aria-label="选择活动"
          :loading="list.busy.value"
          class="picker"
        >
          <el-option
            v-for="c in campaigns"
            :key="c.id"
            :value="c.id"
            :label="`${c.name}（${statusLabels[c.status]}）`"
          />
        </el-select>
        <el-button
          :loading="rep.busy.value"
          :disabled="selected === null"
          aria-label="刷新报表"
          @click="loadReport"
          >刷新</el-button
        >
      </div>
      <LoadState
        :busy="list.busy.value"
        :error="list.error.value"
        @retry="loadCampaigns"
      />
      <el-empty
        v-if="!list.busy.value && !list.error.value && !campaigns.length"
        description="还没有活动，请先在「活动管理」中创建"
      >
        <el-button type="primary" @click="router.push({ name: 'activities' })"
          >前往活动管理</el-button
        >
      </el-empty>
      <template v-else-if="selected !== null">
        <p v-if="current" class="meta">
          {{ formatTime(current.start_at) }} 至 {{ formatTime(current.end_at) }}
          <el-tag v-if="current.is_live" size="small" type="success">当前生效</el-tag>
          <el-tag v-else size="small" type="info">未在有效期</el-tag>
        </p>
        <LoadState
          :busy="rep.busy.value"
          :error="rep.error.value"
          @retry="loadReport"
        />
        <template v-if="report && !rep.error.value">
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
              <el-table-column prop="visits" label="访问次数" min-width="100" align="right" />
              <el-table-column prop="visitors" label="访客数" min-width="90" align="right" />
              <el-table-column prop="chats" label="有效对话" min-width="100" align="right" />
              <el-table-column prop="leads" label="线索" min-width="80" align="right" />
            </el-table>
          </div>
          <p class="note">
            同一访客可能经多个来源进入，各来源访客数之和可能大于总访客数。
          </p>
        </template>
      </template>
    </div>
  </section>
</template>
<style scoped>
.toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--ac-space-2);
  margin-bottom: var(--ac-space-3);
}
.picker-label {
  font-size: 13px;
  color: var(--ac-text-muted);
}
.picker {
  width: min(360px, 100%);
}
.meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--ac-space-2);
  color: var(--ac-text-muted);
  font-size: 13px;
  margin: 0 0 var(--ac-space-3);
}
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
