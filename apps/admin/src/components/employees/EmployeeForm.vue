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
    {
      pattern: /^(?=.*[A-Za-z])(?=.*\d).{8,20}$/,
      message: "请输入8–20位，至少含字母和数字（可含符号）",
    },
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
      ><el-input
        v-model="model.name"
        aria-label="姓名"
        maxlength="100" /></el-form-item
    ><el-form-item label="手机号" prop="phone"
      ><el-input
        v-model="model.phone"
        aria-label="手机号"
        maxlength="11"
        inputmode="tel" /></el-form-item
    ><el-form-item label="部门"
      ><el-input
        v-model="model.dept"
        aria-label="部门"
        maxlength="100" /></el-form-item
    ><el-form-item label="职务"
      ><el-input
        v-model="model.title"
        aria-label="职务"
        maxlength="100" /></el-form-item
    ><el-form-item v-if="!initial" label="角色"
      ><el-select v-model="model.role"
        ><el-option label="员工" value="employee" /><el-option
          label="管理员"
          value="admin" /></el-select></el-form-item
    ><el-form-item v-if="!initial" label="初始密码" prop="password"
      ><el-input
        v-model="model.password"
        aria-label="初始密码"
        type="password"
        show-password
        autocomplete="new-password"
        maxlength="20"
      /><span class="muted"
        >首次登录需修改密码。请通过安全渠道交付口令。</span
      ></el-form-item
    ><el-button type="primary" native-type="submit" :loading="busy"
      >保存员工</el-button
    ></el-form
  >
</template>
