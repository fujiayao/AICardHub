<script setup lang="ts">
import { computed, onMounted, ref, shallowRef, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { api } from "@/api/adapters";
import type { Campaign, CampaignReport } from "@/api/schema";
import { useTask } from "@/composables/useTask";
import LoadState from "@/components/LoadState.vue";
import PageHeader from "@/components/shared/PageHeader.vue";
import { formatTime, statusLabels, statusOf } from "./campaignMeta";
import CampaignReportView from "./CampaignReportView.vue";

const PAGE_SIZE = 100;
const route = useRoute();
const router = useRouter();
const list = useTask();
const campaigns = ref<Campaign[]>([]);
const total = shallowRef(0);
const loadedPage = shallowRef(0);
/** URL-selected campaign that is not on any loaded page; fetched by id. */
const pinned = ref<Campaign | null>(null);
const pinnedError = shallowRef("");
const selected = shallowRef<number | null>(null);
const report = ref<CampaignReport | null>(null);
let requestSeq = 0;
let pinSeq = 0;

const options = computed(() =>
  pinned.value && !campaigns.value.some((c) => c.id === pinned.value?.id)
    ? [pinned.value, ...campaigns.value]
    : campaigns.value,
);
const hasMore = computed(() => campaigns.value.length < total.value);
const current = computed(
  () => options.value.find((c) => c.id === selected.value) ?? null,
);
const optionLabel = (c: Campaign) =>
  `${c.name}（${statusLabels[statusOf(c)]}）`;

function queryId(): number | null {
  const raw = route.query.campaign_id;
  const value = Array.isArray(raw) ? raw[0] : raw;
  const id = Number(value);
  return value && Number.isInteger(id) && id > 0 ? id : null;
}

async function loadPage(next: number) {
  await list.run(async () => {
    const page = await api.campaigns({ page: next, page_size: PAGE_SIZE });
    const known = new Set(campaigns.value.map((c) => c.id));
    campaigns.value =
      next === 1
        ? page.items
        : [...campaigns.value, ...page.items.filter((c) => !known.has(c.id))];
    total.value = page.total;
    loadedPage.value = next;
  });
}
async function loadCampaigns() {
  await loadPage(1);
  if (list.error.value) return;
  const wanted = queryId();
  if (wanted !== null) selected.value = wanted;
  else if (selected.value === null && campaigns.value.length)
    selected.value = campaigns.value[0].id;
  void ensurePinned();
}
function loadMore() {
  if (hasMore.value && !list.busy.value) void loadPage(loadedPage.value + 1);
}

async function ensurePinned() {
  const id = selected.value;
  if (id === null || campaigns.value.some((c) => c.id === id)) return;
  if (pinned.value?.id === id) return;
  const seq = ++pinSeq;
  pinnedError.value = "";
  try {
    const row = await api.campaign(id);
    if (seq === pinSeq) pinned.value = row;
  } catch (e) {
    if (seq === pinSeq)
      pinnedError.value = e instanceof Error ? e.message : "活动信息加载失败";
  }
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

watch(selected, (id) => {
  if (id !== queryId())
    void router.replace({
      query: {
        ...route.query,
        campaign_id: id === null ? undefined : String(id),
      },
    });
  void ensurePinned();
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
            v-for="c in options"
            :key="c.id"
            :value="c.id"
            :label="optionLabel(c)"
          />
        </el-select>
        <el-button v-if="hasMore" :loading="list.busy.value" @click="loadMore"
          >加载更多活动（已加载 {{ campaigns.length }} /
          {{ total }}）</el-button
        >
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
        v-if="
          !list.busy.value &&
          !list.error.value &&
          !options.length &&
          selected === null
        "
        description="还没有活动，请先在「活动管理」中创建"
      >
        <el-button type="primary" @click="router.push({ name: 'activities' })"
          >前往活动管理</el-button
        >
      </el-empty>
      <template v-else-if="selected !== null">
        <p v-if="pinnedError && !current" class="meta">
          活动信息加载失败：{{ pinnedError }}（报表仍按活动 ID
          {{ selected }} 加载）
        </p>
        <p v-if="current" class="meta">
          {{ formatTime(current.start_at) }} 至 {{ formatTime(current.end_at) }}
          <el-tag v-if="current.is_live" size="small" type="success"
            >当前生效</el-tag
          >
          <el-tag v-else size="small" type="info">未在有效期</el-tag>
        </p>
        <LoadState
          :busy="rep.busy.value"
          :error="rep.error.value"
          @retry="loadReport"
        />
        <CampaignReportView
          v-if="report && !rep.error.value"
          :report="report"
        />
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
</style>
