<script setup lang="ts">
import { ref, reactive, onMounted, useTemplateRef } from "vue";
import { ElMessage, type FormInstance, type FormRules } from "element-plus";
import { api, staffEnabled } from "@/api/adapters";
import type { Staff } from "@/api/schema";
import { useTask, confirmAction } from "@/composables/useTask";
import LoadState from "@/components/LoadState.vue";
const props = defineProps<{
  staff: Staff;
  mode: "reset" | "transfer";
  selfId?: number;
}>();
const emit = defineEmits<{ done: [] }>();
const { busy, error, run } = useTask();
const targets = ref<Staff[]>([]),
  ready = ref(false);
const model = reactive({
  password: "",
  to_employee_id: undefined as number | undefined,
});
const form = useTemplateRef<FormInstance>("form");
const rules: FormRules = {
  password: [
    { required: true, message: "请输入新密码" },
    {
      pattern: /^(?=.*[A-Za-z])(?=.*\d).{8,20}$/,
      message: "请输入8–20位，至少含字母和数字（可含符号）",
    },
  ],
  to_employee_id: [{ required: true, message: "请选择接收员工" }],
};
async function load() {
  if (props.mode !== "transfer") return;
  await run(async () => {
    const all: Staff[] = [];
    let page = 1;
    while (page <= 100) {
      const result = await api.employees({ page, page_size: 100 });
      all.push(...result.items);
      if (all.length >= result.total || !result.items.length) break;
      page++;
    }
    targets.value = all.filter(
      (s) => s.id !== props.staff.id && staffEnabled(s),
    );
    ready.value = true;
  });
}
async function submit() {
  if (!(await form.value?.validate().catch(() => false))) return;
  if (
    props.mode === "transfer" &&
    (props.staff.id === props.selfId || !ready.value)
  )
    return;
  const message =
    props.mode === "reset"
      ? `重置 ${props.staff.name} 的密码？对方下次登录需改密。`
      : `将 ${props.staff.name} 的线索及责任转交给选中员工？操作会记录审计。`;
  if (!(await confirmAction(message))) return;
  await run(async () => {
    if (props.mode === "reset")
      await api.resetPassword(props.staff.id, model.password);
    else if (model.to_employee_id)
      await api.transfer(props.staff.id, model.to_employee_id);
    model.password = "";
    ElMessage.success("操作已完成");
    emit("done");
  });
}
onMounted(load);
</script>
<template>
  <LoadState :busy="busy" :error="error" @retry="load" /><el-form
    ref="form"
    :model="model"
    :rules="rules"
    label-position="top"
    @submit.prevent="submit"
    ><el-form-item v-if="mode === 'reset'" label="新密码" prop="password"
      ><el-input
        v-model="model.password"
        type="password"
        show-password
        autocomplete="new-password"
        maxlength="20" /></el-form-item
    ><el-form-item v-else label="接收员工" prop="to_employee_id"
      ><el-select
        v-model="model.to_employee_id"
        filterable
        :loading="busy"
        placeholder="请选择在职接收员工"
        ><el-option
          v-for="staff in targets"
          :key="staff.id"
          :label="`${staff.name} · ${staff.dept ?? ''}`"
          :value="staff.id" /></el-select></el-form-item
    ><el-button
      type="primary"
      native-type="submit"
      :loading="busy"
      :disabled="mode === 'transfer' && !ready"
      >确认{{ mode === "reset" ? "重置" : "转交" }}</el-button
    ></el-form
  >
</template>
