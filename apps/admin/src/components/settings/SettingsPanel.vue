<script setup lang="ts">
import { shallowRef, computed, onMounted } from "vue";
import { ElMessage } from "element-plus";
import { api } from "@/api/adapters";
import { useTask, confirmAction } from "@/composables/useTask";
import LoadState from "@/components/LoadState.vue";
import RuntimeValueForm from "./RuntimeValueForm.vue";
import {
  runtimeFields,
  sanitizeRuntime,
  providerReady,
  canActivate,
  type RuntimeSnapshot,
} from "./runtimeFields";
const emit = defineEmits<{ applied: [] }>();
const selectedKey = shallowRef("visitor_daily_limit"),
  snapshot = shallowRef<RuntimeSnapshot>(),
  version = shallowRef(0);
const { busy, error, run } = useTask();
const groups = [...new Set(runtimeFields.map((f) => f.group))];
const field = computed(
  () =>
    runtimeFields.find((f) => f.key === selectedKey.value) ?? runtimeFields[0],
);
const configured = computed(
  () => snapshot.value?.configured[field.value.key] ?? false,
);
const canEnable = computed(() =>
  !snapshot.value
    ? false
    : field.value.kind === "mode"
      ? canActivate(snapshot.value)
      : providerReady(snapshot.value, true),
);
const canClear = computed(
  () =>
    !!snapshot.value &&
    (snapshot.value.values.llm_mode === "fake" ||
      (field.value.key === "llm_fallback_api_key" &&
        snapshot.value.values.llm_fallback_enabled !== true)),
);
async function refresh() {
  const result = await api.runtimeSettings();
  if (result.limits_unit !== "messages_per_day")
    throw new Error("限额单位与当前界面不匹配");
  snapshot.value = sanitizeRuntime(result.settings);
  version.value++;
}
async function load() {
  await run(refresh);
}
async function save(value: unknown) {
  if (
    field.value.key === "llm_mode" &&
    value === "openai" &&
    !(await confirmAction(
      "启用已配置的真实模型？后续对话会调用模型服务并产生费用。",
    ))
  )
    return;
  await run(async () => {
    await api.saveSetting(field.value.key, value);
    await refresh();
    emit("applied");
    ElMessage.success("配置已保存，后续请求使用新值");
  });
}
async function clear() {
  if (
    !canClear.value ||
    !(await confirmAction(
      `确认清空${field.value.label}？清空后需要重新配置才能使用。`,
    ))
  )
    return;
  await run(async () => {
    await api.saveSetting(field.value.key, "", true);
    await refresh();
    emit("applied");
    ElMessage.success("密钥已显式清空");
  });
}
onMounted(load);
</script>
<template>
  <section class="panel">
    <div class="toolbar">
      <h2>运行时配置</h2>
      <el-button :loading="busy" @click="load">刷新当前配置</el-button>
    </div>
    <p class="muted">
      每项独立保存并校验，成功后从后续请求开始使用。每日限额单位为对话次数；保留天数由清理任务应用。
    </p>
    <el-alert
      title="模型连接按“接口地址 → 模型名称 → 密钥 → 启用模式”逐项配置；备用模型同样先配置完整再启用。当前不提供多项原子保存。"
      type="info"
      :closable="false"
    />
    <p class="muted">
      模型密钥只显示是否已配置，不回填原值或掩码。知识直接输入 Token
      上限当前不支持。
    </p>
    <LoadState :busy="busy" :error="error" @retry="load" /><el-select
      filterable
      v-model="selectedKey"
      class="field-selector"
      aria-label="选择运行配置项"
      :disabled="busy"
      ><el-option-group v-for="group in groups" :key="group" :label="group"
        ><el-option
          v-for="item in runtimeFields.filter((f) => f.group === group)"
          :key="item.key"
          :label="item.label"
          :value="item.key" /></el-option-group></el-select
    ><RuntimeValueForm
      v-if="snapshot"
      :key="selectedKey + '-' + version"
      :field="field"
      :initial="snapshot.values[selectedKey]"
      :configured="configured"
      :busy="busy"
      :can-enable="canEnable"
      :can-clear="canClear"
      @save="save"
      @clear="clear"
    />
  </section>
</template>
<style scoped>
.field-selector {
  width: 360px;
  max-width: 100%;
  margin: 20px 0;
}
</style>
