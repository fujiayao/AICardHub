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
import { statusFilters } from "./campaignMeta";

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
const formKey = shallowRef(0);
const dialogTitle = computed(() =>
  mode.value === "create" ? "新建活动" : mode.value === "edit" ? "编辑活动" : "活动详情",
);

function blank(): CampaignInput {
  return {
    name: "",
    status: "draft",
    start_at: "",
    end_at: "",
    booth: "",
    location: "",
    opening_override: "",
    guide_override: [],
  };
}
function toInput(row: Campaign): CampaignInput {
  return {
    name: row.name,
    status: row.status,
    start_at: row.start_at,
    end_at: row.end_at,
    booth: row.booth,
    location: row.location,
    opening_override: row.opening_override,
    guide_override: [...row.guide_override],
  };
}
function openCreate() {
  current.value = null;
  draft.value = blank();
  mode.value = "create";
  formKey.value++;
}
function openEdit(row: Campaign) {
  current.value = row;
  draft.value = toInput(row);
  mode.value = "edit";
  formKey.value++;
}
function openView(row: Campaign) {
  current.value = row;
  draft.value = null;
  mode.value = "view";
}
function closeDialog() {
  if (saving.value) return;
  mode.value = null;
  draft.value = null;
  current.value = null;
}
function onFilter() {
  void load(1);
}
function openReport(row: Campaign) {
  void router.push({ name: "reports", query: { campaign_id: String(row.id) } });
}

async function save(body: CampaignInput) {
  if (saving.value) return;
  saving.value = true;
  try {
    const id = mode.value === "edit" && current.value ? current.value.id : null;
    await api.saveCampaign(id, body);
    ElMessage.success(id ? "活动已更新" : "活动已创建");
    saving.value = false;
    closeDialog();
    await load(id ? page.value : 1);
  } catch {
    // request() already surfaced the server message via ElMessage
  } finally {
    saving.value = false;
  }
}

async function remove(row: Campaign) {
  if (!(await confirmAction(`删除活动“${row.name}”？删除后不可恢复。`))) return;
  saving.value = true;
  try {
    await api.deleteCampaign(row.id);
    ElMessage.success("活动已删除");
    saving.value = false;
    const lastOnPage = data.value.items.length === 1 && page.value > 1;
    await load(lastOnPage ? page.value - 1 : page.value);
  } catch (e) {
    if (e instanceof ApiError && e.status === 409) {
      await ElMessageBox.alert(
        e.message || "仅未被使用的草稿活动可删除",
        "无法删除活动",
        { type: "warning", confirmButtonText: "知道了" },
      ).catch(() => undefined);
    }
  } finally {
    saving.value = false;
  }
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
      <LoadState :busy="busy && !data.items.length" :error="error" @retry="load()" />
      <CampaignTable
        v-if="!error || data.items.length"
        v-loading="busy && data.items.length > 0"
        :rows="data.items"
        :busy="busy || saving"
        @view="openView"
        @edit="openEdit"
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
      <CampaignForm
        v-if="mode !== 'view' && draft"
        :key="formKey"
        :initial="draft"
        :busy="saving"
        :saved-status="mode === 'edit' && current ? current.status : null"
        @save="save"
        @cancel="closeDialog"
      />
      <CampaignDetail
        v-else-if="mode === 'view' && current"
        :campaign="current"
        @edit="current && openEdit(current)"
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
.pager {
  display: flex;
  justify-content: flex-end;
  margin-top: var(--ac-space-3);
  overflow-x: auto;
}
</style>
