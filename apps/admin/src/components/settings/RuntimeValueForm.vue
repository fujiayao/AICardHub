<script setup lang="ts">
import { ref, shallowRef } from "vue";
import { type RuntimeField, validateRuntimeValue } from "./runtimeFields";
const props = defineProps<{
  field: RuntimeField;
  initial: unknown;
  busy: boolean;
  configured: boolean;
  canEnable: boolean;
  canClear: boolean;
}>();
const emit = defineEmits<{ save: [value: unknown]; clear: [] }>();
const value = ref(
  props.field.kind === "secret"
    ? ""
    : props.field.kind === "words" && Array.isArray(props.initial)
      ? props.initial.join("\n")
      : props.initial,
);
const error = shallowRef("");
function submit() {
  error.value = "";
  try {
    const parsed = validateRuntimeValue(props.field, value.value);
    emit("save", parsed);
    if (props.field.kind === "secret") value.value = "";
  } catch (e) {
    error.value = e instanceof Error ? e.message : "请检查配置值";
  }
}
</script>
<template>
  <el-form label-position="top" :disabled="busy" @submit.prevent="submit"
    ><el-form-item :label="field.label" :error="error" required>
      <el-input
        v-if="field.kind === 'secret'"
        v-model="value as string"
        type="password"
        :maxlength="field.max"
        autocomplete="new-password"
        :placeholder="
          configured ? '已配置；填写新值才会更新' : '未配置；请输入新密钥'
        "
        :aria-label="field.label"
      />
      <el-input-number
        v-else-if="field.kind === 'number'"
        v-model="value as number"
        :min="field.min"
        :max="field.max"
        :precision="field.integer ? 0 : undefined"
        :aria-label="field.label"
      />
      <el-select
        filterable
        v-else-if="field.kind === 'mode'"
        v-model="value as string"
        :aria-label="field.label"
        ><el-option label="本地演示模型（Fake）" value="fake" /><el-option
          label="真实模型（OpenAI兼容）"
          value="openai"
          :disabled="!canEnable"
      /></el-select>
      <el-select
        v-else-if="field.kind === 'protocol'"
        v-model="value as string"
        :aria-label="field.label"
      >
        <el-option label="Responses（原生）" value="responses" />
        <el-option label="Chat Completions（兼容）" value="chat_completions" />
      </el-select>
      <el-switch
        v-else-if="field.kind === 'boolean'"
        v-model="value as boolean"
        :aria-label="field.label"
        :disabled="!canEnable && value !== true"
      />
      <el-input
        v-else
        v-model="value as string"
        :aria-label="field.label"
        :type="field.kind === 'words' ? 'textarea' : 'text'"
        :rows="field.kind === 'words' ? 8 : undefined"
        :maxlength="field.kind === 'words' ? 20200 : field.max"
      />
    </el-form-item>
    <p v-if="field.kind === 'secret'" class="muted">
      {{
        configured ? "已配置" : "未配置"
      }}。不回显密钥或掩码；留空不覆盖，替换后立即清空输入。
    </p>
    <p v-if="field.hint" class="muted">{{ field.hint }}</p>
    <p
      v-if="!canEnable && (field.kind === 'mode' || field.kind === 'boolean')"
      class="muted"
    >
      先分别保存接口地址、模型名称、接口协议及密钥，配置完整后再启用。
    </p>
    <div class="toolbar">
      <el-button
        native-type="submit"
        type="primary"
        :loading="busy"
        :disabled="field.kind === 'secret' && !value"
        >{{ field.kind === "secret" ? "更新密钥" : "保存并应用" }}</el-button
      ><el-button
        v-if="field.kind === 'secret'"
        type="danger"
        :disabled="!configured || !canClear"
        @click="emit('clear')"
        >显式清空密钥</el-button
      >
    </div>
    <p v-if="field.kind === 'secret' && !canClear" class="muted">
      请先切换到本地演示模式，或停用对应备用/兜底模型，再清空当前使用中的密钥。
    </p></el-form
  >
</template>
