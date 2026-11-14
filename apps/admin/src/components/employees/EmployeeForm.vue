<script setup lang="ts">
import { reactive, useTemplateRef } from "vue";
import type { FormInstance, FormRules } from "element-plus";
import type { Staff, EmployeeInput, EmployeeUpdate } from "@/api/schema";
const props = defineProps<{ initial: Staff | null; busy: boolean }>();
const emit = defineEmits<{ save: [body: EmployeeInput | EmployeeUpdate] }>();
const model = reactive({
  name: props.initial?.name ?? "",
  phone: props.initial?.phone ?? "",
  dept: props.initial?.dept ?? "",
  title: props.initial?.title ?? "",
  password: "",
  role: props.initial?.role ?? "employee",
});
const form = useTemplateRef<FormInstance>("form");
const rules: FormRules = {
  name: [{ required: true, message: "请填写姓名" }],
  phone: [
    { required: true, message: "请填写手机号" },
    { pattern: /^1\d{10}$/, message: "请输入11位手机号" },
  ],
  password: [
    { required: !props.initial, message: "请设置初始密码" },
    { min: 8, max: 72, message: "密码长度8–72位" },
  ],
};
async function save() {
  if (!(await form.value?.validate().catch(() => false))) return;
  const { password, ...body } = model;
  emit(
    "save",
    props.initial
      ? {
          name: body.name,
          phone: body.phone,
          dept: body.dept,
          title: body.title,
        }
      : { ...body, password },
  );
}
</script>
<template>
  <el-form
    ref="form"
    :model="model"
    :rules="rules"
    label-position="top"
    @submit.prevent="save"
    ><el-form-item label="姓名" prop="name"
      ><el-input v-model="model.name" maxlength="100" /></el-form-item
    ><el-form-item label="手机号" prop="phone"
      ><el-input
        v-model="model.phone"
        maxlength="11"
        inputmode="tel" /></el-form-item
    ><el-form-item label="部门"
      ><el-input v-model="model.dept" maxlength="100" /></el-form-item
    ><el-form-item label="职务"
      ><el-input v-model="model.title" maxlength="100" /></el-form-item
    ><el-form-item v-if="!initial" label="角色"
      ><el-select v-model="model.role"
        ><el-option label="员工" value="employee" /><el-option
          label="管理员"
          value="admin" /></el-select></el-form-item
    ><el-form-item v-if="!initial" label="初始密码" prop="password"
      ><el-input
        v-model="model.password"
        type="password"
        show-password
        autocomplete="new-password"
        maxlength="72"
      /><span class="muted"
        >首次登录需修改密码。请通过安全渠道交付口令。</span
      ></el-form-item
    ><el-button type="primary" native-type="submit" :loading="busy"
      >保存员工</el-button
    ></el-form
  >
</template>
