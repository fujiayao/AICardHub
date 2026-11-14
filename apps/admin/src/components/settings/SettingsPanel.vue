<script setup lang="ts">
import { ref, shallowRef } from "vue";
import { ElMessage } from "element-plus";
import { api } from "@/api/adapters";
import { useTask } from "@/composables/useTask";
import LoadState from "@/components/LoadState.vue";
// Fixed non-secret allowlist: no free-form key access, no credential input or display.
const options = [
  { key: "llm_mode", label: "模型运行方式", kind: "mode" },
  { key: "visitor_daily_limit", label: "单访客每日对话限额", kind: "number" },
  { key: "card_daily_limit", label: "单名片每日对话限额", kind: "number" },
  { key: "global_daily_limit", label: "全局每日对话限额", kind: "number" },
  {
    key: "inline_token_limit",
    label: "知识直接输入 Token 上限",
    kind: "number",
  },
  {
    key: "visitor_retention_days",
    label: "对话与访客数据保留天数",
    kind: "number",
  },
] as const;
const selected = ref<(typeof options)[number]>(options[0]),
  value = ref<string | number>(""),
  loadedKey = shallowRef("");
const unset = shallowRef(false);
const { busy, error, run } = useTask();
async function load() {
  loadedKey.value = "";
  unset.value = false;
  await run(async () => {
    const result = await api.setting(selected.value.key);
    if (result.key !== selected.value.key)
      throw new Error("服务返回的设置键不匹配");
    const raw = result.value;
    if (raw === null || raw === undefined) {
      unset.value = true;
      value.value = selected.value.kind === "mode" ? "fake" : 1;
      loadedKey.value = result.key;
      return;
    }
    if (selected.value.kind === "mode") {
      if (raw !== "fake" && raw !== "openai")
        throw new Error("模型方式不在允许范围内");
      value.value = raw;
    } else {
      if (typeof raw !== "number" || !Number.isInteger(raw) || raw < 1)
        throw new Error("设置值应为正整数");
      value.value = raw;
    }
    loadedKey.value = result.key;
  });
}
async function save() {
  if (loadedKey.value !== selected.value.key) return;
  if (
    selected.value.kind === "number" &&
    (!Number.isSafeInteger(Number(value.value)) || Number(value.value) < 1)
  ) {
    ElMessage.warning("请输入有效正整数");
    return;
  }
  await run(async () => {
    await api.saveSetting(selected.value.key, value.value);
    ElMessage.success("配置表记录已保存；运行时是否应用请核对服务配置");
  });
}
</script>
<template>
  <section class="panel">
    <h2>非敏感配置记录</h2>
    <el-alert
      title="当前接口保存配置表记录；模型与限额运行时仍由服务环境控制。保存不代表立即生效，运行时应用尚待后端接入。"
      type="warning"
      :closable="false"
    />
    <p class="muted">
      读取配置表中的真实记录。未配置时需手动填写；这里不把空值当作当前运行值。
    </p>
    <div class="toolbar">
      <el-select
        v-model="selected"
        value-key="key"
        style="width: 280px"
        :disabled="busy"
        @change="loadedKey = ''"
        ><el-option
          v-for="option in options"
          :key="option.key"
          :label="option.label"
          :value="option" /></el-select
      ><el-button :loading="busy" @click="load">读取配置</el-button>
    </div>
    <LoadState :busy="busy" :error="error" @retry="load" /><el-form
      v-if="loadedKey === selected.key"
      label-position="top"
      @submit.prevent="save"
      ><p v-if="unset" class="muted">此项尚未配置，下方是待保存的新值。</p>
      <el-form-item :label="selected.label" required
        ><el-select v-if="selected.kind === 'mode'" v-model="value"
          ><el-option
            label="本地演示模型（Fake，不是真实模型）"
            value="fake" /><el-option
            label="后端已配置的真实模型"
            value="openai" /></el-select
        ><el-input-number
          v-else
          v-model="value as number"
          :min="1"
          :max="1000000000"
          :precision="0" /></el-form-item
      ><el-alert
        v-if="selected.key === 'llm_mode' && value === 'fake'"
        title="本地演示模型：回答用于流程验证，不代表真实模型质量评测通过。"
        type="warning"
        :closable="false"
      />
      <p>
        <el-button type="primary" native-type="submit" :loading="busy"
          >保存此项设置</el-button
        >
      </p></el-form
    ><el-divider />
    <p class="muted">
      此页面不读取、不回显 API
      Key、数据库口令、访问令牌或中转凭据。模型地址/型号/超时配置在冻结字段明确前不提供猜测式编辑。
    </p>
  </section>
</template>
