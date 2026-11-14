<script setup lang="ts">
import { ref, onMounted } from "vue";
import { ElMessage } from "element-plus";
import { api } from "@/api/adapters";
import type { Company } from "@/api/schema";
import FieldForm, { type Field } from "@/components/FieldForm.vue";
import LoadState from "@/components/LoadState.vue";
import { useTask } from "@/composables/useTask";
const model = ref<Company>();
const { busy, error, run } = useTask();
const fields: Field[] = [
  { key: "name", label: "公司名称", required: true, max: 120 },
  { key: "short_name", label: "公司简称", max: 60 },
  { key: "intro", label: "公司简介", type: "textarea", max: 10000 },
  { key: "phone", label: "官方电话", max: 40 },
  { key: "address", label: "总部地址", max: 255 },
  { key: "website", label: "官方网站", type: "url", max: 255 },
  {
    key: "logo_url",
    label: "Logo 地址",
    type: "url",
    hint: "填写已有的公开图片地址；本地契约暂无图片上传接口。",
  },
];
async function load() {
  await run(async () => {
    model.value = await api.company();
  });
}
function update(key: string, value: unknown) {
  if (model.value) model.value = { ...model.value, [key]: value };
}
async function save() {
  await run(async () => {
    if (model.value) {
      model.value = await api.saveCompany(model.value);
      ElMessage.success("企业信息已保存");
    }
  });
}
onMounted(load);
</script>
<template>
  <section class="panel">
    <h2>企业信息</h2>
    <LoadState :busy="busy" :error="error" @retry="load" /><FieldForm
      v-if="model"
      :model="{ ...model }"
      :fields="fields"
      :busy="busy"
      @update="update"
      @submit="save"
    />
  </section>
</template>
