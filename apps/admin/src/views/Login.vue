<!-- C1 管理员登录 -->
<script setup lang="ts">
import LoginForm from "@/components/auth/LoginForm.vue";
</script>
<template>
  <div class="login-page">
    <section class="panel login-panel">
      <h1>数科名片管理后台</h1>
      <p class="muted">使用管理员手机号登录。员工账号请从员工端进入。</p>
      <LoginForm />
      <p class="muted">本地候选 · 管理员会话独立保存，过期后需重新登录。</p>
    </section>
  </div>
</template>
<style scoped>
.login-page {
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 24px;
}
.login-panel {
  width: 440px;
  max-width: 100%;
}
</style>
