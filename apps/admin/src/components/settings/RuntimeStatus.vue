<script setup lang="ts">
import { shallowRef, onMounted } from "vue";
import { api } from "@/api/adapters";
import { useTask } from "@/composables/useTask";
import LoadState from "@/components/LoadState.vue";
const mode = shallowRef("");
const { busy, error, run } = useTask();
async function load() {
  await run(async () => {
    const result = await api.health();
    mode.value = result.llm_mode;
  });
}
onMounted(load);
</script>
<template>
  <section class="panel">
    <div class="toolbar">
      <h2>当前服务状态</h2>
      <el-button :loading="busy" @click="load">刷新</el-button>
    </div>
    <LoadState :busy="busy" :error="error" @retry="load" /><el-alert
      v-if="mode === 'fake'"
      title="本地演示模型（Fake）：仅用于流程验证，不代表真实模型评测通过。"
      type="warning"
      :closable="false"
    />
    <p v-else-if="mode">
      当前模型方式：{{ mode }}。连接状态不代表质量评测通过。
    </p>
    <p class="muted">模型凭据由后端安全保存；此页面不请求或回填密钥。</p>
  </section>
</template>
