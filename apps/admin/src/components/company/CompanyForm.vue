<script setup lang="ts">
import { ref, onMounted } from "vue";
import { ElMessage } from "element-plus";
import { api } from "@/api/adapters";
import type { Company } from "@/api/schema";
import FieldForm from "@/components/FieldForm.vue";
import LoadState from "@/components/LoadState.vue";
import { useTask } from "@/composables/useTask";
import { companyFields as fields } from "./companyFields";
const model = ref<Company>();
const { busy, error, run } = useTask();
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
    <h2>主公司信息</h2>
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
