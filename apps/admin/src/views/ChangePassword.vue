<!-- C1 首次改密 -->
<script setup lang="ts">
import { reactive, useTemplateRef } from "vue";
import { useRouter } from "vue-router";
import type { FormInstance, FormRules } from "element-plus";
import { ElMessage } from "element-plus";
import { api } from "@/api/adapters";
import { useAuthStore } from "@/store/modules/auth";
import { useTask } from "@/composables/useTask";
const auth = useAuthStore(),
  router = useRouter(),
  { busy, error, run } = useTask();
const form = useTemplateRef<FormInstance>("form");
const model = reactive({ old_password: "", new_password: "", confirm: "" });
const rules: FormRules = {
  old_password: [{ required: true, message: "请输入原密码" }],
  new_password: [
    { required: true, message: "请输入新密码" },
    {
      pattern: /^(?=.*[A-Za-z])(?=.*\d).{8,20}$/,
      message: "请输入8–20位，至少含字母和数字（可含符号）",
    },
  ],
  confirm: [
    { required: true, message: "请再次输入新密码" },
    {
      validator: (_r: unknown, v: string, cb: (e?: Error) => void) =>
        cb(v === model.new_password ? undefined : new Error("两次密码不一致")),
    },
  ],
};
async function save() {
  if (!(await form.value?.validate().catch(() => false))) return;
  if (model.old_password === model.new_password) {
    ElMessage.warning("新密码不能与原密码相同");
    return;
  }
  await run(async () => {
    await api.changePassword({
      old_password: model.old_password,
      new_password: model.new_password,
    });
    auth.logout();
    model.old_password = "";
    model.new_password = "";
    model.confirm = "";
    ElMessage.success("密码已更新，请使用新密码重新登录");
    await router.replace("/login");
  });
}
</script>
<template>
  <main class="auth-page">
    <section class="auth-card" aria-labelledby="password-title">
      <header class="auth-band">
        <span class="auth-mark" aria-hidden="true">AI</span>
        <p class="auth-product">数科 AI 智能名片 · 管理后台</p>
      </header>
      <div class="auth-body">
        <h1 id="password-title">设置新密码</h1>
        <p class="muted">首次登录必须先修改密码，完成后才能使用管理功能。</p>
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
          @submit.prevent="save"
          ><el-form-item label="原密码" prop="old_password"
            ><el-input
              v-model="model.old_password"
              type="password"
              show-password
              autocomplete="current-password" /></el-form-item
          ><el-form-item label="新密码" prop="new_password"
            ><el-input
              v-model="model.new_password"
              type="password"
              show-password
              autocomplete="new-password"
              maxlength="20" /></el-form-item
          ><el-form-item label="确认新密码" prop="confirm"
            ><el-input
              v-model="model.confirm"
              type="password"
              show-password
              autocomplete="new-password"
              maxlength="20"
          /></el-form-item>
          <div class="toolbar">
            <el-button native-type="submit" type="primary" :loading="busy"
              >更新密码</el-button
            ><el-button @click="auth.logout">退出登录</el-button>
          </div></el-form
        >
      </div>
    </section>
  </main>
</template>
<style scoped>
.auth-page {
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: var(--ac-space-5, 24px) var(--ac-space-4, 16px);
  background: var(--ac-bg, var(--el-fill-color-light));
  font-family:
    system-ui,
    -apple-system,
    "PingFang SC",
    "Microsoft YaHei",
    sans-serif;
}
.auth-card {
  width: min(480px, 100%);
  overflow: hidden;
  background: var(--ac-surface, var(--el-bg-color));
  border: 1px solid var(--ac-border, var(--el-border-color-light));
  border-radius: var(--ac-radius, 8px);
  box-shadow: var(--ac-shadow, var(--el-box-shadow-light));
}
.auth-band {
  display: flex;
  gap: var(--ac-space-3, 12px);
  align-items: center;
  padding: var(--ac-space-4, 16px) var(--ac-space-5, 24px);
  background: var(--ac-navy, var(--el-color-primary));
  color: var(--ac-surface, var(--el-bg-color));
}
.auth-mark {
  display: inline-grid;
  place-items: center;
  flex: none;
  width: 36px;
  height: 36px;
  border-radius: var(--ac-radius, 8px);
  background: var(--ac-teal, var(--el-color-success));
  color: var(--ac-surface, var(--el-bg-color));
  font-weight: 700;
}
.auth-product {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
}
.auth-body {
  padding: var(--ac-space-5, 24px);
}
.auth-card h1 {
  margin: 0;
  font-size: 22px;
  color: var(--ac-text, var(--el-text-color-primary));
}
.auth-card .toolbar {
  margin-bottom: 0;
}
</style>
