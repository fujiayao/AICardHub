<script setup lang="ts">
import { computed, onMounted, ref, shallowRef } from "vue";
import { useRouter } from "vue-router";
import { ElMessage, ElMessageBox } from "element-plus";
import { api } from "@/api/adapters";
import { ApiError } from "@/api/client";
import type { Campaign, CampaignInput, CampaignStatus } from "@/api/schema";
import { confirmAction } from "@/composables/useTask";
import { usePage } from "@/composables/usePage";
import LoadState from "@/components/LoadState.vue";
import PageHeader from "@/components/shared/PageHeader.vue";
import CampaignTable from "./CampaignTable.vue";
import CampaignForm from "./CampaignForm.vue";
import CampaignDetail from "./CampaignDetail.vue";
import { statusFilters, statusOf, toCampaignInput } from "./campaignMeta";

const PAGE_SIZE = 20;
const router = useRouter();
const status = ref<CampaignStatus | "">("");
const { busy, error, data, page, load } = usePage<Campaign>((p) =>
  api.campaigns({
    page: p,
    page_size: PAGE_SIZE,
    ...(status.value ? { status: status.value } : {}),
  }),
);

type Mode = "create" | "edit" | "view";
const mode = ref<Mode | null>(null);
const current = ref<Campaign | null>(null);
const draft = ref<CampaignInput | null>(null);
const saving = shallowRef(false);
const saveError = shallowRef("");
const formKey = shallowRef(0);
// Detail is always re-read from the server so views/edits never use a stale list row.
const item = {
  id: shallowRef<number | null>(null),
  busy: shallowRef(false),
  error: shallowRef(""),
};
let itemSeq = 0;
const dialogTitle = computed(() =>
  mode.value === "create"
    ? "新建活动"
    : mode.value === "edit"
      ? "编辑活动"
      : "活动详情",
);

function openCreate() {
  itemSeq++;
  item.busy.value = false;
  item.id.value = null;
  item.error.value = "";
  current.value = null;
  saveError.value = "";
  draft.value = toCampaignInput(null);
  mode.value = "create";
  formKey.value++;
}
async function fetchItem() {
  const id = item.id.value;
  if (id === null) return;
  const seq = ++itemSeq;
  item.busy.value = true;
  item.error.value = "";
  current.value = null;
  draft.value = null;
  try {
    const row = await api.campaign(id);
    if (seq !== itemSeq) return;
    current.value = row;
    if (mode.value === "edit") {
      draft.value = toCampaignInput(row);
      formKey.value++;
    }
  } catch (e) {
    if (seq === itemSeq)
      item.error.value =
        e instanceof Error ? e.message : "活动加载失败，请重试";
  } finally {
    if (seq === itemSeq) item.busy.value = false;
  }
}
function openItem(row: Campaign, next: "edit" | "view") {
  saveError.value = "";
  item.id.value = row.id;
  mode.value = next;
  void fetchItem();
}
function switchToEdit() {
  if (!current.value) return;
  saveError.value = "";
  draft.value = toCampaignInput(current.value);
  mode.value = "edit";
  formKey.value++;
}
function closeDialog() {
  if (saving.value) return;
  itemSeq++;
  item.busy.value = false;
  item.id.value = null;
  mode.value = null;
  draft.value = null;
  current.value = null;
  saveError.value = "";
}
function onFilter() {
  void load(1);
}
function openReport(row: Campaign) {
  void router.push({ name: "reports", query: { campaign_id: String(row.id) } });
}

async function save(body: CampaignInput) {
  if (saving.value) return;
  const id = mode.value === "edit" ? (current.value?.id ?? null) : null;
  if (mode.value === "edit" && id === null) return;
  saving.value = true;
  saveError.value = "";
  try {
    await api.saveCampaign(id, body);
  } catch (e) {
    // Form stays mounted with the user's input; error is shown inline.
    saveError.value = e instanceof Error ? e.message : "保存未完成，请重试";
    saving.value = false;
    return;
  }
  ElMessage.success(id ? "活动已更新" : "活动已创建");
  saving.value = false;
  closeDialog();
  await load(id ? page.value : 1);
}

async function remove(row: Campaign) {
  if (statusOf(row) !== "draft") return;
  if (!(await confirmAction(`删除草稿活动“${row.name}”？删除后不可恢复。`)))
    return;
  saving.value = true;
  try {
    await api.deleteCampaign(row.id);
  } catch (e) {
    saving.value = false;
    if (e instanceof ApiError && e.status === 409)
      await ElMessageBox.alert(
        `${e.message}。仅未被访问或留资引用的草稿活动可删除，已使用的活动请改为“已结束”。`,
        "无法删除活动",
        { type: "warning", confirmButtonText: "知道了" },
      ).catch(() => undefined);
    // Other errors were already surfaced by request() via ElMessage.
    return;
  }
  saving.value = false;
  ElMessage.success("活动已删除");
  const lastOnPage = data.value.items.length === 1 && page.value > 1;
  await load(lastOnPage ? page.value - 1 : page.value);
}

onMounted(() => void load(1));
</script>
<template>
  <section class="page">
    <PageHeader
      title="活动管理"
      desc="展会、沙龙等线下活动的获客配置。已启用且处于有效期内的活动才会对访客生效。"
    >
      <el-button type="primary" @click="openCreate">新建活动</el-button>
    </PageHeader>
    <div class="panel">
      <div class="toolbar">
        <el-radio-group
          v-model="status"
          aria-label="按状态筛选活动"
          :disabled="busy"
          @change="onFilter"
        >
          <el-radio-button
            v-for="f in statusFilters"
            :key="f.value"
            :value="f.value"
            >{{ f.label }}</el-radio-button
          >
        </el-radio-group>
        <el-button :loading="busy" aria-label="刷新活动列表" @click="load()"
          >刷新</el-button
        >
      </div>
      <LoadState
        :busy="busy && !data.items.length"
        :error="error"
        @retry="load()"
      />
      <CampaignTable
        v-if="!error || data.items.length"
        v-loading="busy && data.items.length > 0"
        :rows="data.items"
        :busy="busy || saving"
        @view="(row: Campaign) => openItem(row, 'view')"
        @edit="(row: Campaign) => openItem(row, 'edit')"
        @remove="remove"
        @report="openReport"
      />
      <div v-if="data.total > PAGE_SIZE" class="pager">
        <el-pagination
          layout="total, prev, pager, next"
          :total="data.total"
          :page-size="PAGE_SIZE"
          :current-page="page"
          :disabled="busy"
          size="small"
          background
          @current-change="(p: number) => load(p)"
        />
      </div>
    </div>
    <el-dialog
      :model-value="mode !== null"
      :title="dialogTitle"
      width="min(720px, 100vw)"
      :close-on-click-modal="false"
      @update:model-value="(v: boolean) => !v && closeDialog()"
    >
      <LoadState
        v-if="mode !== 'create'"
        :busy="item.busy.value"
        :error="item.error.value"
        @retry="fetchItem"
      />
      <el-alert
        v-if="saveError"
        :title="saveError"
        type="error"
        show-icon
        :closable="false"
        class="save-error"
      />
      <CampaignForm
        v-if="mode !== 'view' && draft"
        :key="formKey"
        :initial="draft"
        :busy="saving"
        :saved-status="mode === 'edit' && current ? statusOf(current) : null"
        @save="save"
        @cancel="closeDialog"
      />
      <CampaignDetail
        v-else-if="mode === 'view' && current"
        :campaign="current"
        @edit="switchToEdit"
        @report="current && openReport(current)"
      />
    </el-dialog>
  </section>
</template>
<style scoped>
.toolbar {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: var(--ac-space-2);
  margin-bottom: var(--ac-space-3);
}
.save-error {
  margin-bottom: var(--ac-space-3);
}
.pager {
  display: flex;
  justify-content: flex-end;
  margin-top: var(--ac-space-3);
  overflow-x: auto;
}
</style>
