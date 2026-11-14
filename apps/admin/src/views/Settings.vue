<!-- C10 设置与审计 -->
<script setup lang="ts">
import RuntimeStatus from "@/components/settings/RuntimeStatus.vue";
import SettingsPanel from "@/components/settings/SettingsPanel.vue";
import AuditPanel from "@/components/settings/AuditPanel.vue";
</script>
<template>
  <section class="page">
    <div>
      <h1>设置与审计</h1>
      <p class="muted">
        这里只维护允许公开读取的运行配置。模型密钥由后端环境安全管理。
      </p>
    </div>
    <RuntimeStatus /><SettingsPanel /><AuditPanel />
  </section>
</template>
