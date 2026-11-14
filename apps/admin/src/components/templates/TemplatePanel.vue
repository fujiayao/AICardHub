<script setup lang="ts">
import { ref, onMounted } from "vue";
import { ElMessage } from "element-plus";
import { api } from "@/api/adapters";
import type { Template } from "@/api/schema";
import { useTask, confirmAction } from "@/composables/useTask";
import LoadState from "@/components/LoadState.vue";
import TemplateForm from "./TemplateForm.vue";
import PageHeader from "@/components/shared/PageHeader.vue";
const { busy, error, run } = useTask();
const rows = ref<Template[]>([]),
  draft = ref<Omit<Template, "id"> | null>(null),
  id = ref<number | null>(null);
async function load() {
  await run(async () => {
    rows.value = await api.templates();
  });
}
function edit(row?: Template) {
  id.value = row?.id ?? null;
  draft.value = row
    ? { ...row, guide_questions: [...(row.guide_questions ?? [])] }
    : {
        name: "",
        persona: "",
        opening: "",
        guide_questions: [],
        is_default: false,
        enabled: true,
      };
}
async function save(body: Omit<Template, "id">) {
  await run(async () => {
    await api.saveTemplate(id.value, body);
    draft.value = null;
    rows.value = await api.templates();
    ElMessage.success("模板已保存");
  });
}
async function setDefault(row: Template) {
  if (!(await confirmAction(`将“${row.name}”设为新名片的默认模板？`))) return;
  await run(async () => {
    await api.defaultTemplate(row.id);
    rows.value = await api.templates();
    ElMessage.success("默认模板已更新");
  });
}
async function remove(row: Template) {
  if (!(await confirmAction(`删除模板“${row.name}”？被引用的模板由后端校验。`)))
    return;
  await run(async () => {
    await api.deleteTemplate(row.id);
    rows.value = await api.templates();
  });
}
onMounted(load);
</script>
<template>
  <section class="page">
    <PageHeader
      title="AI 模板"
      desc="统一维护人设、开场白和引导问题。默认模板用于新建名片。"
    >
      <el-button type="primary" @click="edit()">新增模板</el-button>
    </PageHeader>
    <div class="panel">
      <div class="toolbar">
        <el-button :loading="busy" @click="load">刷新</el-button>
      </div>
      <LoadState :busy="busy" :error="error" @retry="load" />
      <div class="table-wrap">
        <el-table :data="rows" empty-text="尚无模板"
          ><el-table-column prop="name" label="名称" /><el-table-column
            prop="opening"
            label="开场白"
            show-overflow-tooltip
          /><el-table-column label="状态" width="160"
            ><template #default="{ row }"
              ><el-tag :type="row.enabled ? 'success' : 'info'">{{
                row.enabled ? "启用" : "停用"
              }}</el-tag>
              <el-tag v-if="row.is_default">默认</el-tag></template
            ></el-table-column
          ><el-table-column label="操作" min-width="240"
            ><template #default="{ row }"
              ><el-button link type="primary" @click="edit(row)">编辑</el-button
              ><el-button
                link
                type="primary"
                :disabled="row.is_default || !row.enabled || busy"
                @click="setDefault(row)"
                >设为默认</el-button
              ><el-button
                link
                type="danger"
                :disabled="row.is_default || busy"
                @click="remove(row)"
                >删除</el-button
              ></template
            ></el-table-column
          ></el-table
        >
      </div>
    </div>
    <el-dialog
      :model-value="!!draft"
      :title="id ? '编辑模板' : '新增模板'"
      width="min(680px, 100vw)"
      :close-on-click-modal="false"
      @update:model-value="
        (v) => {
          if (!v && !busy) draft = null;
        }
      "
      ><TemplateForm v-if="draft" :initial="draft" :busy="busy" @save="save"
    /></el-dialog>
  </section>
</template>
