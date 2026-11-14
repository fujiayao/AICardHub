<script setup lang="ts">
import { useTemplateRef } from "vue";
import type { FormInstance, FormRules } from "element-plus";
export interface Field {
  key: string;
  label: string;
  required?: boolean;
  type?:
    | "phone"
    | "text"
    | "textarea"
    | "password"
    | "number"
    | "email"
    | "url";
  min?: number;
  max?: number;
  hint?: string;
}
const props = defineProps<{
  model: Record<string, unknown>;
  fields: Field[];
  busy?: boolean;
  submitText?: string;
}>();
const emit = defineEmits<{
  submit: [];
  update: [key: string, value: unknown];
}>();
const form = useTemplateRef<FormInstance>("form");
const rules: FormRules = Object.fromEntries(
  props.fields.map((f) => [
    f.key,
    [
      ...(f.required
        ? [
            {
              required: true,
              whitespace: true,
              message: `请填写${f.label}`,
              trigger: "blur",
            },
          ]
        : []),
      ...(f.type === "phone"
        ? [
            {
              pattern: /^1[3-9]\d{9}$/,
              message: "请输入有效手机号",
              trigger: "blur",
            },
          ]
        : []),
      ...(f.type === "email"
        ? [
            {
              type: "email" as const,
              message: "请输入有效邮箱",
              trigger: "blur",
            },
          ]
        : []),
      ...(f.type === "url"
        ? [
            {
              validator: (
                _rule: unknown,
                value: unknown,
                callback: (e?: Error) => void,
              ) => {
                if (value && !/^(https?:\/\/|\/[^/])/.test(String(value)))
                  callback(new Error("请输入 http(s) 或站内路径"));
                else callback();
              },
              trigger: "blur",
            },
          ]
        : []),
    ],
  ]),
);
async function submit() {
  if (await form.value?.validate().catch(() => false)) emit("submit");
}
</script>
<template>
  <el-form
    :disabled="busy"
    ref="form"
    :model="model"
    :rules="rules"
    label-position="top"
    @submit.prevent="submit"
  >
    <el-form-item
      v-for="field in fields"
      :key="field.key"
      :label="field.label"
      :prop="field.key"
    >
      <el-input-number
        v-if="field.type === 'number'"
        :model-value="Number(model[field.key] ?? 0)"
        :min="field.min"
        :max="field.max"
        @update:model-value="emit('update', field.key, $event)"
      />
      <el-input
        v-else
        :model-value="String(model[field.key] ?? '')"
        :type="
          field.type === 'textarea'
            ? 'textarea'
            : field.type === 'password'
              ? 'password'
              : 'text'
        "
        :rows="field.type === 'textarea' ? 5 : undefined"
        :maxlength="field.max ?? (field.type === 'textarea' ? 20000 : 500)"
        :show-password="field.type === 'password'"
        :autocomplete="field.type === 'password' ? 'new-password' : undefined"
        @update:model-value="emit('update', field.key, $event)"
      />
      <span v-if="field.hint" class="muted">{{
        field.hint
      }}</span> </el-form-item
    ><slot /><el-button native-type="submit" type="primary" :loading="busy">{{
      submitText ?? "保存"
    }}</el-button></el-form
  >
</template>
