<!-- C10 设置与审计 -->
<script setup lang="ts">
import { shallowRef } from "vue";
import RuntimeStatus from "@/components/settings/RuntimeStatus.vue";
import SettingsPanel from "@/components/settings/SettingsPanel.vue";
import AuditPanel from "@/components/settings/AuditPanel.vue";
import PageHeader from "@/components/shared/PageHeader.vue";
const statusVersion = shallowRef(0);
</script>
<template>
  <section class="page">
    <PageHeader
      title="设置与审计"
      desc="管理后续请求使用的主模型、备用与兜底模型、每日次数限额、数据保留与敏感词。密钥由后端加密保存。"
    />
    <RuntimeStatus :key="statusVersion" /><SettingsPanel
      @applied="statusVersion++"
    /><AuditPanel />
  </section>
</template>
