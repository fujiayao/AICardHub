<script setup lang="ts">
import { ref, onMounted } from "vue";
import { ElMessage } from "element-plus";
import { api } from "@/api/adapters";
import type { Product, ProductInput } from "@/api/schema";
import FieldForm, { type Field } from "@/components/FieldForm.vue";
import LoadState from "@/components/LoadState.vue";
import { useTask, confirmAction } from "@/composables/useTask";
const { busy, error, run } = useTask();
const rows = ref<Product[]>([]),
  draft = ref<ProductInput | null>(null),
  editing = ref<number | null>(null);
const fields: Field[] = [
  { key: "title", label: "产品标题", required: true },
  { key: "summary", label: "一句话说明", required: true, type: "textarea" },
  { key: "image_url", label: "配图地址", type: "url" },
  { key: "ask_question", label: "点击后带入对话的问题", required: true },
];
async function load() {
  await run(async () => {
    rows.value = await api.products();
  });
}
function edit(row?: Product) {
  editing.value = row?.id ?? null;
  draft.value = row
    ? {
        title: row.title,
        summary: row.summary,
        image_url: row.image_url,
        ask_question: row.ask_question,
        sort: row.sort ?? 0,
        enabled: row.enabled ?? true,
      }
    : {
        title: "",
        summary: "",
        image_url: "",
        ask_question: "",
        sort: 0,
        enabled: true,
      };
}
function update(key: string, value: unknown) {
  if (draft.value) draft.value = { ...draft.value, [key]: value };
}
async function save() {
  await run(async () => {
    if (!draft.value) return;
    await api.saveProduct(editing.value, draft.value);
    draft.value = null;
    rows.value = await api.products();
    ElMessage.success("产品已保存");
  });
}
async function remove(row: Product) {
  if (
    !(await confirmAction(`删除产品“${row.title}”？所有名片将不再显示该产品。`))
  )
    return;
  await run(async () => {
    await api.deleteProduct(row.id);
    rows.value = await api.products();
    ElMessage.success("产品已删除");
  });
}
onMounted(load);
</script>
<template>
  <section class="panel">
    <div class="toolbar">
      <h2>产品卡片</h2>
      <el-button type="primary" @click="edit()">新增产品</el-button
      ><el-button :loading="busy" @click="load">刷新</el-button>
    </div>
    <LoadState :busy="busy" :error="error" @retry="load" /><el-table
      :data="rows"
      empty-text="尚未添加产品"
      ><el-table-column prop="title" label="标题" /><el-table-column
        prop="summary"
        label="说明"
        show-overflow-tooltip
      /><el-table-column label="操作" width="180"
        ><template #default="{ row }"
          ><el-button link type="primary" @click="edit(row)">编辑</el-button
          ><el-button link type="danger" :disabled="busy" @click="remove(row)"
            >删除</el-button
          ></template
        ></el-table-column
      ></el-table
    ><el-dialog
      :model-value="!!draft"
      :title="editing ? '编辑产品' : '新增产品'"
      width="640px"
      :close-on-click-modal="false"
      :before-close="
        (done) => {
          if (!busy) {
            draft = null;
            done();
          }
        }
      "
      @update:model-value="
        (value) => {
          if (!value && !busy) draft = null;
        }
      "
      ><FieldForm
        v-if="draft"
        :model="{ ...draft }"
        :fields="fields"
        :busy="busy"
        @update="update"
        @submit="save"
    /></el-dialog>
  </section>
</template>
