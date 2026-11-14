<!-- C1 管理员登录 -->
<script setup lang="ts">
import LoginForm from "@/components/auth/LoginForm.vue";
</script>
<template>
  <div class="auth-page">
    <section class="auth-card" aria-labelledby="login-title">
      <header class="auth-band">
        <span class="auth-mark" aria-hidden="true">AI</span>
        <p class="auth-product">数科 AI 智能名片 · 管理后台</p>
      </header>
      <div class="auth-body">
        <h1 id="login-title">管理员登录</h1>
        <p class="muted">使用管理员手机号登录。员工账号请从员工端进入。</p>
        <LoginForm />
        <p class="muted auth-foot">
          本地候选 · 管理员会话独立保存，过期后需重新登录。
        </p>
      </div>
    </section>
  </div>
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
  width: min(440px, 100%);
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
.auth-body h1 {
  margin: 0;
  font-size: 22px;
  color: var(--ac-text, var(--el-text-color-primary));
}
.auth-foot {
  margin-bottom: 0;
  font-size: 12px;
}
</style>
