<script setup lang="ts">
import { reactive, useTemplateRef } from "vue";
import { useRoute, useRouter } from "vue-router";
import type { FormInstance, FormRules } from "element-plus";
import { useAuthStore } from "@/store/modules/auth";
import { useTask } from "@/composables/useTask";
import { redirectQuery, resolveTarget } from "@/router/redirect";
const auth = useAuthStore(),
  router = useRouter(),
  route = useRoute(),
  { busy, error, run } = useTask();
const model = reactive({ phone: "", password: "" });
const form = useTemplateRef<FormInstance>("form");
const rules: FormRules = {
  phone: [
    { required: true, message: "请输入手机号" },
    { pattern: /^1\d{10}$/, message: "请输入11位手机号" },
  ],
  password: [{ required: true, message: "请输入密码" }],
};
async function submit() {
  if (!(await form.value?.validate().catch(() => false))) return;
  await run(async () => {
    await auth.login(model.phone, model.password);
    model.password = "";
    const target = route.query.redirect;
    await router.replace(
      auth.session?.must_change_pwd
        ? { path: "/change-password", query: redirectQuery(target) }
        : resolveTarget(target),
    );
  });
}
</script>
<template>
  <el-alert
    v-if="error"
    :title="error"
    type="error"
    :closable="false"
  /><el-form
    ref="form"
    :model="model"
    :rules="rules"
    label-position="top"
    @submit.prevent="submit"
    ><el-form-item label="管理员手机号" prop="phone"
      ><el-input
        v-model="model.phone"
        inputmode="tel"
        autocomplete="username"
        maxlength="11" /></el-form-item
    ><el-form-item label="密码" prop="password"
      ><el-input
        v-model="model.password"
        type="password"
        show-password
        autocomplete="current-password"
        maxlength="72" /></el-form-item
    ><el-button type="primary" native-type="submit" :loading="busy"
      >登录管理后台</el-button
    ></el-form
  >
</template>
