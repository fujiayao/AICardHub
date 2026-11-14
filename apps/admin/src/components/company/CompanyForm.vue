<script setup lang="ts">
import { ref, shallowRef, onMounted } from "vue";
import { ElMessage } from "element-plus";
import { api } from "@/api/adapters";
import type { Company } from "@/api/schema";
import FieldForm from "@/components/FieldForm.vue";
import LoadState from "@/components/LoadState.vue";
import { useTask } from "@/composables/useTask";
import { companyFields as fields } from "./companyFields";
const emit = defineEmits<{ saved: [] }>();
const model = ref<Company>();
const dirty = shallowRef(false),
  stale = shallowRef(false);
const { busy, error, run } = useTask();
async function load() {
  await run(async () => {
    model.value = await api.company();
    dirty.value = false;
    stale.value = false;
  });
}
/** Called when the primary company changed elsewhere; never discards unsaved input. */
async function refresh() {
  if (dirty.value) stale.value = true;
  else await load();
}
function update(key: string, value: unknown) {
  if (model.value) {
    model.value = { ...model.value, [key]: value };
    dirty.value = true;
  }
}
async function save() {
  const current = model.value;
  if (!current) return;
  const saved = await run(() => api.saveCompany(current));
  if (!saved) return;
  model.value = saved;
  dirty.value = false;
  stale.value = false;
  ElMessage.success("主公司信息已保存");
  emit("saved");
}
defineExpose({ refresh });
onMounted(load);
</script>
<template>
  <section class="panel">
    <h2>主公司信息</h2>
    <el-alert
      v-if="stale"
      type="warning"
      :closable="false"
      title="主公司信息已在“任职公司”中被修改，当前表单有未保存内容。"
      ><el-button link type="primary" @click="load"
        >放弃修改并载入最新</el-button
      ></el-alert
    >
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
