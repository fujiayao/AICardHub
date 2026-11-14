<script setup lang="ts">
import { ref, shallowRef, onMounted } from "vue";
import { ElMessage } from "element-plus";
import { api } from "@/api/adapters";
import type { CompanyInput, CompanyOption } from "@/api/schema";
import FieldForm from "@/components/FieldForm.vue";
import LoadState from "@/components/LoadState.vue";
import { useTask } from "@/composables/useTask";
import { companyFields, emptyCompany } from "./companyFields";
const emit = defineEmits<{ changed: [] }>();
const list = useTask(),
  edit = useTask();
const rows = shallowRef<CompanyOption[]>([]);
const open = shallowRef(false),
  editingId = shallowRef<number | null>(null),
  editingPrimary = shallowRef(false);
const model = ref<CompanyInput>(emptyCompany());
async function load() {
  await list.run(async () => {
    rows.value = await api.companies();
  });
}
async function openEditor(row?: CompanyOption) {
  editingId.value = row?.id ?? null;
  editingPrimary.value = row?.is_primary ?? false;
  model.value = emptyCompany();
  open.value = true;
  if (!row) return;
  await edit.run(async () => {
    const item = await api.companyItem(row.id);
    model.value = {
      name: item.name,
      short_name: item.short_name,
      intro: item.intro,
      phone: item.phone,
      address: item.address,
      website: item.website,
      logo_url: item.logo_url,
      brand_color: item.brand_color,
    };
  });
}
function update(key: string, value: unknown) {
  model.value = { ...model.value, [key]: value };
}
async function save() {
  await edit.run(async () => {
    await api.saveCompanyItem(editingId.value, model.value);
    open.value = false;
    ElMessage.success(editingId.value ? "公司信息已保存" : "公司已创建");
    await load();
    emit("changed");
  });
}
onMounted(load);
</script>
<template>
  <section class="panel" aria-labelledby="company-list-title">
    <div class="toolbar">
      <h2 id="company-list-title">任职公司</h2>
      <el-button type="primary" @click="openEditor()">新增公司</el-button
      ><el-button :loading="list.busy.value" @click="load">刷新</el-button>
    </div>
    <p class="muted">
      员工可关联不同任职公司；名片展示所关联公司的信息。产品目录仅属于主公司，其他公司名片不展示主公司产品。公司不提供删除。
    </p>
    <LoadState
      :busy="list.busy.value"
      :error="list.error.value"
      @retry="load"
    />
    <div class="table-wrap">
      <el-table
        :data="rows"
        row-key="id"
        border
        empty-text="暂无公司数据"
        aria-label="任职公司列表"
      >
        <el-table-column label="公司名称" prop="name" min-width="180" />
        <el-table-column label="简称" min-width="120">
          <template #default="{ row }">{{ row.short_name || "—" }}</template>
        </el-table-column>
        <el-table-column label="类型" width="110">
          <template #default="{ row }"
            ><el-tag :type="row.is_primary ? 'primary' : 'info'">{{
              row.is_primary ? "主公司" : "任职公司"
            }}</el-tag></template
          >
        </el-table-column>
        <el-table-column label="操作" width="110">
          <template #default="{ row }"
            ><el-button
              link
              type="primary"
              :aria-label="`编辑 ${row.name}`"
              @click="openEditor(row)"
              >编辑</el-button
            ></template
          >
        </el-table-column>
      </el-table>
    </div>
    <el-dialog
      v-model="open"
      :title="editingId ? '编辑公司' : '新增公司'"
      width="min(640px, 100vw)"
      :close-on-click-modal="false"
    >
      <el-alert
        v-if="editingPrimary"
        type="info"
        :closable="false"
        title="这是主公司，与上方“主公司信息”为同一数据。"
      />
      <LoadState :busy="edit.busy.value" :error="edit.error.value" />
      <FieldForm
        v-if="open"
        :key="editingId ?? 'new'"
        :model="{ ...model }"
        :fields="companyFields"
        :busy="edit.busy.value"
        :submit-text="editingId ? '保存公司' : '创建公司'"
        @update="update"
        @submit="save"
      />
    </el-dialog>
  </section>
</template>
